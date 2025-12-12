import os
from openai import AsyncOpenAI
import json

async def ask_llm(prompt: str, history: list = None, system_prompt: str = None) -> str:
    """
    Interacts with the LLM provider.
    """
    provider = os.getenv("LLM_PROVIDER", "openai")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    # model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # Simple OpenRouter/OpenAI compatible client
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1" if provider == "openrouter" else None
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": prompt})

    import asyncio

    for attempt in range(5):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            print(f"LLM Error (Attempt {attempt+1}/5): {error_msg}")
            
            # Check for Rate Limit (429)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                wait_time = 20 * (attempt + 1) # simple linear backoff starting at 20s
                print(f"Rate limit hit. Waiting {wait_time}s before retrying...")
                await asyncio.sleep(wait_time)
            else:
                # If it's not a rate limit, maybe we shouldn't retry or just wait a short bit
                # For now, let's just return empty if it's a fatal error, but maybe retry on connection issues?
                # Let's simple retry for everything for now with short delay
                await asyncio.sleep(2)
    
    return ""
