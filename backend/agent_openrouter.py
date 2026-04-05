"""
Multimodal agent for Vulcan OmniPro 220 using OpenRouter.
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
import os
from dotenv import load_dotenv
from vector_store import VectorStore
from knowledge_extractor import KnowledgeExtractor
from pathlib import Path

load_dotenv()


class VulcanAgent:
    def __init__(self, vector_store: VectorStore, knowledge_base: Dict[str, Any]):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.vector_store = vector_store
        self.knowledge_base = knowledge_base
        self.conversation_history = []
        self.model = "xiaomi/mimo-v2-pro"

    def _search_manual(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search the manual for relevant information."""
        return self.vector_store.search(query, n_results)

    def chat(self, user_message: str, image_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        """
        # Search the manual for relevant information
        search_results = self._search_manual(user_message, n_results=5)

        # Build context from search results
        context = "\n\n".join([
            f"[From {r['metadata'].get('source', 'manual')}, page {r['metadata'].get('page', 'unknown')}]\n{r['text']}"
            for r in search_results
        ])

        # Build the prompt
        system_prompt = f"""You are an expert technical support agent for the Vulcan OmniPro 220 multiprocess welding system.

You help users who just bought this welder and are setting it up in their garage. They're not idiots, but they're not professional welders either. Be helpful, clear, and patient.

Key guidelines:
1. Use the manual context provided to answer questions accurately
2. Always cite page numbers when providing technical specifications
3. Be concise and clear - avoid jargon when possible
4. If you're not sure, say so

MANUAL CONTEXT:
{context}

Answer the user's question based on the manual context above."""

        # Add to conversation history
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Call OpenRouter
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )

        text_response = response.choices[0].message.content

        return {
            "text": text_response,
            "artifacts": [],
            "images": [],
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        }

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []


if __name__ == "__main__":
    # Test the agent
    from vector_store import build_vector_store_from_knowledge_base

    # Load knowledge base
    kb_file = Path("knowledge_base.json")
    if not kb_file.exists():
        print("Building knowledge base...")
        extractor = KnowledgeExtractor()
        kb = extractor.process_all_manuals()
    else:
        with open(kb_file, 'r') as f:
            kb = json.load(f)

    # Build vector store
    store = build_vector_store_from_knowledge_base(kb)

    # Create agent
    agent = VulcanAgent(store, kb)

    # Test query
    print("Testing agent with: 'What's the duty cycle for MIG welding at 200A on 240V?'")
    response = agent.chat("What's the duty cycle for MIG welding at 200A on 240V?")

    print(f"\nResponse:\n{response['text']}")
