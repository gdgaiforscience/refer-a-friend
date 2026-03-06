# GDG AI for Science – Refer-a-Friend Tracker

A free, serverless referral tracker for GDG events, built with **Google Apps Script** and backed by a **Google Sheet**. No server, no Docker, no database to manage.

## Architecture

| File | Purpose |
|---|---|
| `Code.gs` | Apps Script backend — handles link generation, click tracking & redirects, stats, leaderboard |
| `Index.html` | Single-file frontend — pure HTML/CSS/JS, served by the same Web App |

### Google Sheet structure

The script auto-creates two tabs on first run:

| Tab | Columns |
|---|---|
| `referrals` | `email`, `event_path`, `referral_code`, `created_at` |
| `clicks` | `referral_code`, `clicked_at` |

---

## Deployment

### Step 1 — Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new blank spreadsheet.
2. Copy the **Sheet ID** from the URL:
   `https://docs.google.com/spreadsheets/d/`**`SHEET_ID`**`/edit`

### Step 2 — Create the Apps Script project

1. In the Sheet, click **Extensions → Apps Script**.
2. Delete any default code in the editor.
3. Paste the contents of **`Code.gs`** into the `Code.gs` file.
4. Click **+ (Add file) → HTML**, name it exactly **`Index`** (no extension — Apps Script adds `.html` automatically).
5. Paste the contents of **`Index.html`** into the new `Index.html` file.

### Step 3 — Configure `Code.gs`

At the top of `Code.gs`, set the one required constant:

```javascript
var SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE";  // from Step 1
```

Optionally update the `EVENTS` map to add or change event names and URLs.

### Step 4 — First deploy

1. Click **Deploy → New deployment**.
2. Click the gear icon next to **Type** and select **Web app**.
3. Set:
   - **Description**: e.g. `v1`
   - **Execute as**: Me
   - **Who has access**: Anyone
4. Click **Deploy** — copy the **Web App URL** to share. That's it! 🎉

---

## Updating events

Edit the `EVENTS` map in `Code.gs` and redeploy (new version) at any time:

```javascript
var EVENTS = {
  "My New Event": "https://gdg.community.dev/events/details/...",
  // ...
};
```


## Privacy

Emails are stored **in plain text** in the Google Sheet, which is owned by and accessible only to the Google account that deployed the script. There is no public-facing exposure of email addresses — the leaderboard shows only referral codes.

---


