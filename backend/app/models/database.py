import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.utils.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL
connect_args = {}

# Automatically URL-encode password if it contains special characters like '@'
if db_url and "://" in db_url and not db_url.startswith("sqlite"):
    try:
        scheme, rest = db_url.split("://", 1)
        if "@" in rest:
            userinfo, host_db = rest.rsplit("@", 1)
            if ":" in userinfo:
                username, password = userinfo.split(":", 1)
                # URL-encode only the password part
                encoded_password = quote_plus(password)
                db_url = f"{scheme}://{username}:{encoded_password}@{host_db}"
                logger.info("Automatically escaped special characters in database password.")
    except Exception as parse_err:
        logger.warning(f"Could not parse database URL for escaping: {parse_err}")

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(db_url, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        logger.info("Successfully connected to the MySQL database!")
except Exception as e:
    logger.warning(
        f"Could not connect to database '{db_url}' ({e}). "
        "Falling back to local SQLite database: sqlite:///./career_copilot.db"
    )
    db_url = "sqlite:///./career_copilot.db"
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
