"""
This module outsources the imports overhead to unclutter app.py

Note that sys.exit(1) still happens as expected - imports are performed at
start of runtime, so no relying on fetch_response() being called.
"""

import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv

load_dotenv()
API_KEY = os.getenv('API_KEY')
if not find_dotenv() or not API_KEY:
	print("Error: .env file not found or API_KEY missing. Consult README.md")
	sys.exit(1)
genai.configure(api_key=os.environ['API_KEY'])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")


def fetch_llm_response(query: str):
	"""Fetch a response from Gemini 1.5 API"""
	response = model.generate_content(query)
	return response
