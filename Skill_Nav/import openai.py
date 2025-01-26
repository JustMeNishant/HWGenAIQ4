from openai import AzureOpenAI
from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION") 
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

# Initialize the client
client = AzureOpenAI()

# Custom message
custom_message = 'Hi My Name is Nishant, This is My first API call or testing, How are things looking on your end'

# Create the request
res = client.chat.completions.create(
    model="gpt-4o",  # Use the correct model, e.g., gpt-4o or gpt-4o-mini
    messages=[{"role": "system", "content": "You are a helpful assistant."},
              {"role": "user", "content": custom_message}],
    temperature=0.7,
    max_tokens=256,
    top_p=0.6,
    frequency_penalty=0.7
)
# Access the response correctly
response = res.choices[0].message.content  # Access content directly
print(response)
