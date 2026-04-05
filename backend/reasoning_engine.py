"""
Reasoning engine for multi-hop search and knowledge synthesis.
This is the brain that chains searches, infers from context, and never says "I don't know".
"""

from typing import List, Dict, Any, Optional, Tuple
from vector_store import VectorStore
from domain_knowledge import WeldingDomainKnowledge
from query_planner import QueryPlanner
import json


class ReasoningEngine:
    """
    Orchestrates multi-hop reasoning:
    1. Decomposes queries
    2. Executes search plan
    3. Synthesizes results with domain knowledge
    4. Estimates confidence
    5. NEVER returns "not found" - always provides best answer
    """

    def __init__(self, vector_store: VectorStore, knowledge_base: Dict[str, Any]):
        self.vector_store = vector_store
        self.knowledge_base = knowledge_base
        self.domain_knowledge = WeldingDomainKnowledge()
        self.query_planner = QueryPlanner()

    def reason(self, query: str) -> Dict[str, Any]:
        """
        Main reasoning loop.
        Takes a query and returns the best possible answer with confidence level.
        """
        # Step 1: Analyze query intent
        query_analysis = self.query_planner.analyze_query_intent(query)

        # Step 2: Create search plan
        search_plan = self.query_planner.create_search_plan(query_analysis)

        # Step 3: Execute search plan
        search_results = self._execute_search_plan(search_plan)

        # Step 4: Apply domain knowledge to fill gaps
        domain_inferences = self._apply_domain_knowledge(query_analysis, search_results)

        # Step 5: Synthesize final answer
        synthesis = self._synthesize_answer(
            query=query,
            query_analysis=query_analysis,
            search_results=search_results,
            domain_inferences=domain_inferences
        )

        # Step 6: Estimate confidence
        confidence = self._estimate_confidence(search_results, domain_inferences, synthesis)

        return {
            "answer": synthesis["answer"],
            "confidence": confidence,
            "reasoning_chain": synthesis["reasoning_chain"],
            "sources": synthesis["sources"],
            "inferences": domain_inferences,
            "intent": query_analysis["primary_intent"],
            "search_stats": {
                "total_searches": len([s for s in search_plan if s["action"] == "search"]),
                "results_found": sum(len(r) for r in search_results.values())
            }
        }

    def _execute_search_plan(self, search_plan: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """
        Execute each step in the search plan.
        Returns all search results organized by step.
        """
        results = {}

        for step in search_plan:
            if step["action"] == "search":
                step_results = self.vector_store.search(
                    query=step["query"],
                    n_results=step.get("n_results", 5)
                )
                results[f"step_{step['step']}"] = step_results

        return results

    def _apply_domain_knowledge(self, query_analysis: Dict[str, Any], search_results: Dict[str, List]) -> Dict[str, Any]:
        """
        Use domain knowledge to infer missing information.
        This is where we go from "not found" to "here's what I know".
        """
        context = query_analysis["context"]
        intent = query_analysis["primary_intent"]
        inferences = {}

        # Cross-reference known specs
        if any(context.values()):
            inferences["cross_reference"] = self.domain_knowledge.cross_reference_specs(context)

        # Intent-specific inferences
        if intent == "duty_cycle" and context.get("amperage") and context.get("voltage"):
            inferences["duty_cycle"] = self.domain_knowledge.infer_duty_cycle(
                amperage=context["amperage"],
                voltage=context["voltage"]
            )

        elif intent == "wire_speed" and context.get("amperage"):
            wire_diameter = context.get("wire_diameter", "0.035")
            inferences["wire_speed"] = self.domain_knowledge.infer_wire_speed(
                amperage=context["amperage"],
                wire_diameter=wire_diameter
            )

        elif intent == "amperage" and context.get("material") and context.get("thickness"):
            inferences["amperage"] = self.domain_knowledge.infer_amperage_from_material(
                material=context["material"],
                thickness=context["thickness"]
            )

        elif intent == "polarity" and context.get("process"):
            inferences["polarity"] = self.domain_knowledge.infer_polarity(
                process=context["process"],
                material=context.get("material", "steel")
            )

        elif intent == "troubleshooting":
            # Extract defect description from query
            inferences["troubleshooting"] = self.domain_knowledge.diagnose_weld_defect(
                query_analysis["original_query"]
            )

        return inferences

    def _synthesize_answer(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        search_results: Dict[str, List],
        domain_inferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize final answer from all sources.
        Prioritize: exact matches > related info > domain knowledge inferences
        """
        answer_parts = []
        reasoning_chain = []
        sources = []

        # Collect all search results
        all_results = []
        for step_name, results in search_results.items():
            all_results.extend(results)

        # Sort by relevance (distance)
        all_results.sort(key=lambda x: x.get("distance", 1.0))

        # Strategy 1: Check if we have direct answers from manual
        if all_results:
            high_confidence_results = [r for r in all_results if r.get("distance", 1.0) < 0.5]

            if high_confidence_results:
                # We found relevant info in manual
                for result in high_confidence_results[:3]:
                    answer_parts.append(result["text"])
                    sources.append({
                        "type": "manual",
                        "page": result["metadata"].get("page"),
                        "source": result["metadata"].get("source"),
                        "confidence": 1.0 - result.get("distance", 0)
                    })
                    reasoning_chain.append(f"Found in manual (page {result['metadata'].get('page')})")

        # Strategy 2: Use domain knowledge inferences
        if domain_inferences:
            for inference_type, inference_data in domain_inferences.items():
                if inference_type == "cross_reference":
                    # Multiple inferences
                    for key, value in inference_data.items():
                        if isinstance(value, dict) and "reasoning" in value:
                            answer_parts.append(value["reasoning"])
                            reasoning_chain.append(f"Inferred {key} from domain knowledge")
                            sources.append({
                                "type": "domain_knowledge",
                                "inference": key,
                                "confidence": value.get("confidence", 0.7)
                            })
                elif isinstance(inference_data, dict) and "reasoning" in inference_data:
                    answer_parts.append(inference_data["reasoning"])
                    reasoning_chain.append(f"Applied domain knowledge: {inference_type}")
                    sources.append({
                        "type": "domain_knowledge",
                        "inference": inference_type,
                        "confidence": inference_data.get("confidence", 0.7)
                    })
                elif isinstance(inference_data, list):
                    # Troubleshooting causes
                    for item in inference_data:
                        if "likely_causes" in item:
                            causes_text = "Likely causes: " + ", ".join(item["likely_causes"])
                            answer_parts.append(causes_text)
                            reasoning_chain.append("Applied troubleshooting heuristics")

        # Strategy 3: Use lower-confidence manual results if we still don't have much
        if len(answer_parts) < 2 and all_results:
            medium_confidence_results = [r for r in all_results if 0.5 <= r.get("distance", 1.0) < 0.8]

            for result in medium_confidence_results[:2]:
                answer_parts.append(result["text"])
                sources.append({
                    "type": "manual_related",
                    "page": result["metadata"].get("page"),
                    "confidence": 0.6
                })
                reasoning_chain.append(f"Related info from manual (page {result['metadata'].get('page')})")

        # Strategy 4: If still nothing, use pure domain knowledge
        if not answer_parts:
            fallback = self._generate_fallback_answer(query_analysis)
            answer_parts.append(fallback["text"])
            reasoning_chain.append("Generated answer from domain knowledge")
            sources.append({
                "type": "domain_knowledge_fallback",
                "confidence": 0.5
            })

        # Combine answer parts
        final_answer = self._format_answer_for_technician(
            answer_parts=answer_parts,
            intent=query_analysis["primary_intent"],
            context=query_analysis["context"]
        )

        return {
            "answer": final_answer,
            "reasoning_chain": reasoning_chain,
            "sources": sources
        }

    def _generate_fallback_answer(self, query_analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a reasonable fallback answer when we have no direct info.
        This ensures we NEVER say "I don't know".
        """
        intent = query_analysis["primary_intent"]
        context = query_analysis["context"]

        if intent == "duty_cycle":
            voltage = context.get("voltage", "240V")
            text = f"For the OmniPro 220 on {voltage}, duty cycle varies by amperage. "
            text += "At lower amperages (100-150A), expect 50-60% duty cycle. "
            text += "At higher amperages (200-250A), expect 30-40% duty cycle. "
            text += "Check the manual's duty cycle chart for exact values."

        elif intent == "wire_speed":
            text = "Wire speed depends on amperage and wire diameter. "
            text += "As a rule of thumb, higher amperage = faster wire speed. "
            text += "For .035\" wire, typical range is 100-500 IPM. "
            text += "Start at mid-range and adjust based on puddle behavior."

        elif intent == "polarity":
            process = context.get("process", "MIG")
            text = f"For {process} welding: "
            if "MIG" in process.upper():
                text += "Use DCEP (DC Electrode Positive) for steel and aluminum. "
            elif "FLUX" in process.upper():
                text += "Use DCEN (DC Electrode Negative) for flux-core wire. "
            elif "TIG" in process.upper():
                text += "Use DCEN for steel, AC for aluminum. "
            text += "Check your machine's polarity diagram for connection details."

        elif intent == "troubleshooting":
            text = "Common weld issues: Check your ground connection first. "
            text += "Make sure material is clean. Verify gas flow (15-25 CFH). "
            text += "Check wire speed and voltage settings. "
            text += "Consult the troubleshooting section in the manual."

        elif intent == "setup":
            text = "Basic setup: 1) Connect ground clamp to workpiece. "
            text += "2) Install wire spool and feed through gun. "
            text += "3) Connect gas if using MIG. "
            text += "4) Set polarity for your process. "
            text += "5) Set voltage and wire speed for your material thickness."

        else:
            text = "The OmniPro 220 is a multiprocess welder supporting MIG, TIG, and Stick. "
            text += "Check the manual for specific settings and procedures. "
            text += "For best results, match your settings to material type and thickness."

        return {"text": text}

    def _format_answer_for_technician(
        self,
        answer_parts: List[str],
        intent: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Format the answer to sound like a senior technician explaining in a garage.
        Casual but knowledgeable. No "I don't know" - always helpful.
        """
        # Start with context if we have it
        intro = ""
        if context.get("material") and context.get("thickness"):
            intro = f"Alright, for {context['thickness']} {context['material']}: "
        elif context.get("process"):
            intro = f"For {context['process']} welding: "

        # Combine answer parts naturally
        if len(answer_parts) == 1:
            main_answer = answer_parts[0]
        elif len(answer_parts) == 2:
            main_answer = answer_parts[0] + " " + answer_parts[1]
        else:
            # More than 2 parts - structure it
            main_answer = answer_parts[0]
            for part in answer_parts[1:3]:  # Max 3 parts
                main_answer += "\n\n" + part

        # Add practical advice based on intent
        advice = ""
        if intent == "duty_cycle":
            advice = "\n\nPractical tip: If you're pushing the duty cycle limit, give it a breather every few minutes. Keeps the machine happy longer."
        elif intent == "wire_speed":
            advice = "\n\nPro tip: Start conservative and adjust up. Listen to the weld - should sound like bacon frying, not popping."
        elif intent == "troubleshooting":
            advice = "\n\nRemember: 90% of weld problems are either dirty metal, bad ground, or wrong settings. Start with the basics."

        return intro + main_answer + advice

    def _estimate_confidence(
        self,
        search_results: Dict[str, List],
        domain_inferences: Dict[str, Any],
        synthesis: Dict[str, Any]
    ) -> float:
        """
        Estimate overall confidence in the answer.
        High confidence = found in manual
        Medium confidence = inferred from domain knowledge
        Low confidence = fallback answer
        """
        sources = synthesis.get("sources", [])

        if not sources:
            return 0.3  # Minimal confidence

        # Calculate weighted confidence
        total_confidence = 0.0
        weights = {
            "manual": 1.0,
            "manual_related": 0.7,
            "domain_knowledge": 0.75,
            "domain_knowledge_fallback": 0.5
        }

        for source in sources:
            source_type = source.get("type", "")
            source_confidence = source.get("confidence", 0.5)
            weight = weights.get(source_type, 0.5)
            total_confidence += source_confidence * weight

        # Average and normalize
        final_confidence = min(total_confidence / len(sources), 1.0)

        # Boost if we have manual sources
        has_manual = any(s.get("type") == "manual" for s in sources)
        if has_manual:
            final_confidence = min(final_confidence + 0.15, 1.0)

        return round(final_confidence, 2)

    def multi_hop_search(self, initial_query: str, max_hops: int = 3) -> Dict[str, Any]:
        """
        Perform iterative multi-hop search, refining queries based on previous results.
        """
        all_results = []
        current_query = initial_query

        for hop in range(max_hops):
            # Search
            results = self.vector_store.search(current_query, n_results=5)
            all_results.extend(results)

            # If we got good results, stop
            if results and results[0].get("distance", 1.0) < 0.4:
                break

            # Otherwise, refine the query
            refined_query = self.query_planner.refine_search_queries(
                original_query=current_query,
                search_results=results,
                iteration=hop
            )

            if not refined_query:
                break

            current_query = refined_query

        return {
            "results": all_results,
            "hops": hop + 1,
            "final_query": current_query
        }
