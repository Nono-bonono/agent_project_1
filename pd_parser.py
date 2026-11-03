import pandas as pd

df = pd.read_json("outputs/metrics.jsonl", lines=True)   # lines=True = one JSON object per line

# Totals per run, per agent
summary = df.groupby(["run_id", "agent"]).agg(
    turns=("turn", "count"),
    prompt_tokens=("prompt_tokens", "sum"),
    completion_tokens=("completion_tokens", "sum"),
    llm_s=("llm_s", "sum"),
    errors=("errors", "sum"),
)
print(summary)

# How often each tool is called
print(df.explode("tool_calls")["tool_calls"].value_counts())