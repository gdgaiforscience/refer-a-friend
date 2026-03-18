import os
import requests
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import pandas as pd

# --- CONFIGURATION ---
load_dotenv()
BITLY_TOKEN = os.getenv("BITLY_TOKEN")
BITLY_GROUP_GUID = os.getenv("BITLY_GROUP_GUID")
TAG = os.getenv("TAG")
# ---------------------

BASE_URL = "https://api-ssl.bitly.com/v4"
HEADERS = {
    "Authorization": f"Bearer {BITLY_TOKEN}",
    "Content-Type": "application/json"
}


def get_bitlinks_by_tag(tag):
    """Fetches all bitlinks associated with a specific tag, handling pagination."""
    all_links = []
    page = 1
    size = 50  # max page size for Bitly API

    while True:
        url = f"{BASE_URL}/groups/{BITLY_GROUP_GUID}/bitlinks"
        params = {"tags": tag, "size": size, "page": page}

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Error fetching links: {response.status_code} - {response.text}")
            break

        data = response.json()
        links = data.get("links", [])
        if not links:
            break

        all_links.extend(links)

        # Check for pagination
        pagination = data.get("pagination", {})
        next_url = pagination.get("next")
        if not next_url:
            break
        page += 1

    return all_links


def get_click_summary(bitlink):
    """Fetches the total click count for a specific bitlink."""
    # bitlink is usually 'bit.ly/xxxx' or 'goo.gle/xxxx'
    url = f"{BASE_URL}/bitlinks/{bitlink}/clicks/summary"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("total_clicks", 0)
    else:
        print(f"Error fetching clicks for {bitlink}: {response.status_code} - {response.text}")
        return 0


def main():
    if not BITLY_TOKEN:
        print("Please set your BITLY_TOKEN in the .env file.")
        return
    if not BITLY_GROUP_GUID:
        print("Please set your BITLY_GROUP_GUID in the .env file.")
        return

    print(f"Fetching links with tag: {TAG}...")
    links = get_bitlinks_by_tag(TAG)

    if not links:
        print("No links found with that tag.")
        return

    print(f"Found {len(links)} links. Fetching click data...")

    # Collect click counts per unique bitly link
    link_data = []
    for item in links:
        bitlink = item.get("id", "")
        long_url = item.get("long_url", "")
        clicks = get_click_summary(bitlink)
        link_data.append({"bitlink": bitlink, "long_url": long_url, "clicks": clicks})
        print(f"  {bitlink}: {clicks} clicks")

    if not link_data:
        print("No click data available yet.")
        return

    # Build DataFrame and sort by clicks descending
    df = pd.DataFrame(link_data)
    df = df.sort_values(by="clicks", ascending=False).reset_index(drop=True)

    print("\n--- Results (sorted by clicks) ---")
    print(df.to_string(index=False))

    # Visualization
    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.8), 6))
    bars = ax.bar(range(len(df)), df["clicks"], color="skyblue", edgecolor="steelblue")

    # Add click count labels on top of each bar
    for i, (bar, clicks) in enumerate(zip(bars, df["clicks"])):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(clicks), ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["bitlink"], rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Bitly Link")
    ax.set_ylabel("Total Clicks")
    ax.set_title(f"Clicks per Bitly Link (Tag: {TAG})")
    plt.tight_layout()

    output_image = "referral_stats.png"
    plt.savefig(output_image, dpi=150)
    print(f"\nPlot saved to {output_image}")
    plt.show()


if __name__ == "__main__":
    main()
