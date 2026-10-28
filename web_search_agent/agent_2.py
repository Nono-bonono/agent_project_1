"""
This agent looks for an MPs position on a topic from outside Hansard data and then pools it
for position anlysis. It retrieves data from a set number of sources.
"""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('agent_test_key.env')
from tools_2 import *

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Claude Sonnet used as standard
MODEL = os.environ.get("AGENT_MODEL", "anthropic/claude-sonnet-5.5")

SYSTEM = """
You summarize a Member of Parliaments (MP) position on a given topic from material on the web.
1) “call search_site with site='mp_site' and domain set to the website without 
‘https://’ or ‘www.’. Skip this step if the website is null.”
2) "use 'search_guardian' to find information from the Guardian"
3) "use 'search_site' to find material from the BBC and PoliticsHome"

"Make sure to use 'read_article' sparingly to conserve usage.
Also make sure to separate an MPs own position from commentary about them."

4)Then write:
- "Overall position (2-3 sentences)"
- "Key arguments each with source, date and url”
- "Any shift in position over time"
- “If a Period is given, pass it as date_from and date_to”
- “Ignore results where the MP is only mentioned in passing”
"Only state what the sources support; say if evidence is thin."
"""

# --- Agent Loop ---

def run_agent(mp, topic, date_from = None, date_to = None, max_turns=14):
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
    mp = input("MP: ").strip()
    topic = input("Topic: ").strip()
    date_from = input("From (yyyy-mm-dd, blank for any): ").strip() or None
    date_to = input("To (yyyy-mm-dd, blank for now): ").strip() or None

    result = run_agent(mp, topic, date_from, date_to)

    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/web_{mp}_{topic}.md".replace(" ", "_")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {mp} on {topic}\n\n{result}\n")
    print(f"Saved to {filename}")