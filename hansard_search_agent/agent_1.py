"""
This is a simple agent that evaluates an MP's position on 
a given topic from the Hansard public data.
"""

import json
import os
import sys
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

SYSTEM = """You summarise a UK MP's position on a topic using Hansard.
Steps: 1) find_mp to get their exact name. 2) search_parliament with
'spokenby:<name> AND words:<topic>' (try synonyms if few hits). 
If a Period is given, pass it to search_parliament as date_from and date_to.
3) get_debate when an excerpt lacks context. Then write:
- Overall position (2-3 sentences)
- Key arguments, each with date + debate title
- Any shift in position over time
Only state what the speeches support; say if evidence is thin."""

# --- Agent Loop ---

def run_agent(mp, topic, date_from = None, date_to = None, max_turns=10):
    question = f"MP: {mp}\nTopic: {topic}\nPeriod: {date_from or 'any'} to {date_to or 'now'}"
    messages = [
        {"role": "system",
         "content": SYSTEM,
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
    mp, topic, *dates = sys.argv[1:]
    print(run_agent(mp, topic, *dates))

    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/{mp}_{topic}.md".replace(" ", "_")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {mp} on {topic}\n\n{result}\n")
    print(f"Saved to {filename}")


