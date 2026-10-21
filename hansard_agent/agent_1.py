"""
This is a simple agent that evaluates movement in British 
political parties based on speeches from the Houses of Parliament"""

import datetime
import json
import os
import sys
import re
import requests
from tools import *
 
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

# --- Agent Loop ---

def run_agent(question, max_turns = 8):

    messages = [
        {"role": SYSTEM,
         "content": (
            "You research UK parliamentary debates using Hansard tools. "
            "Search first, open debates when excerpts aren't enough, "
            "and cite member, date and debate title."
            ),
        },
        {"role": "user", "content": question},
    ]

    for _ in range(max_turns):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:  
            return msg.content

        for call in msg.tool_calls:
            name = call.function.name
            print(f"  → {name}({call.function.arguments})", file=sys.stderr)
            try:
                args = json.loads(call.function.arguments)  # arguments arrive as a JSON string
                content = json.dumps(FUNCS[name](**args))
            except Exception as e:  # let the model see and recover from errors
                content = f"Error: {e}"
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

    return "Stopped: hit max_turns."

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What have MPs said about AI regulation this year?"
    print(run_agent(q))


