import string
import random
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import func
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
BASE_BEVY_URL = os.getenv("BASE_BEVY_URL") or "https://gdg.community.dev"
BASE_BEVY_URL = BASE_BEVY_URL.rstrip("/")
DOMAIN_URL = (os.getenv("DOMAIN_URL") or "http://127.0.0.1:8000").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gdg_referrals.db")

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
    return ''.join(random.choice(chars) for _ in range(length))

def record_click(db: Session, referral_id: int):
    """Background task to record a click asynchronously"""
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
    # Clean the event path to avoid double slashes
    clean_path = request.event_path.lstrip("/")

    # 1. Check if this member already has a link for this specific event
    existing = db.query(Referral).filter(
        Referral.member_email == request.member_email,
        Referral.event_path == clean_path
    ).first()

    if existing:
        response.status_code = status.HTTP_200_OK
        tracking_url = f"{DOMAIN_URL}/ref/{existing.referral_code}"
        
        # Construct the final Bevy URL with UTM parameters
        if existing.event_path.startswith("http"):
            bevy_base = existing.event_path
        else:
            bevy_base = f"{BASE_BEVY_URL}/{existing.event_path}"
        
        separator = "&" if "?" in bevy_base else "?"
        referral_url = f"{bevy_base}{separator}utm_source=referral&utm_medium=member&utm_campaign={existing.referral_code}"
        
        return {
            "referral_url": referral_url, 
            "referral_code": existing.referral_code,
            "tracking_url": tracking_url
        }

    # 2. Generate a new unique code (checking for collisions in the DB)
    while True:
        code = generate_unique_code()
        collision = db.query(Referral).filter(Referral.referral_code == code).first()
        if not collision:
            break

    new_referral = Referral(
        member_email=request.member_email,
        event_path=clean_path,
        referral_code=code
    )
    db.add(new_referral)
    db.commit()
    db.refresh(new_referral)

    # Construct the tracking (internal) and full (referral) URLs
    tracking_url = f"{DOMAIN_URL}/ref/{code}"
    
    # Construct the final Bevy URL with UTM parameters
    if clean_path.startswith("http"):
        bevy_base = clean_path
    else:
        bevy_base = f"{BASE_BEVY_URL}/{clean_path}"
    
    separator = "&" if "?" in bevy_base else "?"
    referral_url = f"{bevy_base}{separator}utm_source=referral&utm_medium=member&utm_campaign={code}"
    
    return {
        "referral_url": referral_url,
        "referral_code": code,
        "tracking_url": tracking_url
    }


@app.get("/ref/{referral_code}")
def redirect_to_bevy(
    referral_code: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Tracks the click and redirects to the Bevy URL with UTM parameters.
    """
    referral = db.query(Referral).filter(Referral.referral_code == referral_code).first()
    
    if not referral:
        raise HTTPException(status_code=404, detail="Referral code not found")

    # Log click asynchronously so the redirect is very fast
    # Note: background_tasks use the same db session so be careful if the session closes.
    # Safe practice for background writes: open a new session or write directly
    # To keep this simple and safe, we do it inline here, or could use standard queue.
    # Doing inline since DB is fast sqlite.
    record_click(db, referral.id)

    # Construct the final URL
    if referral.event_path.startswith("http"):
        url = referral.event_path
    else:
        url = f"{BASE_BEVY_URL}/{referral.event_path}"
    
    # Append UTM parameters. Use standard URL query param delimiters (?) or (&).
    separator = "&" if "?" in url else "?"
    url += f"{separator}utm_source=referral&utm_medium=member&utm_campaign={referral.referral_code}"

    # 302 Found (Standard Temporary Redirect)
    return RedirectResponse(url=url, status_code=302)


@app.get("/stats/{referral_code}")
def get_stats(referral_code: str, db: Session = Depends(get_db)):
    """
    Returns basic click stats for a specific referral link.
    """
    referral = db.query(Referral).filter(Referral.referral_code == referral_code).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral code not found")

    clicks_count = db.query(Click).filter(Click.referral_id == referral.id).count()
    return {
        "referral_code": referral_code,
        "member_email": referral.member_email,
        "event_path": referral.event_path,
        "total_clicks": clicks_count
    }

@app.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    """
    Returns a leaderboard of top 10 referrers based on total clicks.
    """
    results = (
        db.query(Referral.referral_code, func.count(Click.id).label("total_clicks"))
        .outerjoin(Click, Referral.id == Click.referral_id)
        .group_by(Referral.referral_code)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    
    return [{"referral_code": r.referral_code, "total_clicks": r.total_clicks} for r in results]
