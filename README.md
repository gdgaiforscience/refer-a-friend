# GDG AI for Science – Refer-a-Friend Tracker

A free, serverless referral tracker for GDG events, built with **Google Apps Script**, **Google Sheets**, and the **Bitly API**. Each referrer gets a unique `goo.gle` short link per event. Bitly handles all redirects and click tracking.

## Architecture

| File | Purpose |
|---|---|
| `Code.gs` | Apps Script backend — generates Bitly links, manages rate limiting and reCAPTCHA verification, logs referrals |
| `Index.html` | Single-file frontend — pure HTML/CSS/JS with reCAPTCHA v3 |

### Google Sheet structure

The script expects a Google Sheet with two tabs. You must create these manually:

| Tab | Columns / Usage |
|---|---|
| `events` | Row 1: Headers (e.g., `event`, `event_url`). Row 2+: Event names in column A, Event URLs in column B. |
| `leaderboard` | Used for logging generated links. Columns will be: `Timestamp`, `Email`, `Website`, `Bitly Link`. |

---

## Deployment

### Step 1 — Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new blank spreadsheet.
2. Create two tabs named exactly: `events` and `leaderboard`.
3. Add a header row to `events` and fill in your target events.
4. Copy the **Sheet ID** from the URL:
   `https://docs.google.com/spreadsheets/d/`**`SHEET_ID`**`/edit`

### Step 2 — Create the reCAPTCHA Keys

1. Visit the [reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin/create) and create a new **reCAPTCHA v3** site.
2. Copy your **Site Key** and **Secret Key**.

### Step 3 — Create the Apps Script project

1. In the Google Sheet, click **Extensions → Apps Script**.
2. Delete any default code in the editor.
3. Paste the contents of **`Code.gs`** into the default `Code.gs` file.
4. Click **+ (Add file) → HTML**, name it exactly **`Index`** (no extension — Apps Script adds `.html` automatically).
5. Paste the contents of **`Index.html`** into the new `Index.html` file.
6. In `Index.html`, replace the reCAPTCHA Site Key placeholder with your actual **Site Key** in two places:
   - In the `<script src="...">` tag in the `<head>`.
   - In the `const RECAPTCHA_SITE_KEY = '...';` variable in the JavaScript block.

### Step 4 — Configure Script Properties

Sensitive credentials are automatically loaded from Script Properties securely:

1. In the Apps Script editor, go to **Project Settings** (gear icon in the left sidebar).
2. Scroll to **Script Properties** and click **Add script property** to add the following three properties:
   - `SHEET_ID` = your Google Sheet ID (from Step 1)
   - `BITLY_TOKEN` = your Bitly API Generic Access Token
   - `RECAPTCHA_SECRET` = your reCAPTCHA Secret Key (from Step 2)

*(Note: The script will automatically fetch your `BITLY_GROUP_GUID` on its first run and cache it so you don't need to specify it manually).*

### Step 5 — First deploy

1. Click **Deploy → New deployment**.
2. Click the gear icon next to **Type** and select **Web app**.
3. Set:
   - **Description**: e.g. `v1`
   - **Execute as**: Me
   - **Who has access**: Anyone
4. Click **Deploy** — copy the **Web App URL** to share. That's it! 🎉

---

## Updating events

Edit the `events` tab in the Google Sheet at any time — no redeployment needed. New events will appear in the frontend dropdown automatically.

| event_name | event_url |
|---|---|
| GDG AI for Science - March Meetup | https://gdg.community.dev/events/details/... |

---

## How it works

1. A user enters their email and selects an event securely protected by reCAPTCHA v3.
2. The frontend triggers `generateReferralLink` in `Code.gs`.
3. The backend validates the email, enforces a daily rate limit per email, and validates the reCAPTCHA score.
4. The backend calls the Bitly API to create a unique `goo.gle/...` short link pointing to the event URL, tagged with the user's base64-encoded email.
5. The generated trackable link is stored in the `leaderboard` tab.
6. The user shares their link with friends. Bitly tracks all clicks on each link.

## Privacy

Emails are stored **in plain text** in the Google Sheet, which is owned by and accessible only to the Google account that deployed the script. API tokens and secrets are stored securely in Apps Script's Script Properties and are never exposed to end users.
