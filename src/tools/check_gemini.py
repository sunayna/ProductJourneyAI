# save this as check_models.py and run it
from google import genai
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

for model in client.models.list():
    print(model.name)