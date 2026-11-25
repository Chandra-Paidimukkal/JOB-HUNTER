"""Quick Groq API key + model verification."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
print(f"Key set: {'YES' if settings.GROQ_API_KEY and settings.GROQ_API_KEY != 'your_groq_api_key_here' else 'NO'}")
print(f"Model:   {settings.GROQ_MODEL}")

try:
    from groq import Groq
    client = Groq(api_key=settings.GROQ_API_KEY)
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": "Reply with exactly: GROQ_WORKS"}],
        max_tokens=20,
    )
    reply = response.choices[0].message.content.strip()
    print(f"Test reply: {reply}")
    print(f"Model used: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}")
    print("\nGROQ API: WORKING CORRECTLY")
except Exception as e:
    print(f"\nGROQ API ERROR: {e}")
    # Try fallback model
    print("\nTrying fallback model: openai/gpt-oss-20b ...")
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": "Reply: GROQ_WORKS"}],
            max_tokens=10,
        )
        print(f"Fallback worked: {response.choices[0].message.content}")
        print("Recommend setting GROQ_MODEL=openai/gpt-oss-20b in .env")
    except Exception as e2:
        print(f"Fallback also failed: {e2}")
