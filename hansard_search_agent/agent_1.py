"""
This is a simple agent that evaluates an MP's position on 
a given topic from the Hansard public data.
"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agent_loop import agent_loop
from tools_1 import *          # TOOLS, FUNCS

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

def run_agent(mp, topic, date_from=None, date_to=None, max_turns=10):
    question = f"MP: {mp}\nTopic: {topic}\nPeriod: {date_from or 'any'} to {date_to or 'now'}"
    return agent_loop("hansard", MODEL, SYSTEM, question, TOOLS, FUNCS, max_turns)

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


