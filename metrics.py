import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).parent / "outputs" / "metrics" / "metrics.jsonl"
RUN_ID = uuid.uuid4().hex[:8]   # one ID per program run, shared by every agent

def log_step(**fields):
    """Append one record (one line of JSON) to the log file."""
    record = {"run_id": RUN_ID,
              "ts": datetime.now(timezone.utc).isoformat(),
              **fields}
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


