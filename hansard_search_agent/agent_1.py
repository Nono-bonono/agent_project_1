"""
This is a simple agent that evaluates an MP's position on 
a given topic from the Hansard public data.
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
from tools_1 import *
 
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

# Claude Sonnet used as standard
MODEL = os.environ.get("AGENT_MODEL", "anthropic/claude-haiku-5.5")

# --- System prompt ---

SYSTEM = """You summarise a UK MP's position on a topic using Hansard.
Steps: 
1) find_mp to get their exact name. 
2) search_parliament with
'spokenby:<name> AND words:<topic>' (try synonyms if fewer than 5 results, but don't try more than 2 synonyms). 
If a Period is given, pass it to search_parliament as date_from and date_to.
3) Use get_debate for at most 2 debates, only when an excerpt is ambiguous. Prefer excerpts.
Then write:
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

        log_step(agent="hansard", turn=turn, model=MODEL,
                 llm_s=round(llm_s, 2), tool_s=round(tool_s, 2),
                 prompt_tokens=resp.usage.prompt_tokens,
                 completion_tokens=resp.usage.completion_tokens,
                 tool_calls=tool_names, errors=errors,
                 done=not msg.tool_calls)

        if not msg.tool_calls:
            return msg.content

    log_step(agent="hansard", hit_max_turns=True)
    return "Stopped: hit max_turns."

if __name__ == "__main__":
    mp = input("MP: ").strip()
    topic = input("Topic: ").strip()
    date_from = input("From (yyyy-mm-dd, blank for any): ").strip() or None
    date_to = input("To (yyyy-mm-dd, blank for now): ").strip() or None

    result = run_agent(mp, topic, date_from, date_to)

    os.makedirs("outputs/position", exist_ok=True)
    filename = f"outputs/position/{mp}_{topic}.md".replace(" ", "_")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {mp} on {topic}\n\n{result}\n")
    print(f"Saved to {filename}")


