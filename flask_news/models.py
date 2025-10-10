import uuid
import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Boolean,
    JSON,
    DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -------------------- DATABASE CONFIG --------------------
DB_NAME = "ai_tools.db"  # keep separate from other projects
DB_URL = f"sqlite:///{DB_NAME}"

Base = declarative_base()
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# -------------------- TABLE MODEL --------------------
class AITool(Base):
    __tablename__ = "ai_tools"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    short_description = Column(Text)
    long_description = Column(Text)
    use_cases = Column(JSON)           # list of use cases
    supported_tech = Column(JSON)      # list of supported technologies
    tags = Column(JSON)                # category tags like "Coding", "Education"
    pricing_info = Column(String)      # e.g. Free, Freemium, Paid
    website_url = Column(String)       # official tool link (external)
    source_url = Column(String)        # where scraped from (internal link)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    validated = Column(Boolean, default=False)

    def to_dict(self):
        """Return the model as a Python dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# -------------------- DATABASE FUNCTIONS --------------------
def init_db(db_url=None):
    """Initialize the database and create tables."""
    global engine, SessionLocal
    if db_url:
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

def get_session():
    """Get a new SQLAlchemy session."""
    return SessionLocal()

def add_tool_from_dict(data: dict):
    """Add a new AI tool record from a dictionary."""
    db = get_session()
    try:
        tool = AITool(**data)
        db.add(tool)
        db.commit()
        db.refresh(tool)
        return tool
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding tool: {e}")
    finally:
        db.close()

def get_all_tools():
    """Retrieve all tools as a list of dicts."""
    db = get_session()
    try:
        tools = db.query(AITool).all()
        return [t.to_dict() for t in tools]
    finally:
        db.close()

# -------------------- INIT ON IMPORT --------------------
if __name__ == "__main__":
    init_db()
    print("✅ Database and ai_tools table created successfully!")
