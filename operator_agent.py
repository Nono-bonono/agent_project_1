import sys
from pathlib import Path

HERE = Path(__file__).parent   # the "Agent coding" folder

sys.path.append(str(HERE / "hansard_search_agent"))
sys.path.append(str(HERE / "web_search_agent"))

import agent_1
import agent_2

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
They are described in your 'TOOLS' schema.
1) Call agent_1, this is an agent that will search official Parliament records via Hansard.
2) Call agent_2, this is an agent that will search the wider web for material
3)Then write:
- "Overall position (2-3 sentences)"
- "Key arguments each with source, date and url”
- "Any shift in position over time"
- “If a Period is given, pass it as date_from and date_to”
- “Ignore results where the MP is only mentioned in passing”
"Only state what the sources support; say if evidence is thin."
"""

# ---- TOOLS SCHEMA ----

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_site",
            "description": (
                "Search the BBC or PoliticsHome or a politicians official page for articles quoting or written by an MP on a topic. "
                "Returns title, date (may be null), url and a text excerpt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mp_name": {"type": "string"},
                    "topic": {"type": "string"},
                    "site": {"type": "string", "enum": ["bbc", "politicshome", "mp_site"]},
                    "domain": {"type": "string", "description": "Required when site is 'mp_site': the domain from find_mp_site, e.g. 'edmiliband.org'"},
                    "date_from": {"type": "string", "description": "yyyy-mm-dd"},
                    "date_to": {"type": "string", "description": "yyyy-mm-dd"},
                    "take": {"type": "integer", "description": "Max results (default 5)"},
                },
                "required": ["mp_name", "topic", "site"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_article",
            "description": "Fetch the most relevant passages of an article by url, when the search excerpt isn't enough.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "topic": {"type": "string"},
                },
                "required": ["url", "topic"],
            },
        },
    },

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

    result = run_agent(mp, topic, date_from, date_to)

    os.makedirs("outputs", exist_ok=True)
    filename = f"outputs/web_{mp}_{topic}.md".replace(" ", "_")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {mp} on {topic}\n\n{result}\n")
    print(f"Saved to {filename}")