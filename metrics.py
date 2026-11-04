import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).parent / "outputs" / "metrics" / "metrics.jsonl"
CONTEXT = {"run_id": uuid.uuid4().hex[:8]}   # replaces RUN_ID

def new_run(**labels):
    """Start a new run: fresh run_id plus any labels (version, query...)."""
    CONTEXT.clear()
    CONTEXT.update(run_id=uuid.uuid4().hex[:8], **labels)

def log_step(**fields):
    record = {**CONTEXT,
              "ts": datetime.now(timezone.utc).isoformat(),
              **fields}
    # ... rest unchanged
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


