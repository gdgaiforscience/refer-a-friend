# Referral System Architecture

## Evaluation: Custom Application vs. SaaS Integration

When building a referral tracking system for the GDG AI for Science communities (hosted on Bevy), we have two main avenues:

1. **Integration with an Existing Referral SaaS (e.g., Viral Loops, Rewardful)**
   - **Pros:** Feature-rich, includes built-in dashboards, fraud detection, and integrated reward mechanics out of the box.
   - **Cons:** Often requires a monthly subscription fee. More importantly, integrating these tools requires modifying the destination site (Bevy) to include their tracking JavaScript. Since Bevy does not natively support inserting custom JS payloads for custom tracking setups, this path is highly constrained and fragile.

2. **Custom Serverless / Lightweight Tracking Application**
   - **Pros:** Full control over the tracking logic, completely free (no SaaS subscriptions), and effectively bridges the gap by acting as a middle-man. It does not require modifying the Bevy frontend code; it instead passes intent to Bevy via standard UTM parameters which Bevy (or standard Google Analytics attached to the Bevy site) can natively digest.
   - **Cons:** Requires custom maintenance, hosting, and building basic reports/dashboards ourselves.

**Chosen Approach:**
We are proceeding with a **Custom Tracking Application**. It provides the flexibility needed to work around Bevy's limitations by acting as an intelligent link shortener and proxy.

## Architecture & Data Flow

The architecture consists of a single, lightweight backend service built using **Python, FastAPI, and SQLite**.

1. **Link Generation:**
   - A GDG community member provides their email (or unique ID) and the specific Bevy event they want to promote via a simple API or UI form provided by this server.
   - The application generates a unique `referral_code` (e.g., a simple alphanumeric string), stores the mapping in a local SQLite database, and returns a short link (`http://our-domain.com/ref/<referral_code>`).

2. **Tracking & Redirection:**
   - When a potential new member clicks the short link, the request hits the FastAPI server.
   - The server performs a database lookup for the `<referral_code>`.
   - It asynchronously logs a "click" event in the database for tracking metrics.
   - It constructs the final destination URL by taking the original Bevy event URL and appending tracking parameters:
     `?utm_source=referral&utm_medium=member&utm_campaign=<referral_code>`
   - Finally, the server issues an HTTP `302 Found` redirect, sending the user to the Bevy site where they complete registration. Bevy's analytics will naturally pick up the UTM tags to recognize the referral source.

## Security & Privacy
- **Email Hashing:** Member emails are never stored in plain text. They are salted and hashed (SHA-256) before being saved to the database. This prevents email leakage even if the database is compromised.
- **Referral Codes:** High-entropy alphanumeric codes are used for tracking instead of personally identifiable information.
- **UTM Privacy:** UTM parameters only contain the anonymous referral code, not the member's email.
