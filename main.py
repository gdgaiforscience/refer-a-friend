import os
import secrets
import string
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
BASE_BEVY_URL = os.getenv("BASE_BEVY_URL") or "https://gdg.community.dev"
BASE_BEVY_URL = BASE_BEVY_URL.rstrip("/")
DOMAIN_URL = (os.getenv("DOMAIN_URL") or "http://127.0.0.1:8000").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gdg_referrals.db")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is required. "
        "Set it in your .env file or via 'fly secrets set SECRET_KEY=...'."
    )

# --- Database Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Referral(Base):
    __tablename__ = "referrals"
    __table_args__ = (UniqueConstraint('member_email', 'event_path', name='_member_event_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    member_email = Column(String, index=True, nullable=False)
    event_path = Column(String, nullable=False)
    referral_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"))
    clicked_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- App Initialization ---
app = FastAPI(title="GDG Referral Tracker")

# --- Pydantic Models for Requests ---
class GenerateLinkRequest(BaseModel):
    member_email: str
    event_path: str

class GenerateLinkResponse(BaseModel):
    referral_url: str
    referral_code: str
    tracking_url: str

# --- Helper Functions ---
def generate_unique_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_email(email: str) -> str:
    """Returns a salted SHA256 hash of the email."""
    normalized_email = email.lower().strip()
    return hashlib.sha256((normalized_email + SECRET_KEY).encode()).hexdigest()

def build_referral_url(event_path: str, referral_code: str) -> str:
    """Constructs the full Bevy URL with UTM parameters."""
    base = event_path if event_path.startswith("http") else f"{BASE_BEVY_URL}/{event_path}"
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}utm_source=referral&utm_medium=member&utm_campaign={referral_code}"

def record_click(db: Session, referral_id: int):
    """Records a click event for a referral."""
    new_click = Click(referral_id=referral_id)
    db.add(new_click)
    db.commit()

# --- Routes ---

@app.post("/generate", response_model=GenerateLinkResponse, status_code=status.HTTP_201_CREATED)
def generate_link(request: GenerateLinkRequest, response: Response, db: Session = Depends(get_db)):
    """
    Generates a unique referral link for a member and specific event.
    If a link already exists for this email and event, returns the existing one.
    """
    clean_path = request.event_path.lstrip("/")
    hashed_email = hash_email(request.member_email)

    existing = db.query(Referral).filter(
        Referral.member_email == hashed_email,
        Referral.event_path == clean_path
    ).first()

    if existing:
        response.status_code = status.HTTP_200_OK
        return {
            "referral_url": build_referral_url(existing.event_path, existing.referral_code),
            "referral_code": existing.referral_code,
            "tracking_url": f"{DOMAIN_URL}/ref/{existing.referral_code}"
        }

    # Generate a new unique code (with collision check)
    while True:
        code = generate_unique_code()
        if not db.query(Referral).filter(Referral.referral_code == code).first():
            break

    new_referral = Referral(
        member_email=hashed_email,
        event_path=clean_path,
        referral_code=code
    )
    db.add(new_referral)
    db.commit()
    db.refresh(new_referral)

    return {
        "referral_url": build_referral_url(clean_path, code),
        "referral_code": code,
        "tracking_url": f"{DOMAIN_URL}/ref/{code}"
    }


@app.get("/ref/{referral_code}")
def redirect_to_bevy(referral_code: str, db: Session = Depends(get_db)):
    """
    Tracks the click and redirects to the Bevy URL with UTM parameters.
    """
    referral = db.query(Referral).filter(Referral.referral_code == referral_code).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral code not found")

    # Record click inline (SQLite is fast enough for this use-case)
    record_click(db, referral.id)

    url = build_referral_url(referral.event_path, referral.referral_code)
    return RedirectResponse(url=url, status_code=302)


@app.get("/stats/{referral_code}")
def get_stats(
    referral_code: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    all_time: bool = False,
    db: Session = Depends(get_db)
):
    """
    Returns click stats for a specific referral link.
    Defaults to current month unless dates or all_time=True are provided.
    """
    referral = db.query(Referral).filter(Referral.referral_code == referral_code).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral code not found")

    query = db.query(Click).filter(Click.referral_id == referral.id)

    if not all_time:
        if start_date or end_date:
            if start_date:
                query = query.filter(Click.clicked_at >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.filter(Click.clicked_at <= datetime.fromisoformat(end_date))
        else:
            # Default to current month
            now = datetime.utcnow()
            query = query.filter(
                func.extract('month', Click.clicked_at) == now.month,
                func.extract('year', Click.clicked_at) == now.year
            )

    clicks_count = query.count()

    return {
        "referral_code": referral_code,
        "member_email": "******** (Hidden for Security)",
        "event_path": referral.event_path,
        "total_clicks": clicks_count,
        "filter": "all_time" if all_time else "custom" if (start_date or end_date) else "current_month"
    }

@app.get("/leaderboard")
def get_leaderboard(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    all_time: bool = False,
    db: Session = Depends(get_db)
):
    """
    Returns a leaderboard of top 10 referrers.
    Defaults to current month unless dates or all_time=True are provided.
    """
    now = datetime.utcnow()
    
    # Base join condition
    join_cond = (Referral.id == Click.referral_id)
    
    if not all_time:
        if start_date or end_date:
            if start_date:
                join_cond &= (Click.clicked_at >= datetime.fromisoformat(start_date))
            if end_date:
                join_cond &= (Click.clicked_at <= datetime.fromisoformat(end_date))
        else:
            # Default to current month
            join_cond &= (func.extract('month', Click.clicked_at) == now.month)
            join_cond &= (func.extract('year', Click.clicked_at) == now.year)

    results = (
        db.query(Referral.referral_code, func.count(Click.id).label("total_clicks"))
        .outerjoin(Click, join_cond)
        .group_by(Referral.referral_code)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    
    return [{"referral_code": r.referral_code, "total_clicks": r.total_clicks} for r in results]
