import os, openai

ai_coice = "azure"

# azure 
if ai_coice == "azure":
    #TODO: need a api for users to be able to set their own api key
    openai.api_type = "azure"
    openai.api_base = ""
    openai.api_version = "2023-05-15"
    openai.api_key = ""
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


