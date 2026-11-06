'''
General loop for agents to call to keep things more streamlined.
'''

import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

from metrics import log_step

load_dotenv("agent_test_key.env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def agent_loop(name, model, system, question, tools, funcs, max_turns=10):
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

    for turn in range(max_turns):
        t0 = time.perf_counter()
        resp = client.chat.completions.create(model=model, messages=messages, tools=tools)
        llm_s = time.perf_counter() - t0

        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        tool_names, errors = [], 0
        t1 = time.perf_counter()
        for call in msg.tool_calls or []:
            fn = call.function.name
            tool_names.append(fn)
            print(f"  → {fn}({call.function.arguments})", file=sys.stderr)
            try:
                args = json.loads(call.function.arguments)
                content = json.dumps(funcs[fn](**args))
            except Exception as e:
                content = f"Error: {e}"
                errors += 1
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})
        tool_s = time.perf_counter() - t1

        log_step(agent=name, turn=turn, model=model,
                 llm_s=round(llm_s, 2), tool_s=round(tool_s, 2),
                 prompt_tokens=resp.usage.prompt_tokens,
                 completion_tokens=resp.usage.completion_tokens,
                 tool_calls=tool_names, errors=errors,
                 output=msg.content if not msg.tool_calls else None,
                 done=not msg.tool_calls)

        if not msg.tool_calls:
            return msg.content

    log_step(agent=name, hit_max_turns=True)
    return "Stopped: hit max_turns."