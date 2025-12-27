"""Debug script to check raw API responses"""

import asyncio
import os
import json
import httpx


async def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return

    print("=== Raw Credits API Response ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openrouter.ai/api/v1/credits",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
