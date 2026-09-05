import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env if present
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Database Configuration (Supabase PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_DB_HOST = os.environ.get("SUPABASE_DB_HOST")
SUPABASE_DB_PORT = int(os.environ.get("SUPABASE_DB_PORT", 5432))
SUPABASE_DB_NAME = os.environ.get("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.environ.get("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD", "")

# SQLite path kept for migration script access
SQLITE_DB_PATH = os.path.join(BASE_DIR, "razor_recover.db")

SECRET_KEY = os.environ.get("SECRET_KEY", "razor-recover-ai-demo-secret-key-2026")
IS_DEMO_ENVIRONMENT = True
PORT = int(os.environ.get("PORT", 5000))
