"""Debug script to check API responses"""

import asyncio
import os
import json

from llminfo_cli.providers.openrouter import OpenRouterProvider


async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return

    provider = OpenRouterProvider(api_key=api_key)

    print("=== Credits API Response ===")
    credits = await provider.get_credits()
    print(json.dumps(credits.model_dump(), indent=2))

    print("\n=== Models Count ===")
    models = await provider.get_models()
    print(f"Total models: {len(models)}")
    free_models = [m for m in models if m.is_free]
    print(f"Free models (by :free suffix): {len(free_models)}")

    # Check pricing of free models
    print("\n=== First 5 Free Models with Pricing ===")
    for i, m in enumerate(free_models[:5]):
        pricing = m.pricing if m.pricing else "N/A"
        print(f"{i + 1}. {m.id}")
        print(f"   Name: {m.name}")
        print(f"   Context: {m.context_length}")
        print(f"   Pricing: {pricing}")


if __name__ == "__main__":
    asyncio.run(main())
