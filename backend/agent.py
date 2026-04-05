"""
Multimodal agent for Vulcan OmniPro 220 using Claude.
"""

import anthropic
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
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.vector_store = vector_store
        self.knowledge_base = knowledge_base
        self.conversation_history = []

        # Define tools for the agent
        self.tools = [
            {
                "name": "search_manual",
                "description": "Search the Vulcan OmniPro 220 technical manuals for specific information. Use this to find duty cycles, specifications, troubleshooting steps, setup procedures, and technical details.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant information in the manuals"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_images_for_topic",
                "description": "Retrieve relevant images, diagrams, or schematics from the manual for a specific topic (e.g., 'wiring diagram', 'front panel', 'polarity setup', 'weld defects').",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic to find images for (e.g., 'polarity setup', 'wire feed mechanism', 'front panel controls')"
                        },
                        "page_number": {
                            "type": "integer",
                            "description": "Optional: specific page number if known"
                        }
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "create_artifact",
                "description": "Create an interactive artifact (diagram, calculator, table, flowchart) when information is too complex to explain in text alone. Use this for duty cycle calculators, polarity diagrams, troubleshooting flowcharts, and settings configurators.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "artifact_type": {
                            "type": "string",
                            "enum": ["diagram", "calculator", "table", "flowchart", "configurator"],
                            "description": "Type of artifact to create"
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the artifact"
                        },
                        "data": {
                            "type": "object",
                            "description": "Data needed to render the artifact"
                        }
                    },
                    "required": ["artifact_type", "title", "data"]
                }
            }
        ]

    def _search_manual(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Tool implementation: search the manual."""
        return self.vector_store.search(query, n_results)

    def _get_images_for_topic(self, topic: str, page_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """Tool implementation: get relevant images."""
        # Simple keyword matching for now (could be enhanced with embeddings)
        relevant_images = []

        for img in self.knowledge_base.get("images", []):
            # Search for images on specific page or with relevant context
            if page_number and img["page"] == page_number:
                relevant_images.append(img)
            # Could add more sophisticated image matching here

        return relevant_images[:5]

    def _create_artifact(self, artifact_type: str, title: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation: create an artifact specification."""
        return {
            "type": artifact_type,
            "title": title,
            "data": data
        }

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a tool and return results."""
        if tool_name == "search_manual":
            return self._search_manual(
                query=tool_input["query"],
                n_results=tool_input.get("n_results", 5)
            )
        elif tool_name == "get_images_for_topic":
            return self._get_images_for_topic(
                topic=tool_input["topic"],
                page_number=tool_input.get("page_number")
            )
        elif tool_name == "create_artifact":
            return self._create_artifact(
                artifact_type=tool_input["artifact_type"],
                title=tool_input["title"],
                data=tool_input["data"]
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def chat(self, user_message: str, image_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        Supports text and image inputs.
        """
        # Build message content
        message_content = []

        if image_data:
            # User uploaded an image (e.g., photo of a weld defect)
            message_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data
                }
            })

        message_content.append({
            "type": "text",
            "text": user_message
        })

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message_content
        })

        # System prompt
        system_prompt = """You are an expert technical support agent for the Vulcan OmniPro 220 multiprocess welding system.

You help users who just bought this welder and are setting it up in their garage. They're not idiots, but they're not professional welders either. Be helpful, clear, and patient.

Key guidelines:
1. **Use tools proactively**: Always search the manual for technical details before answering. Don't guess specifications.

2. **Be multimodal**: When explaining something visual (wiring diagrams, polarity setup, front panel controls), create an artifact to show it, don't just describe it in text.

3. **Create artifacts for**:
   - Duty cycle calculators (when user asks about duty cycles)
   - Polarity diagrams (when explaining cable connections)
   - Troubleshooting flowcharts (when diagnosing problems)
   - Settings configurators (when user needs to set up for specific material/thickness)
   - Visual representations of tables and matrices

4. **Tone**: Friendly, clear, and concise. Imagine you're a helpful technician explaining to a homeowner.

5. **Accuracy**: Always cite page numbers from the manual when providing technical info. If you're not sure, say so and search for it.

When a user asks about duty cycles, polarity, troubleshooting, or specifications - use the search_manual tool first, then create an artifact if it helps visualize the answer."""

        # Call Claude with tools
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_prompt,
            messages=self.conversation_history,
            tools=self.tools
        )

        # Process response and handle tool calls
        artifacts = []
        text_response = ""
        images = []

        while response.stop_reason == "tool_use":
            # Extract text and tool uses from response
            for block in response.content:
                if block.type == "text":
                    text_response += block.text
                elif block.type == "tool_use":
                    # Execute the tool
                    tool_result = self._execute_tool(block.name, block.input)

                    # Handle artifact creation
                    if block.name == "create_artifact":
                        artifacts.append(tool_result)

                    # Handle image retrieval
                    if block.name == "get_images_for_topic":
                        images.extend(tool_result)

                    # Add assistant response to history
                    if not any(msg.get("role") == "assistant" for msg in self.conversation_history[-1:]):
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": response.content
                        })

                    # Add tool result to history
                    self.conversation_history.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(tool_result)
                        }]
                    })

            # Continue the conversation
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                messages=self.conversation_history,
                tools=self.tools
            )

        # Extract final text response
        for block in response.content:
            if block.type == "text":
                text_response += block.text

        # Add final assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        return {
            "text": text_response,
            "artifacts": artifacts,
            "images": images,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
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
    if response['artifacts']:
        print(f"\nArtifacts created: {len(response['artifacts'])}")
