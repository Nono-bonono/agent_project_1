"""
This agent looks for an MPs position on a topic from outside Hansard data and then pools it
for position anlysis. It retrieves data from a set number of sources.
"""

import json
import os
import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from metrics import log_step

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('agent_test_key.env')
from tools_2 import *

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Claude Sonnet used as standard
MODEL = os.environ.get("AGENT_MODEL", "anthropic/claude-haiku-5.5")

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

    for turn in range(max_turns):
        t0 = time.perf_counter()
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        llm_s = time.perf_counter() - t0

        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        tool_names, errors = [], 0
        t1 = time.perf_counter()
        for call in msg.tool_calls or []:          # "or []" handles the no-tools case
            name = call.function.name
            tool_names.append(name)
            print(f"  → {name}({call.function.arguments})", file=sys.stderr)
            try:
                args = json.loads(call.function.arguments)
                content = json.dumps(FUNCS[name](**args))
            except Exception as e:
                content = f"Error: {e}"
                errors += 1
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})
        tool_s = time.perf_counter() - t1

        log_step(agent="web", turn=turn, model=MODEL,
                    llm_s=round(llm_s, 2), tool_s=round(tool_s, 2),
                    prompt_tokens=resp.usage.prompt_tokens,
                    completion_tokens=resp.usage.completion_tokens,
                    tool_calls=tool_names, errors=errors,
                    done=not msg.tool_calls)

        if not msg.tool_calls:
            return msg.content

    log_step(agent="web", hit_max_turns=True)
    return "Stopped: hit max_turns."

if __name__ == "__main__":
    mp = input("MP: ").strip()
    topic = input("Topic: ").strip()
    date_from = input("From (yyyy-mm-dd, blank for any): ").strip() or None
    date_to = input("To (yyyy-mm-dd, blank for now): ").strip() or None

    result = run_agent(mp, topic, date_from, date_to)

    os.makedirs("outputs/position", exist_ok=True)
    filename = f"outputs/postition/web_{mp}_{topic}.md".replace(" ", "_")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {mp} on {topic}\n\n{result}\n")
    print(f"Saved to {filename}")