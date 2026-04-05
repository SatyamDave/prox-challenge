"""
Vector-backed retrieval over structured manual knowledge.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
            )
        )
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        try:
            self.client.delete_collection("manual_knowledge")
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name="manual_knowledge",
            metadata={"description": "Structured nodes from Vulcan OmniPro 220 manuals"},
        )

    def add_knowledge_nodes(self, nodes: List[Dict[str, Any]]):
        if not nodes:
            return

        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for index, node in enumerate(nodes):
            ids.append(node.get("id", f"node_{index}"))
            documents.append(self._node_to_document(node))
            metadatas.append(
                {
                    "node_id": node.get("id", f"node_{index}"),
                    "node_type": node.get("type", "text"),
                    "page": str(node.get("page", "")),
                    "source": node.get("source", ""),
                    "title": node.get("title", ""),
                    "heading": node.get("heading", ""),
                    "tags": ", ".join(node.get("tags", [])),
                }
            )

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"Added {len(nodes)} knowledge nodes to vector store")

    def search(self, query: str, n_results: int = 5, node_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        results = self.collection.query(query_texts=[query], n_results=n_results)

        formatted_results: List[Dict[str, Any]] = []
        if not results.get("documents"):
            return formatted_results

        for index, document in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][index] if results.get("metadatas") else {}
            if node_types and metadata.get("node_type") not in node_types:
                continue

            formatted_results.append(
                {
                    "text": document,
                    "metadata": metadata,
                    "distance": results["distances"][0][index] if results.get("distances") else 0,
                }
            )

        return formatted_results

    def get_collection_count(self) -> int:
        return self.collection.count()

    def _node_to_document(self, node: Dict[str, Any]) -> str:
        parts = [
            f"Type: {node.get('type', 'text')}",
            f"Title: {node.get('title', '')}",
            f"Heading: {node.get('heading', '')}",
            f"Tags: {', '.join(node.get('tags', []))}",
            f"Content: {node.get('content', '')}",
        ]

        if node.get("data"):
            parts.append(f"Structured data: {node['data']}")
        if node.get("steps"):
            parts.append("Steps: " + " | ".join(node["steps"]))

        return "\n".join(part for part in parts if part.strip())


def build_vector_store_from_knowledge_base(knowledge_base: Dict[str, Any]) -> VectorStore:
    store = VectorStore()
    nodes = knowledge_base.get("knowledge_nodes")
    if nodes:
        store.add_knowledge_nodes(nodes)
    elif knowledge_base.get("text_chunks"):
        fallback_nodes = []
        for index, chunk in enumerate(knowledge_base["text_chunks"]):
            fallback_nodes.append(
                {
                    "id": f"legacy_text_{index}",
                    "type": "text",
                    "page": chunk.get("page"),
                    "source": chunk.get("source"),
                    "title": chunk.get("heading") or "Manual text",
                    "heading": chunk.get("heading", ""),
                    "content": chunk.get("text", ""),
                    "tags": chunk.get("tags", []),
                }
            )
        store.add_knowledge_nodes(fallback_nodes)
    return store


if __name__ == "__main__":
    import json

    kb_file = Path("knowledge_base.json")
    if kb_file.exists():
        with open(kb_file, "r") as handle:
            kb = json.load(handle)

        store = build_vector_store_from_knowledge_base(kb)
        print(f"Vector store built with {store.get_collection_count()} nodes")
        results = store.search("duty cycle for MIG welding at 200A", n_results=3)
        for result in results:
            print(f"- {result['metadata'].get('node_type')} p.{result['metadata'].get('page')}: {result['text'][:100]}...")
    else:
        print("No knowledge base found. Run knowledge_extractor.py first.")
