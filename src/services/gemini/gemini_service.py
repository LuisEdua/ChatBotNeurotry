import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))

model = genai.GenerativeModel('gemini-1.5-flash')

"""
while True:
    user_input = input()
    if user_input == "exit":
        break
    response = model.generate_content(user_input)
    print(response.text)
"""
