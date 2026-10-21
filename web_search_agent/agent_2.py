"""
This agent looks for an MPs position on a topic from outside Hansard data and then pools it
for position anlysis. It retrieves data from a set number of sources.
"""

import json
import os
import sys
from tools_2 import *

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('agent_test_key.env')

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Claude Sonnet used as standard
MODEL = os.environ.get("AGENT_MODEL", "anthropic/claude-sonnet-5.5")

SYSTEM = """

"""

# ---- Loop for agent ----