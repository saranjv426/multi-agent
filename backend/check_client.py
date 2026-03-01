
from openai import OpenAI
import sys

try:
    client = OpenAI(api_key="sk-test")
    print("Client attributes:", dir(client))
    if hasattr(client, 'responses'):
        print("client.responses exists!")
    else:
        print("client.responses DOES NOT exist.")
except Exception as e:
    print(f"Error: {e}")
