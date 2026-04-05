"""
Structured knowledge extraction for the Vulcan OmniPro 220 manuals.

This module does more than create flat chunks:
- text sections become explanatory nodes
- table-like regions become constraint nodes
- procedures become step nodes
- images become diagram candidates
- lightweight relationships connect related nodes
"""

import base64
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import fitz  # PyMuPDF


PROCESS_KEYWORDS = ["mig", "tig", "stick", "flux", "flux-cored", "fcaw", "spool gun"]
TABLE_HINTS = [
    "duty cycle",
    "specification",
    "specifications",
    "chart",
    "settings",
    "parameter",
    "output",
    "input",
    "thickness",
    "wire speed",
]
PROCEDURE_HINTS = [
    "step",
    "install",
    "connect",
    "turn",
    "select",
    "press",
    "verify",
    "check",
]
DIAGRAM_HINTS = [
    "diagram",
    "wiring",
    "connection",
    "polarity",
    "torch",
    "ground",
    "work clamp",
    "electrode",
]


class KnowledgeExtractor:
    def __init__(self, files_dir: str = "../files"):
        self.files_dir = Path(files_dir)
        self.knowledge_base: Dict[str, Any] = {
            "text_chunks": [],
            "images": [],
            "tables": [],
            "procedures": [],
            "diagrams": [],
            "knowledge_nodes": [],
            "relationships": [],
        }

    def extract_from_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract structured knowledge from a PDF."""
        doc = fitz.open(pdf_path)
        extracted: Dict[str, Any] = {
            "text_chunks": [],
            "images": [],
            "tables": [],
            "procedures": [],
            "diagrams": [],
            "knowledge_nodes": [],
            "relationships": [],
            "metadata": {
                "filename": pdf_path.name,
                "pages": len(doc),
            },
        }

        for page_index in range(len(doc)):
            page = doc[page_index]
            page_num = page_index + 1
            page_text = page.get_text("text")
            page_images = self._extract_images_from_page(page, page_num, pdf_path.name)
            extracted["images"].extend(page_images)

            if not page_text.strip():
                continue

            sections = self._create_semantic_chunks(page_text, page_num, pdf_path.name)
            tables = self._extract_tables(page_text, page_num, pdf_path.name)
            procedures = self._extract_procedures(page_text, page_num, pdf_path.name)
            diagrams = self._extract_diagram_candidates(
                page_text=page_text,
                images=page_images,
                page=page_num,
                source=pdf_path.name,
            )

            extracted["text_chunks"].extend(sections)
            extracted["tables"].extend(tables)
            extracted["procedures"].extend(procedures)
            extracted["diagrams"].extend(diagrams)

            page_nodes = (
                self._create_nodes_from_sections(sections, "text")
                + self._create_nodes_from_sections(tables, "table")
                + self._create_nodes_from_sections(procedures, "procedure")
                + self._create_nodes_from_sections(diagrams, "diagram")
            )
            extracted["knowledge_nodes"].extend(page_nodes)
            extracted["relationships"].extend(self._relate_page_nodes(page_nodes))

        doc.close()
        return extracted

    def _create_semantic_chunks(self, text: str, page_num: int, source: str) -> List[Dict[str, Any]]:
        """Split text into explanatory sections while preserving headings."""
        chunks: List[Dict[str, Any]] = []
        lines = [line.strip() for line in text.split("\n")]
        current_lines: List[str] = []
        current_heading = ""

        for line in lines:
            if not line:
                continue

            if self._is_heading(line):
                if current_lines:
                    chunks.append(
                        self._create_section(
                            content="\n".join(current_lines),
                            heading=current_heading,
                            page=page_num,
                            source=source,
                            section_type="text",
                        )
                    )
                current_heading = line
                current_lines = [line]
                continue

            current_lines.append(line)
            if len("\n".join(current_lines)) >= 650:
                chunks.append(
                    self._create_section(
                        content="\n".join(current_lines),
                        heading=current_heading,
                        page=page_num,
                        source=source,
                        section_type="text",
                    )
                )
                current_lines = []

        if current_lines:
            chunks.append(
                self._create_section(
                    content="\n".join(current_lines),
                    heading=current_heading,
                    page=page_num,
                    source=source,
                    section_type="text",
                )
            )

        return chunks

    def _extract_tables(self, text: str, page_num: int, source: str) -> List[Dict[str, Any]]:
        """Heuristically detect table-like blocks and convert them into matrix nodes."""
        blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        tables: List[Dict[str, Any]] = []

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            joined = " ".join(lines).lower()
            numeric_lines = sum(bool(re.search(r"\d", line)) for line in lines)
            delimiter_lines = sum(
                1
                for line in lines
                if "\t" in line or re.search(r"\s{2,}", line) or len(re.findall(r"\d+", line)) >= 2
            )
            looks_tabular = (
                len(lines) >= 3
                and numeric_lines >= 2
                and delimiter_lines >= 2
                and any(hint in joined for hint in TABLE_HINTS)
            )
            if not looks_tabular:
                continue

            parsed_rows = [self._split_table_line(line) for line in lines if len(self._split_table_line(line)) >= 2]
            if len(parsed_rows) < 2:
                continue

            tables.append(
                {
                    "type": "table",
                    "title": lines[0][:120],
                    "heading": lines[0],
                    "page": page_num,
                    "source": source,
                    "text": block,
                    "data": {
                        "rows": parsed_rows[1:],
                        "columns": parsed_rows[0],
                    },
                    "tags": self._extract_tags(block),
                }
            )

        return tables

    def _extract_procedures(self, text: str, page_num: int, source: str) -> List[Dict[str, Any]]:
        """Extract step-by-step instructions into structured procedures."""
        blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        procedures: List[Dict[str, Any]] = []

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            step_lines = [
                line
                for line in lines
                if re.match(r"^(?:\d+[\).\s]|[-*]\s+)", line) or any(hint in line.lower() for hint in PROCEDURE_HINTS)
            ]
            if len(step_lines) < 3:
                continue

            steps = [re.sub(r"^(?:\d+[\).\s]+|[-*]\s+)", "", line).strip() for line in step_lines]
            procedures.append(
                {
                    "type": "procedure",
                    "title": lines[0][:120],
                    "heading": lines[0],
                    "page": page_num,
                    "source": source,
                    "text": block,
                    "steps": steps,
                    "tags": self._extract_tags(block),
                }
            )

        return procedures

    def _extract_diagram_candidates(
        self,
        page_text: str,
        images: List[Dict[str, Any]],
        page: int,
        source: str,
    ) -> List[Dict[str, Any]]:
        """Treat image-bearing pages with wiring/polarity language as diagram knowledge."""
        if not images:
            return []

        text_lower = page_text.lower()
        if not any(hint in text_lower for hint in DIAGRAM_HINTS):
            return []

        snippet = "\n".join(line.strip() for line in page_text.split("\n")[:12] if line.strip())
        return [
            {
                "type": "diagram",
                "title": "Diagram candidate",
                "heading": "Diagram candidate",
                "page": page,
                "source": source,
                "text": snippet,
                "image_refs": [image["index"] for image in images],
                "tags": self._extract_tags(page_text),
            }
        ]

    def _create_nodes_from_sections(self, sections: List[Dict[str, Any]], node_type: str) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        for index, section in enumerate(sections):
            node_id = f"{section['source']}:p{section['page']}:{node_type}:{index}"
            nodes.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "page": section["page"],
                    "source": section["source"],
                    "title": section.get("title") or section.get("heading") or node_type.title(),
                    "heading": section.get("heading", ""),
                    "content": section.get("text", ""),
                    "data": section.get("data"),
                    "steps": section.get("steps"),
                    "tags": section.get("tags", []),
                }
            )
        return nodes

    def _relate_page_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relationships: List[Dict[str, Any]] = []
        for left_index, left in enumerate(nodes):
            for right in nodes[left_index + 1:]:
                shared_tags = sorted(set(left.get("tags", [])) & set(right.get("tags", [])))
                if not shared_tags:
                    continue

                relation_type = "relates_to"
                if left["type"] == "table" and right["type"] in {"text", "procedure"}:
                    relation_type = "supports"
                elif left["type"] == "diagram" or right["type"] == "diagram":
                    relation_type = "visualizes"

                relationships.append(
                    {
                        "source": left["id"],
                        "target": right["id"],
                        "type": relation_type,
                        "shared_tags": shared_tags[:5],
                    }
                )
        return relationships

    def _create_section(
        self,
        content: str,
        heading: str,
        page: int,
        source: str,
        section_type: str,
    ) -> Dict[str, Any]:
        return {
            "type": section_type,
            "text": content,
            "heading": heading,
            "page": page,
            "source": source,
            "tags": self._extract_tags(f"{heading}\n{content}"),
        }

    def _extract_images_from_page(self, page: Any, page_num: int, source: str) -> List[Dict[str, Any]]:
        """Extract images from a PDF page."""
        images: List[Dict[str, Any]] = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                base_image = page.parent.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                rects = page.get_image_rects(xref)
                if not rects:
                    rects = [page.rect]

                for rect_index, bbox in enumerate(rects):
                    images.append(
                        {
                            "page": page_num,
                            "source": source,
                            "index": img_index,
                            "rect_index": rect_index,
                            "format": image_ext,
                            "data": image_b64,
                            "bbox": {
                                "x0": bbox.x0,
                                "y0": bbox.y0,
                                "x1": bbox.x1,
                                "y1": bbox.y1,
                            },
                        }
                    )
            except Exception as exc:
                print(f"Error extracting image {img_index} from page {page_num}: {exc}")
        return images

    def _extract_tags(self, text: str) -> List[str]:
        lowered = text.lower()
        tags = []
        for keyword in PROCESS_KEYWORDS + TABLE_HINTS + DIAGRAM_HINTS + ["porosity", "spatter", "aluminum", "steel"]:
            if keyword in lowered:
                tags.append(keyword)
        return sorted(set(tags))

    def _split_table_line(self, line: str) -> List[str]:
        if "\t" in line:
            parts = [part.strip() for part in line.split("\t") if part.strip()]
        else:
            parts = [part.strip() for part in re.split(r"\s{2,}", line) if part.strip()]
        if len(parts) < 2:
            compact = re.findall(r"[A-Za-z0-9.%+/()-]+", line)
            return compact if len(compact) >= 2 else []
        return parts

    def _is_heading(self, line: str) -> bool:
        return line.isupper() or (len(line) < 100 and line.endswith(":"))

    def _merge_results(self, extracted_items: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        for item in extracted_items:
            merged.extend(item.get(key, []))
        return merged

    def process_all_manuals(self) -> Dict[str, Any]:
        """Process every manual and save a reusable structured knowledge base."""
        pdf_files = list(self.files_dir.glob("*.pdf"))
        extracted_sets = []

        for pdf_file in pdf_files:
            print(f"Processing {pdf_file.name}...")
            extracted_sets.append(self.extract_from_pdf(pdf_file))

        knowledge_base = {
            "text_chunks": self._merge_results(extracted_sets, "text_chunks"),
            "images": self._merge_results(extracted_sets, "images"),
            "tables": self._merge_results(extracted_sets, "tables"),
            "procedures": self._merge_results(extracted_sets, "procedures"),
            "diagrams": self._merge_results(extracted_sets, "diagrams"),
            "knowledge_nodes": self._merge_results(extracted_sets, "knowledge_nodes"),
            "relationships": self._merge_results(extracted_sets, "relationships"),
        }

        self.knowledge_base = knowledge_base

        kb_lite = {
            **knowledge_base,
            "images": [{k: v for k, v in image.items() if k != "data"} for image in knowledge_base["images"]],
        }

        with open(Path("knowledge_base.json"), "w") as handle:
            json.dump(kb_lite, handle, indent=2)

        print(
            "Extracted "
            f"{len(knowledge_base['text_chunks'])} text chunks, "
            f"{len(knowledge_base['tables'])} tables, "
            f"{len(knowledge_base['procedures'])} procedures, "
            f"{len(knowledge_base['diagrams'])} diagrams, "
            f"{len(knowledge_base['relationships'])} relationships"
        )
        return self.knowledge_base

    def get_knowledge_base(self) -> Dict[str, Any]:
        return self.knowledge_base


if __name__ == "__main__":
    extractor = KnowledgeExtractor()
    kb = extractor.process_all_manuals()
    print("Knowledge base created:")
    print(f"  - {len(kb['knowledge_nodes'])} nodes")
    print(f"  - {len(kb['relationships'])} relationships")
