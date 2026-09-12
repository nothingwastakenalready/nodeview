# Deployment checklist

Raffael uses a SQLite database in the Docker volume, so every production deploy
with migrations must start with a backup and end with a health check.

## Local pre-deploy check

Run this from the repository before pushing or deploying:

```bash
scripts/pre-deploy-check.sh
```

This runs the Python tests, frontend tests, frontend build, and validates the
Docker Compose file. The Python suite includes Alembic tests for:

- a fresh SQLite database upgraded to the current head
- a database where `devices.parent_id` and `ix_devices_parent_id` already exist
  but `alembic_version` is still on `20260912_04`

## Production deploy order

Use this order on the VM from `/opt/raffael`.

1. Stop only the app container before touching the database:

   ```bash
   docker compose stop raffael
   ```

2. Create a timestamped database backup:

   ```bash
   mkdir -p backups
   docker run --rm \
     -v raffael_raffael-data:/data:ro \
     -v "$PWD/backups:/backup" \
     alpine \
     sh -c 'cp /data/raffael.db /backup/raffael-before-deploy-$(date +%Y%m%d-%H%M%S).db'
   ```

3. Inspect the live schema before running migrations:

   ```bash
   docker compose run --rm --no-deps raffael python - <<'PY'
   import sqlite3

   db = "/data/raffael.db"
   with sqlite3.connect(db) as con:
       columns = {row[1] for row in con.execute("PRAGMA table_info(devices)")}
       indexes = {row[1] for row in con.execute("PRAGMA index_list(devices)")}
       version = con.execute("SELECT version_num FROM alembic_version").fetchone()
       integrity = con.execute("PRAGMA integrity_check").fetchone()[0]

   print(f"integrity={integrity}")
   print(f"alembic_version={version[0] if version else None}")
   print(f"parent_id={'present' if 'parent_id' in columns else 'missing'}")
   print(f"ix_devices_parent_id={'present' if 'ix_devices_parent_id' in indexes else 'missing'}")
   PY
   ```

4. Pull/build the intended release and run migrations:

   ```bash
   git pull --ff-only
   docker compose build raffael
   docker compose run --rm --no-deps raffael alembic upgrade head
   ```

5. Start the app and verify it:

   ```bash
   docker compose up -d raffael
   docker compose ps
   curl -fsS http://127.0.0.1:8080/health
   ```

6. Check the public page from another machine:

   ```bash
   curl -fsS http://192.168.1.147:8080/health
   ```

## Rollback triggers

Rollback or stop the deploy if any of these happen:

- the backup cannot be created or read
- `PRAGMA integrity_check` is not `ok`
- Alembic fails during migration
- the app container repeatedly restarts
- `/health` does not return HTTP 200 after startup

For a failed deploy, keep the app stopped, preserve the failed database for
inspection, and restore from the timestamped backup only after confirming the
backup passes `PRAGMA integrity_check`.
