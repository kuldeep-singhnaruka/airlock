import json
from typing import Any

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "estimate_tokens",
            "description": "Estimate tokens with a four-characters-per-token heuristic.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "model_card",
            "description": "Return context window and usage notes for a known open model.",
            "parameters": {
                "type": "object",
                "properties": {"model_name": {"type": "string"}},
                "required": ["model_name"],
                "additionalProperties": False,
            },
        },
    },
]

MODEL_CARDS: dict[str, dict[str, Any]] = {
    "llama3.2": {
        "context_window": 128000,
        "notes": "Small local default. Pull it with Ollama when you want real local inference.",
    },
    "llama-3.1-8b-instant": {
        "context_window": 128000,
        "notes": "Fast hosted open model on Groq's free tier. Confirm the live model name.",
    },
}


def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    if name == "estimate_tokens":
        text = str(arguments.get("text", ""))
        estimate = max(1, (len(text) + 3) // 4) if text else 0
        return json.dumps({"estimated_tokens": estimate, "method": "chars/4"})
    if name == "model_card":
        model_name = str(arguments.get("model_name", "unknown"))
        card = MODEL_CARDS.get(
            model_name,
            {
                "context_window": None,
                "notes": "Unknown model. Check the provider catalog before production use.",
            },
        )
        return json.dumps({"model_name": model_name, **card})
    return json.dumps({"error": f"Unknown tool: {name}"})


def tool_names() -> list[str]:
    return [spec["function"]["name"] for spec in TOOL_SPECS]
