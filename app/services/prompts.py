import json

CHAT_SYSTEM_PROMPT = """You are a concise enterprise assistant inside an inference gateway.
Answer the latest user message in plain text.
When a tool is available and the question needs a count or a model fact, call that tool.
Do not invent token counts or context-window sizes.
"""


def structured_system_prompt(schema_name: str, schema: dict) -> str:
    return (
        "Return only a JSON object. Do not use markdown.\n"
        f"SCHEMA_NAME={schema_name}\n"
        f"JSON_SCHEMA={json.dumps(schema, separators=(',', ':'))}"
    )
