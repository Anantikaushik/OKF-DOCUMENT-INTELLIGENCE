import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing.")

client = Groq(api_key=api_key)

print("=" * 60)
print("GROQ AVAILABLE MODELS")
print("=" * 60)

models = client.models.list()

for model in models.data:
    print(model.id)

print("=" * 60)
print(f"Total models available: {len(models.data)}")
print("=" * 60)