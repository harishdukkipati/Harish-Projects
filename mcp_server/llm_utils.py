import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
print("API key:", openai.api_key)

def ask_llm(prompt):
    response = openai.chat.completions.create(
        model="gpt-4", 
        messages=[
            {"role": "system", "content": "You are an educational assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    answer = response.choices[0].message.content.strip()
    print("LLM answer:", answer)
    return answer
