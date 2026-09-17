from datetime import datetime, timezone, timedelta

SGT = timezone(timedelta(hours=8))


def log(msg: str) -> None:
    print(f"[{datetime.now(SGT):%H:%M:%S}] {msg}", flush=True)
