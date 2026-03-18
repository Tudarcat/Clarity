from agent.provider.custom_provider import CustomProvider
import os

env_api_key = os.environ.get("ARK_API_KEY")

if not env_api_key:
    print("Error: ARK_API_KEY environment variable is not set.")
    print("Please set the ARK_API_KEY environment variable and try again.")
    print("For example: $env:ARK_API_KEY = 'your_api_key'")
    exit(1)

custom_prov = CustomProvider(api_key=env_api_key, api_url="https://ark.cn-beijing.volces.com/api/v3")

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
]

res = custom_prov.chat(messages=messages, tool_list=[])
print("Test completed successfully!")
print("Response:", res)