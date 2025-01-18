import os
from openai import OpenAI

with open(".env") as env:
    for line in env:
        key, value = line.strip().split("=")
        os.environ[key] = value

client = OpenAI(
    api_key=os.environ['API_KEY']
)