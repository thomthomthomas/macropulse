import os
from dotenv import load_dotenv

load_dotenv()

_client = None


def client():
    global _client
    if _client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set")
        _client = create_client(url, key)
    return _client


def _chunks(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i + n]


def upsert_observations(rows):
    for chunk in _chunks(rows):
        client().table("observations").upsert(
            chunk, on_conflict="series_id,observation_date").execute()


def upsert_snapshot(snapshot):
    client().table("daily_snapshot").upsert(
        snapshot, on_conflict="snapshot_date").execute()


def upsert_news(rows):
    for chunk in _chunks(rows, 200):
        client().table("news").upsert(chunk, on_conflict="url").execute()


def prune_news(days=30):
    client().rpc("prune_old_news", {"days": days}).execute()


def log_run(row):
    client().table("update_runs").insert(row).execute()
