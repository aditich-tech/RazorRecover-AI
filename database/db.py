import os
import re
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

from config import (
    DATABASE_URL,
    SUPABASE_DB_HOST,
    SUPABASE_DB_PORT,
    SUPABASE_DB_NAME,
    SUPABASE_DB_USER,
    SUPABASE_DB_PASSWORD,
)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema_pg.sql")

def _convert_query(query: str) -> str:
    """
    Converts SQLite-style '?' parameter placeholders to PostgreSQL '%s' placeholders,
    ignoring '?' characters inside quoted string literals.
    """
    if "?" not in query:
        return query
        
    parts = []
    in_quote = False
    quote_char = None
    i = 0
    while i < len(query):
        ch = query[i]
        if not in_quote:
            if ch in ("'", '"'):
                in_quote = True
                quote_char = ch
                parts.append(ch)
            elif ch == "?":
                parts.append("%s")
            else:
                parts.append(ch)
        else:
            parts.append(ch)
            if ch == quote_char:
                if i + 1 < len(query) and query[i + 1] == quote_char:
                    parts.append(query[i + 1])
                    i += 1
                else:
                    in_quote = False
        i += 1
    return "".join(parts)

from psycopg2.pool import ThreadedConnectionPool

_pool = None

def get_pool():
    """Returns the shared ThreadedConnectionPool, initializing it lazily."""
    global _pool
    if _pool is None or getattr(_pool, 'closed', False):
        if DATABASE_URL:
            _pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=15,
                dsn=DATABASE_URL,
                cursor_factory=RealDictCursor
            )
        elif SUPABASE_DB_HOST and SUPABASE_DB_PASSWORD:
            _pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=15,
                host=SUPABASE_DB_HOST,
                port=SUPABASE_DB_PORT,
                dbname=SUPABASE_DB_NAME,
                user=SUPABASE_DB_USER,
                password=SUPABASE_DB_PASSWORD,
                cursor_factory=RealDictCursor,
            )
        else:
            raise RuntimeError(
                "Supabase PostgreSQL is not configured.\n"
                "Please configure DATABASE_URL in your .env file.\n"
                "See .env.example for guidance on obtaining your Supabase connection string."
            )
    return _pool

def get_db_connection():
    """
    Returns a PostgreSQL connection from the connection pool.
    """
    return get_pool().getconn()

@contextmanager
def get_db():
    """Context manager for PostgreSQL connections that reuses pooled connections efficiently."""
    pool = get_pool()
    conn = pool.getconn()
    if conn.closed:
        conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        conn.rollback()
        try:
            pool.putconn(conn, close=True)
        except Exception:
            pass
        raise
    except Exception:
        conn.rollback()
        pool.putconn(conn)
        raise
    else:
        pool.putconn(conn)

def init_db(force_recreate=False):
    """Initializes PostgreSQL schema from schema_pg.sql."""
    with get_db() as conn:
        with conn.cursor() as cur:
            if force_recreate:
                cur.execute("DROP TABLE IF EXISTS audit_logs, recovery_rules, transactions, users CASCADE;")
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                cur.execute(f.read())

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return rows as list of dicts (or single dict)."""
    pg_query = _convert_query(query)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(pg_query, args)
            if cur.description is None:
                return None if one else []
            r = cur.fetchall()
            if not r:
                return None if one else []
            return dict(r[0]) if one else [dict(row) for row in r]

def execute_db(query, args=()):
    """Execute an INSERT/UPDATE/DELETE query and return last_id and row_count."""
    pg_query = _convert_query(query)
    last_id = None
    row_count = 0

    with get_db() as conn:
        with conn.cursor() as cur:
            # If INSERT and no RETURNING clause, attempt appending RETURNING id for last_id
            trimmed = pg_query.strip()
            is_insert = trimmed.upper().startswith("INSERT INTO") and "RETURNING" not in trimmed.upper()
            if is_insert:
                try:
                    cur.execute(f"{trimmed} RETURNING id", args)
                    row = cur.fetchone()
                    if row and "id" in row:
                        last_id = row["id"]
                    row_count = cur.rowcount
                    return {"last_id": last_id, "row_count": row_count}
                except Exception:
                    # Table might not have an id column or constraint prevents it; rollback sub-savepoint & fallback
                    conn.rollback()

            cur.execute(pg_query, args)
            row_count = cur.rowcount
            return {"last_id": last_id, "row_count": row_count}

def execute_many(query, args_list):
    """Execute batch operations in a single transaction using psycopg2 execute_batch."""
    if not args_list:
        return {"row_count": 0}
        
    pg_query = _convert_query(query)
    with get_db() as conn:
        with conn.cursor() as cur:
            execute_batch(cur, pg_query, args_list, page_size=1000)
            row_count = len(args_list)
            return {"row_count": row_count}

def is_db_seeded():
    """Checks if the Supabase PostgreSQL transactions table has at least 10,000 records."""
    try:
        res = query_db("SELECT COUNT(*) as cnt FROM transactions", one=True)
        return res is not None and res.get("cnt", 0) >= 10000
    except Exception:
        return False
