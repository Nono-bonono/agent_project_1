'''
Benchmarking function to run and compare the agents. Used to evaulate the setup.
'''

import time
import pandas as pd

import metrics
import operator_agent

VERSION = "v1-baseline-test"   # change before each batch
REPEATS = 1

QUERIES = {
    "ed_energy":        {"mp": "Ed Miliband",   "topic": "energy",  "date_from": None,         "date_to": "2026-06-01"},
    "rush_ali_housing": {"mp": "Rushanara Ali", "topic": "housing", "date_from": None,         "date_to": "2026-06-01"},
    "sajid_energy":     {"mp": "Sajid Javid",   "topic": "energy",  "date_from": "2015-01-01", "date_to": "2018-01-01"},
}

def benchmark_loop():
    for name, query in QUERIES.items():
        for repeat in range(REPEATS):
            metrics.new_run(version=VERSION, query=name, repeat=repeat)
            print(f"Running {name} (repeat {repeat + 1}/{REPEATS})...")
            t0 = time.perf_counter()
            try:
                operator_agent.run_operator(**query)
            except Exception as e:                     
                metrics.log_step(agent="benchmark", error=str(e))
            metrics.log_step(agent="benchmark", total_s=round(time.perf_counter() - t0, 2))

def summarise():
    df = pd.read_json(metrics.LOG_FILE, lines=True)
    df = df[df["version"] == VERSION]

    # Totals per run, then averaged across repeats
    agents = df[df["agent"] != "benchmark"]
    per_run = agents.groupby(["query", "run_id", "agent"]).agg(
        turns=("turn", "count"),
        prompt_tokens=("prompt_tokens", "sum"),
        completion_tokens=("completion_tokens", "sum"),
        llm_s=("llm_s", "sum"),
        errors=("errors", "sum"),
    )
    print(per_run.groupby(["query", "agent"]).mean())

    # Total time per query: mean and spread across repeats
    print(df[df["agent"] == "benchmark"].groupby("query")["total_s"].agg(["mean", "std"]))

    print(df.explode("tool_calls")["tool_calls"].value_counts())

if __name__ == "__main__":
    benchmark_loop()
    summarise()