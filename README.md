# MP Position Agents

> **Status: parked.** This project is paused for now. Future targets are further optimisation of the agents (hyperparameters, cost and latency) and analysis of political stances (say-vs-vote comparison and a critic step; see the roadmap).

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
pip install openai python-dotenv requests tavily-python pandas
```

Create `agent_test_key.env` in the project root:

```
OPENROUTER_API_KEY=...
GUARDIAN_API_KEY=...
TAVILY_API_KEY=...
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

## Benchmarking

`agent_loop.py` holds the tool-calling loop shared by all three agents. `metrics.py` logs one line per LLM turn (tokens, timings, tool calls, errors) to `outputs/metrics/metrics.jsonl`.

`benchmark.py` runs a fixed set of queries through the operator and prints per-agent totals. Change `VERSION` before each batch so runs can be compared. To inspect results, open `outputs/metrics/check_file.ipynb` (local only, because `outputs/` is gitignored).

First comparison, before and after the shared-loop refactor (3 queries, 1 run each, so treat it as indicative only):

| Version | LLM calls / run | Prompt tokens | Completion tokens | Wall time | Errors |
|---|---|---|---|---|---|
| v1-baseline | 9.7 | 64,594 | 7,001 | 73 s | 0 |
| v2-shared-loop | 11.0 | 60,780 | 9,953 | 83 s | 0 |

The refactor was meant to remove duplicated code, not to speed things up. Differences here are within what you'd expect from run-to-run variation at this sample size.

## Example output

See [`examples/combined_Ed_Miliband_AI.md`](examples/combined_Ed_Miliband_AI.md). Live runs save to `outputs/`, which is gitignored.

## Project structure

```
├── operator_agent.py          # orchestrator
├── agent_loop.py              # shared tool-calling loop
├── metrics.py                 # per-turn logging
├── benchmark.py               # benchmark runner and summary
├── hansard_search_agent/
│   ├── agent_1.py             # prompt + tools wiring
│   └── tools_1.py             # Hansard/Members API tools + schemas
├── web_search_agent/
│   ├── agent_2.py
│   └── tools_2.py             # Guardian/Tavily tools + schemas
├── examples/                  # sample report
├── outputs/                   # reports + metrics (gitignored)
└── agent_test_key.env         # API keys (not committed)
```

## Limitations

- The web agent only covers a fixed set of sources, so coverage depends on what they've published.
- Tavily doesn't always return publication dates.
- MP name matching relies on the Parliament Members API search.

## Roadmap

- [ ] Optimise the agents: tune models and hyperparameters, using the benchmark to measure cost, latency and errors
- [ ] Say-vs-vote agent: compare what an MP says with their voting record (Commons Votes API)
- [ ] Critic agent: check the final report against its sources
- [ ] Party comparison across several MPs
