"""Run migrations against the Supabase project via REST API."""

import asyncio
import sys
from pathlib import Path

import httpx

SUPABASE_URL = "https://twaostoxlkgooursmkib.supabase.co"
SUPABASE_SERVICE_KEY = "sb_secret_h_9COH7lxsxfoEOseM0eyA_OR55J8ey"

MIGRATIONS_DIR = Path(__file__).parent


async def run_migrations() -> None:
    """Apply all migration SQL files in order."""
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        print("No migration files found.")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        for sql_file in sql_files:
            sql = sql_file.read_text(encoding="utf-8")
            print(f"Applying {sql_file.name}...")

            resp = await client.post(
                f"{SUPABASE_URL}/rest/v1/rpc",
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                },
                json={"query": sql},
            )

            if resp.status_code >= 400:
                # Try the SQL endpoint directly
                resp2 = await client.post(
                    f"{SUPABASE_URL}/pg",
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/sql",
                    },
                    content=sql,
                )
                if resp2.status_code >= 400:
                    print(f"  ERROR ({resp2.status_code}): {resp2.text}")
                    sys.exit(1)
                else:
                    print(f"  OK via /pg endpoint")
            else:
                print(f"  OK")

    print("\nAll migrations applied successfully.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
