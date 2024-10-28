import os
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key-here")
models = client.models.list()
for model in models:
    print(f"Model: {model.id}")

