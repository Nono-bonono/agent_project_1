"""
This is a simple agent that evaluates movement in British 
political parties based on speeches from the Houses of Parliament"""

import datetime
import json
import os
import sys
import re
import requests
 
from dotenv import load_dotenv
from openai import OpenAI
 
load_dotenv('agent_test_key.env')  
 
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Claude Sonnet used as standard
MODEL = os.environ.get("AGENT_MODEL", "anthropic/claude-sonnet-5.5")


# --- System prompt ---

SYSTEM = """You are a useful assistant that evaluates debates from the British Houses of Parliament
that are relevant to the user query. These debates should be within the user given timeframe.
You will then run them through a model that you have access to through your tools and asses the results."""



