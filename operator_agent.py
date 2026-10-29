import sys
import os
import json

from pathlib import Path

HERE = Path(__file__).parent   # the "Agent coding" folder

sys.path.append(str(HERE / "hansard_search_agent"))
sys.path.append(str(HERE / "web_search_agent"))

from hansard_search_agent import agent_1
from web_search_agent import agent_2

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
You summarize a Member of Parliaments (MP) position using 2 specialized agents available to you.
1) Call ask_hansard, this is an agent that will search official Parliament records via Hansard.
2) Call ask_web, this is an agent that will search the wider web for material
“If a Period is given, pass it as date_from and date_to”
3) Compare what the MP says in Parliament with how they are reported elsewhere, 
and note agreements, contradictions, and gaps.
4)Then write:
- "Overall position (2-3 sentences)"
- "Key arguments each with source, date and url where available”
- "Any shift in position over time"
- "Parliament vs media: agreements, contradictions, gaps"
"Only state what the sources support; say if evidence is thin."
"""

# ---- FUNCTIONS ----

def ask_hansard(mp, topic, date_from=None, date_to=None):
    '''The agent that searches Parliament Hansard'''
    return agent_1.run_agent(mp, topic, date_from=date_from, date_to=date_to)

def ask_web(mp, topic, date_from=None, date_to=None):
    '''The agent that searches certain websites'''
    return agent_2.run_agent(mp, topic, date_from=date_from, date_to=date_to)

# ---- TOOLS SCHEMA ----

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ask_hansard",
            "description": (
                "Run an agent that searches the Parliament website for an MPs position on a given topic"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mp": {"type": "string"},
                    "topic": {"type": "string"},
                    "date_from": {"type": "string", "description": "yyyy-mm-dd"},
                    "date_to": {"type": "string", "description": "yyyy-mm-dd"}
                },
                "required": ["mp", "topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_web",
            "description": (
                "Run an agent that searches certain websites for an MPs position on a given topic"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mp": {"type": "string"},
                    "topic": {"type": "string"},
                    "date_from": {"type": "string", "description": "yyyy-mm-dd"},
                    "date_to": {"type": "string", "description": "yyyy-mm-dd"}
                },
                "required": ["mp", "topic"],
            },
        },
    },
]

FUNCS = {"ask_hansard": ask_hansard, 
         "ask_web": ask_web}

# ---- OPERATOR LOOP ----

def run_operator(mp, topic, date_from = None, date_to = None, max_turns=10):
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

    result = run_operator(mp, topic, date_from, date_to)

    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/combined_{mp}_{topic}.md".replace(" ", "_")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {mp} on {topic}\n\n{result}\n")
    print(f"Saved to {filename}")