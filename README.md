# MP Position Agents

A small multi-agent system that summarises a UK MP's position on a topic. It compares what they say in Parliament with how they're reported elsewhere.

Built from scratch in Python as a learning project. There's no agent framework: each agent is a plain tool-calling loop over the OpenAI-compatible API (via OpenRouter).

## How it works

```
                 operator_agent.py
                (orchestrator / LLM)
                 /                \
        ask_hansard              ask_web
            |                       |
   hansard_search_agent      web_search_agent
   - find_mp                 - search_guardian
   - search_parliament       - search_site (BBC, PoliticsHome, MP's site)
   - get_debate              - read_article
            |                       |
   Hansard + Members APIs    Guardian API + Tavily
```

1. **Hansard agent** (`agent_1.py`): finds the MP, searches their spoken contributions on the topic, and reads full debates only when an excerpt is ambiguous.
2. **Web agent** (`agent_2.py`): searches the Guardian, BBC, PoliticsHome and the MP's own website. It keeps the MP's own statements separate from commentary about them.
3. **Operator** (`operator_agent.py`): calls both agents as tools, then compares the results to give the MP's overall position, key arguments with sources, any shift over time, and where Parliament and the media agree, contradict or leave gaps.

Each agent is told to state only what its sources support and to say when the evidence is thin.

## Setup

Requires Python 3.10+.

```bash
pip install openai python-dotenv requests tavily-python
```

Create `agent_test_key.env` in the project root:

```
OPENROUTER_API_KEY=...
GUARDIAN_API_KEY=...
TAVILY_API_KEY=...
AGENT_MODEL=anthropic/claude-sonnet-5.5   # optional, this is the default
```

## Usage

Run the full pipeline:

```bash
python operator_agent.py
```

You'll be prompted for an MP, a topic and an optional date range. The output is saved to `outputs/combined_<MP>_<Topic>.md`.

Each agent also runs on its own:

```bash
python hansard_search_agent/agent_1.py   # → outputs/<MP>_<Topic>.md
python web_search_agent/agent_2.py       # → outputs/web_<MP>_<Topic>.md
```

Tool calls are printed to stderr as they happen, so you can watch the agent work.

## Example output

See `outputs/combined_Ed_Miliband_AI.md`.

## Project structure

```
├── operator_agent.py          # orchestrator
├── hansard_search_agent/
│   ├── agent_1.py             # agent loop + prompt
│   └── tools_1.py             # Hansard/Members API tools + schemas
├── web_search_agent/
│   ├── agent_2.py
│   └── tools_2.py             # Guardian/Tavily tools + schemas
├── outputs/                   # saved reports
└── agent_test_key.env         # API keys (not committed)
```

## Limitations

- The web agent only covers a fixed set of sources, so coverage depends on what they've published.
- Tavily doesn't always return publication dates.
- MP name matching relies on the Parliament Members API search.

## Roadmap

- [ ] Analysis step (in the operator or as a 4th agent)
- [ ] ...