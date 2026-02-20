# GDG Referral Tracking System

This is a lightweight application designed to bridge the gap between Google Developer Group (GDG) community referrals and the Bevy platform, which lacks native tracking.

It provides an intelligent link shortener and proxy that maps unique referral codes to Bevy events, logging intent locally before issuing a standard 302 Redirect with UTM parameters appended for Bevy analytics to capture.

## Tech Stack
* Python 3.9+
* FastAPI
* SQLite + SQLAlchemy (Local, zero-config database)
* Uvicorn

## Setup Instructions

### 1. Configure the Environment
Copy the example environment file and customize it.

```bash
cp .env.example .env
```

Review `.env`:
- `BASE_BEVY_URL`: The root of your GDG domain (e.g. `https://gdg.community.dev`)
- `DOMAIN_URL`: The domain where *this* tracking server is hosted (e.g. `http://localhost:8000` or `https://ref.mygdg.com`)
- `DATABASE_URL`: Location for the SQLite database (defaults to `./gdg_referrals.db`)

### 2. Install Dependencies
Using your preferred virtual environment (such as `conda` or `venv`), install the requirements:

```bash
# Example using pip:
pip install -r requirements.txt
```

### 3. Run the Development Server (API Backend)
```bash
uvicorn main:app --reload
```
The server will start at `http://127.0.0.1:8000`. 
- **Swagger Documentation:** Visit `http://127.0.0.1:8000/docs` to test the API directly.

### 4. Run the Streamlit Frontend UI
In a separate terminal, launch the Streamlit app:
```bash
streamlit run frontend.py
```
This will open the visual dashboard in your browser where you can generate tracking links and check stats.

## How It Works

### Generate a Link
As a GDG member, I want to invite my friend to the "AI in Finance" event. The Bevy event path is `gdg-ai-for-science-australia/events/details/ai-in-finance-123`.

To get my unique referral link, I (or an automated script) hit the `/generate` endpoint:
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/generate' \
  -H 'Content-Type: application/json' \
  -d '{
  "member_email": "jane.doe@example.com",
  "event_path": "gdg-ai-for-science-australia/events/details/ai-in-finance-123"
}'
```
**Response:**
```json
{
  "referral_url": "http://127.0.0.1:8000/ref/aB3h9K",
  "referral_code": "aB3h9K"
}
```

### Referral Click/Redirect
When a friend clicks `http://127.0.0.1:8000/ref/aB3h9K`:
1. The click is logged in the `gdg_referrals.db`.
2. The user is instantly redirected to the Bevy site:
   `https://gdg.community.dev/gdg-ai-for-science-australia/events/details/ai-in-finance-123?utm_source=referral&utm_medium=member&utm_campaign=jane.doe@example.com`

### Check Stats
To see metrics for a link:
```bash
curl 'http://127.0.0.1:8000/stats/aB3h9K'
```
**Response:**
```json
{
  "referral_code": "aB3h9K",
  "member_email": "jane.doe@example.com",
  "event_path": "gdg-ai-for-science-australia/events/details/ai-in-finance-123",
  "total_clicks": 42
}
```

## Deployment (Fly.io)

This application can be deployed for free on [Fly.io](https://fly.io/). It uses a persistent volume to store the SQLite database securely.

### 1. Install Flyctl
Install the Fly.io command line tool.
- **Mac:** `brew install superfly/tap/flyctl`
- **Linux:** `curl -L https://fly.io/install.sh | sh`
- **Windows:** `pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"`

### 2. Login to Fly
```bash
fly auth login
```

### 3. Create the Persistent Volume
We configured `fly.toml` to expect a volume named `data_vol`. Run this to create a 1GB free-tier volume in your primary region:
```bash
fly volumes create data_vol --region syd --size 1
```
*(Note: Change `--region syd` to whichever region you prefer, such as `iad` or `lhr`.)*

### 4. Set Environment Variables (Secrets)
Set the required secrets (like your Bevy API or DOMAIN_URL) for production securely so they aren't exposed in your code.
```bash
fly secrets set DOMAIN_URL="https://gdg-refer.fly.dev"
fly secrets set BASE_BEVY_URL="https://gdg.community.dev"
```

### 5. Deploy the App
Deploy the API! Fly will read your `Dockerfile` and `fly.toml`.
```bash
fly deploy
```

Now, your API will be live at `https://gdg-refer.fly.dev` (or whichever name Fly assigns) and your database will securely persist across restarts! You can then point your Streamlit frontend (deployed on Streamlit Cloud) to this API url.
