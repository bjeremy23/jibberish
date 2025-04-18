import os, openai

ai_coice = "azure"

# azure 
if ai_coice == "azure":
    openai.api_type = "azure"
    openai.api_base = "https://bjere-m9n0vzju-eastus2.cognitiveservices.azure.com/"
    openai.api_version = "2023-05-15"
    openai.api_key = "1TZWQHLuMCT9M2zscBuTrpZGnw1zfrctI5dqSiGunZhNm3JPYn4BJQQJ99BDACHYHv6XJ3w3AAAAACOGO3I8"
    model = "gpt-4.1"  # <-- Replace with your actual deployment name
else:
    # openai
    with open(".env") as env:
        for line in env:
            key, value = line.strip().split("=")
            os.environ[key] = value

    client = openai.OpenAI(
        api_key=os.environ['API_KEY']
    )
    model = "gpt-4"


