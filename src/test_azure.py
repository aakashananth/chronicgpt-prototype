import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()  # loads .env

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

print("Sending request...")

response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Hello! Please confirm the Azure setup is working.",
        },
    ],
)

print("\nResponse:")
print(response.choices[0].message.content)
