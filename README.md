# GDG AI for Science – Refer-a-Friend Tracker

A free, serverless referral tracker for GDG events, built with **Google Apps Script**, **Google Sheets**, and the **Bitly API**. Each referrer gets a unique `goo.gle` short link per event. Bitly handles all redirects and click tracking.

## Architecture

| File | Purpose |
|---|---|
| `Code.gs` | Apps Script backend — generates Bitly links, manages rate limiting, HMAC email hashing, and reCAPTCHA verification, logs referrals |
| `Index.html` | Single-page frontend — pure HTML/CSS/JS with reCAPTCHA v2 checkbox |
| `analyze_links.py` | Python script for local performance analysis — fetches click counts per link and generates a visualization |

### Google Sheet structure

The script expects a Google Sheet with two tabs. You must create these manually:

| Tab | Columns / Usage |
|---|---|
| `events` | Row 1: Headers (e.g., `event`, `event_url`). Row 2+: Event names in column A, Event URLs in column B. |
| `leaderboard` | Used for logging generated links. Columns will be: `Timestamp`, `Email`, `Website`, `Bitly Link`, `HashedEmail`. |

---

## Deployment — Apps Script & Web App

### Step 1 — Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new blank spreadsheet.
2. Create two tabs named exactly: `events` and `leaderboard`.
3. Add a header row to `events` and fill in your target events.
4. Add a header row to `leaderboard` with columns: `Timestamp`, `Email`, `Website`, `Bitly Link`, `HashedEmail`.
5. Copy the **Sheet ID** from the URL:
   `https://docs.google.com/spreadsheets/d/`**`SHEET_ID`**`/edit`

### Step 2 — Create the reCAPTCHA Keys

1. Visit the [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin/create) and create a new **reCAPTCHA v2 (Checkbox)** site. 
2. Add your deployment domain (usually `script.google.com`) to the allowed domains list.
3. Copy your **Site Key** and **Secret Key**.

### Step 3 — Create the Apps Script project

1. In the Google Sheet, click **Extensions → Apps Script**.
2. Delete any default code in the editor.
3. Paste the contents of **`Code.gs`** into the default `Code.gs` file.
4. Click **+ (Add file) → HTML**, name it exactly **`Index`** (no extension — Apps Script adds `.html` automatically).
5. Paste the contents of **`Index.html`** into the new `Index.html` file.
6. In `Index.html`, replace the reCAPTCHA Site Key placeholder with your actual **Site Key** in two places:
   - In the `data-sitekey` attribute of the `<div class="g-recaptcha" ...>` tag.
   - In the `const RECAPTCHA_SITE_KEY = '...';` variable in the JavaScript block.

### Step 4 — Configure Script Properties

Sensitive credentials are automatically loaded from Script Properties securely:

1. In the Apps Script editor, go to **Project Settings** (gear icon in the left sidebar).
2. Scroll to **Script Properties** and click **Add script property** to add the following:
   - `SHEET_ID`: Your Google Sheet ID (from Step 1).
   - `BITLY_TOKEN`: Your Bitly API Generic Access Token.
   - `BITLY_GROUP_GUID`: Your Bitly Group GUID (usually found in Bitly account settings).
   - `RECAPTCHA_SECRET`: Your reCAPTCHA Secret Key (from Step 2).
   - `HMAC_SECRET`: A long random string used to hash user emails (this protects email privacy in short links).

### Step 5 — First deploy

1. Click **Deploy → New deployment**.
2. Click the gear icon next to **Type** and select **Web app**.
3. Set:
   - **Description**: e.g. `v1`
   - **Execute as**: Me
   - **Who has access**: Anyone
4. Click **Deploy** — copy the **Web App URL** to share. That's it! 🎉

---

## Deployment — Link Analysis Tools

A Python script is provided to analyze the performance of your referral links locally.

### Step 1 — Local Setup

1. Ensure you have Python 3.x installed.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install requests python-dotenv matplotlib pandas
   ```

### Step 2 — Configure Environment

1. Create a `.env` file in the root directory (you can copy `.env.example`):
   ```bash
   cp .env.example .env
   ```
2. Fill in your credentials:
   - `BITLY_TOKEN`: Your Bitly API token.
   - `BITLY_GROUP_GUID`: Your Bitly Group GUID.
   - `TAG`: The tag used for tracking (default in `Code.gs` is `gdg-track`).

### Step 3 — Run Analysis

1. Run the analysis script:
   ```bash
   python analyze_links.py
   ```
2. The script will output a table of clicks per link to the terminal and save a visualization plot as **`referral_stats.png`**.

---

## Privacy & Security

- **Email Hashing**: Emails are **not** exposed in plain text in the short links. They are hashed using HMAC-SHA256 with a secret salt (`HMAC_SECRET`). Only the first 6 bytes of the hash are used, providing high collision resistance while keeping links short.
- **Rate Limiting**: Users are limited to 10 link generations per day (per email) to prevent abuse.
- **reCAPTCHA**: Protection against automated link generation bots.
- **Storage**: User emails are stored in plain text **only** in the private Google Sheet linked to the deployment.

## How it works

1. A user enters their email and selects an event securely protected by reCAPTCHA v2.
2. The frontend triggers `generateReferralLink` in `Code.gs`.
3. The backend validates the email, enforces a daily rate limit, and validates the reCAPTCHA solution.
4. The backend calls the Bitly API to create a unique `goo.gle/...` short link pointing to the event URL, tagged with the user's hashed email (as a `ref_user` parameter).
5. The generated trackable link is stored in the `leaderboard` tab.
6. The user shares their link. Bitly tracks all clicks on each link.
7. Use `analyze_links.py` to pull these stats and visualize them for a campaign report!
