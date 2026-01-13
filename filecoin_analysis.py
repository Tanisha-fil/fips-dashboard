import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}

# ========== 1️⃣ CORE DEVS ATTENDANCE ==========

def fetch_coredevs_attendance():
    repo = "filecoin-project/core-devs"
    url = f"https://api.github.com/repos/{repo}/contents/meetings"
    
    # Try with headers first, fallback to no auth if needed
    resp = requests.get(url, headers=HEADERS)
    files = resp.json()
    
    # Check if we got an error message
    if isinstance(files, dict) and "message" in files:
        print(f"⚠️  API Error: {files['message']}")
        print("Trying without authentication...")
        resp = requests.get(url)
        files = resp.json()
    
    if not isinstance(files, list):
        print(f"❌ Unexpected response format: {type(files)}")
        return pd.DataFrame()

    data = []
    for f in files:
        if f["name"].endswith(".md"):
            raw_url = f["download_url"]
            text = requests.get(raw_url).text
            attendees = re.findall(r"(?i)attendees?:\s*(.+)", text)
            if attendees:
                # Split names separated by commas or newlines
                names = re.split(r"[,•\n]", attendees[0])
                names = [n.strip() for n in names if n.strip()]
                data.append({
                    "Meeting": f["name"].replace(".md",""),
                    "Attendees": len(names)
                })
    df = pd.DataFrame(data)
    df.to_csv("coredevs_attendance.csv", index=False)
    print("✅ Saved coredevs_attendance.csv")
    return df


# ========== 2️⃣ FIP DISCUSSION COMMENTS ==========

def fetch_fip_comments():
    repo = "filecoin-project/FIPs"
    discussions_url = f"https://api.github.com/repos/{repo}/discussions"
    all_discussions = []
    page = 1

    while True:
        resp = requests.get(f"{discussions_url}?per_page=100&page={page}", headers=HEADERS)
        page_data = resp.json()
        
        # Check if we got an error message
        if isinstance(page_data, dict) and "message" in page_data:
            print(f"⚠️  API Error: {page_data['message']}")
            print("Trying without authentication...")
            resp = requests.get(f"{discussions_url}?per_page=100&page={page}")
            page_data = resp.json()
        
        if not page_data or (isinstance(page_data, dict) and "message" in page_data):
            break
        all_discussions.extend(page_data)
        page += 1

    rows = []
    for d in all_discussions:
        title = d["title"]
        num_comments = d["comments"]
        created_at = datetime.strptime(d["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        rows.append({
            "FIP_Title": title,
            "Comments": num_comments,
            "Month": created_at.strftime("%Y-%m")
        })

    df = pd.DataFrame(rows)
    summary = df.groupby("Month")["Comments"].mean().reset_index()
    summary.to_csv("fip_comment_counts.csv", index=False)
    print("✅ Saved fip_comment_counts.csv")
    return summary


# ========== RUN ==========

if __name__ == "__main__":
    print("Fetching Core Devs attendance...")
    a_df = fetch_coredevs_attendance()
    print(a_df.head())

    print("\nFetching FIP comment counts...")
    c_df = fetch_fip_comments()
    print(c_df.head())

    print("\n✅ Done! Use these CSVs to plot your graphs.")