# GDG Referral Tracker

A lightweight refer-a-friend link generator and tracker for Google Developer Group (GDG) communities on Bevy.

It acts as an intelligent link shortener: members generate a unique referral code, share the short link, and the service logs every click before redirecting visitors to the Bevy event page with UTM parameters appended.

## Tech Stack

* Python 3.9+
* **FastAPI** — REST API backend
* **SQLite + SQLAlchemy** — zero-config database
* **Streamlit** — frontend dashboard
* **Uvicorn** — ASGI server

## Quick Start

### 1. Configure the Environment

```bash
cp .env.example .env
```

Edit `.env` and set:

| Variable | Description |
|----------|-------------|
| `PUBLIC_URL` | **Production Only.** The external URL (e.g. `https://gdg-refer.fly.dev`). Used for links shared with users. |
| `DOMAIN_URL` | Where *this* API backend service is hosted (e.g. `http://localhost:8000`) |
| `DATABASE_URL` | SQLite path (default: `sqlite:///./gdg_referrals.db`) |
| `SECRET_KEY` | **Required.** Salt for hashing member emails. Keep secret and persistent! |

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the backend API

```bash
uvicorn main:app --reload
```

The API starts at `http://127.0.0.1:8000`.
Interactive Swagger docs to see API capabilities: `http://127.0.0.1:8000/docs`.

### 4. Run the Frontend

In a separate terminal:

```bash
streamlit run frontend.py
```

## Security & Privacy

* **Email hashing** — Member emails are salted + SHA-256 hashed before storage. The `SECRET_KEY` env var is required at startup.
* **No PII in URLs** — UTM parameters use the anonymous referral code, never the email.
* **Cryptographic codes** — Referral codes are generated with `secrets.choice` (CSPRNG).

## Deployment

This app has two components that can be deployed independently:

| Component | What | Hosting Options |
|-----------|------|-----------------|
| **API backend** (`main.py`) | FastAPI + SQLite | Fly.io, Render, Google Cloud Run |
| **Frontend** (`frontend.py`) | Streamlit dashboard | Streamlit Community Cloud (free) |

### Option A: Fly.io (Backend)

Fly.io offers a free tier with persistent volumes for SQLite.

1. Install Flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Prepare: `fly launch --no-deploy`
3. Create volume: `fly volumes create data --region syd --size 1`
4. Set secrets:
   ```bash
   fly secrets set SECRET_KEY="your-secret-key-here"
   fly secrets set PUBLIC_URL="https://gdg-refer.fly.dev"
   fly secrets set DATABASE_URL="sqlite:////data/gdg_referrals.db"
   ```
5. Deploy: `fly deploy`

The Frontend will be live at `https://gdg-refer.fly.dev` (and the API).

> [!TIP]
> Destroy the app and everything with `fly apps destroy gdg-refer`.

> [!TIP]
> `DOMAIN_URL` is set automatically in `fly.toml` based on the app name. If you change the app name or add a custom domain, update the `DOMAIN_URL` value in `fly.toml` to match.

### Option B: Render (Backend — Free Tier)

[Render](https://render.com) offers a free web service tier with a persistent disk add-on.

1. Push this repo to GitHub.
2. On Render, create a **New Web Service** → connect your repo.
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables under **Environment**:
   - `SECRET_KEY`, `DOMAIN_URL`, `DATABASE_URL`
5. *(Optional)* Add a **Disk** (mount path `/data`, 1 GB) and set `DATABASE_URL=sqlite:////data/gdg_referrals.db` for persistence across deploys.

> [!NOTE]
> Render's free tier spins down after inactivity. The first request after sleep takes ~30 seconds to cold-start.

### Frontend: Streamlit Community Cloud (Free)

[Streamlit Community Cloud](https://streamlit.io/cloud) hosts Streamlit apps for free from a GitHub repo.

1. Push this repo to GitHub (or a fork containing `frontend.py` and `requirements.txt`).
2. Go to [share.streamlit.io](https://share.streamlit.io) and create a new app.
3. Set the **main file** to `frontend.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   API_URL = "https://your-backend-domain.com"
   ```
5. Deploy — the dashboard will be live at `https://your-app.streamlit.app`.

## Backup the Database
Execute:
```
fly sftp get /data/gdg_referrals.db ./backup/prod_backup.db
fly sftp get /data/gdg_referrals.db-shm ./backup/prod_backup.db-shm
fly sftp get /data/gdg_referrals.db-wal ./backup/prod_backup.db-wal
python utils/decrypt.py --db ./prod_backup.db
```

### General Production Guidance

- **`SECRET_KEY`** must be the same across deploys — changing it invalidates all existing email hashes.
- **SQLite** works well for community-scale traffic. For higher concurrency, replace with PostgreSQL by changing `DATABASE_URL` (e.g. `postgresql://user:pass@host/db`).
- **HTTPS** — ensure `DOMAIN_URL` uses `https://` in production so shared referral links are secure.

## Known Limitations

* **No rate limiting** on `/generate` — a bot could fill the database. Consider adding middleware if exposed publicly.
* **No authentication** — any visitor can generate links. Suitable for trusted community use.
* **SQLite** — single-writer; fine for low–medium traffic. For higher scale, swap to PostgreSQL.
