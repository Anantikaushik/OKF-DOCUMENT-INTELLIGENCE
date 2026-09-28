from __future__ import annotations

import json

from app.llm.groq_client import GroqClient


SYSTEM_PROMPT = """
You are a knowledge graph extraction system.

Extract entities and relationships ONLY from the supplied text.

Return a JSON object with exactly these two keys:

{
  "entities": [
    {
      "name": "entity name",
      "type": "entity type",
      "description": "short description"
    }
  ],
  "relationships": [
    {
      "source": "source entity",
      "relationship": "relationship type",
      "target": "target entity"
    }
  ]
}

Rules:

1. Use only information explicitly supported by the text.
2. Do not invent entities.
3. Do not invent relationships.
4. Keep entity names concise.
5. Keep descriptions short.
6. Return valid JSON only.
"""


class EntityExtractor:

    def __init__(self):
        self.groq = GroqClient()

    def extract(self, text: str) -> dict:

        response = self.groq.chat(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=text,
            json_mode=True,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Groq returned an empty response."
            )

        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Groq returned invalid JSON."
            ) from exc

        if "entities" not in result:
            result["entities"] = []

        if "relationships" not in result:
            result["relationships"] = []

        return result