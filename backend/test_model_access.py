
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# Test all relevant GPT models including new ones
models_to_test = [
    "gpt-4o",           # GPT-4 Omni (vision capable)
    "gpt-4o-mini",      # GPT-4 Omni Mini (cheaper, faster)
    "gpt-5",            # GPT-5 (if available)
    "gpt-5-mini",       # GPT-5 Mini (if available)
    "gpt-5.1",          # GPT-5.1 (if available)
    "o1-preview",       # O1 reasoning model
    "o1-mini",          # O1 mini reasoning model
]

print(f"Testing access with API Key: {api_key[:8]}...")
print("\n" + "="*60)

accessible_models = []

for model in models_to_test:
    print(f"\nTesting model: {model}")
    try:
        # Use appropriate parameter based on model
        if model.startswith("gpt-5") or model.startswith("o1"):
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_completion_tokens=10
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
        print(f"✅ SUCCESS: {model} is accessible")
        print(f"   Response: {response.choices[0].message.content}")
        accessible_models.append(model)
    except Exception as e:
        error_str = str(e)
        if "does not exist" in error_str or "model_not_found" in error_str:
            print(f"❌ FAILED: {model} - Model does not exist")
        elif "Unsupported parameter" in error_str:
            print(f"⚠️  PARAMETER ERROR: {model} - {error_str[:100]}")
        else:
            print(f"❌ FAILED: {model} - {error_str[:150]}")

print("\n" + "="*60)
print(f"\n✅ ACCESSIBLE MODELS ({len(accessible_models)}):")
for model in accessible_models:
    print(f"   - {model}")
    
print("\n" + "="*60)
print("\nRECOMMENDATION for Vision + Text tasks:")
if "gpt-5.1" in accessible_models:
    print("   Use: gpt-5.1 (best performance)")
elif "gpt-5" in accessible_models:
    print("   Use: gpt-5 (excellent performance)")
elif "gpt-4o" in accessible_models:
    print("   Use: gpt-4o (proven, reliable)")
