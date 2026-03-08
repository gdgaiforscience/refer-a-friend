# GDG AI for Science – Refer-a-Friend Tracker

A free, serverless referral tracker for GDG events, built with **Google Apps Script**, **Google Sheets**, and the **Bitly API**. Each referrer gets a unique `go.gle` short link per event. Bitly handles all redirects and click tracking.

## Architecture

| File | Purpose |
|---|---|
| `Code.gs` | Apps Script backend — generates Bitly links, manages referrals |
| `Index.html` | Single-file frontend — pure HTML/CSS/JS, served by the same Web App |

### Google Sheet structure

The script auto-creates two tabs on first run:

| Tab | Columns |
|---|---|
| `events` | `event_name`, `event_url` |
| `referrals` | `email`, `event_name`, `bitly_link`, `created_at` |

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

At the top of `Code.gs`, set the Sheet ID:

```javascript
var SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE";  // from Step 1
```

### Step 4 — Set Bitly API credentials

1. In the Apps Script editor, go to **Project Settings** (gear icon in the sidebar).
2. Scroll to **Script Properties** and click **Add script property**:
   - `BITLY_TOKEN` = your Bitly API access token
   - `BITLY_GROUP_GUID` = *(optional)* your Bitly group GUID — required for some enterprise accounts

> **Tip:** If you need to find your group GUID, run the `listBitlyGroups()` function from the Apps Script editor (Run → listBitlyGroups) and check the **Execution log** for the result.

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

Edit the `events` tab in the Google Sheet at any time — no redeployment needed:

| event_name | event_url |
|---|---|
| GDG AI for Science - March Meetup | https://gdg.community.dev/events/details/... |

---

## How it works

1. A user enters their email and selects an event
2. The app calls the Bitly API to create a unique `go.gle/...` short link pointing to the event URL
3. The user shares their link with friends
4. Bitly tracks all clicks on each link
5. Referral data is stored in the Google Sheet

## Privacy

Emails are stored **in plain text** in the Google Sheet, which is owned by and accessible only to the Google account that deployed the script. The Bitly API token is stored securely in Apps Script's Script Properties and is not exposed to end users.

---
