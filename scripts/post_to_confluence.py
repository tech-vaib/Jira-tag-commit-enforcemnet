#!/usr/bin/env python3
import os
import requests
import subprocess
import sys
from datetime import datetime
import re

# ========== CONFIGURATION ==========
JIRA_BASE_URL = "https://yourcompany.atlassian.net/browse/"  # 🔁 Replace with your actual JIRA base URL

# ========== ENVIRONMENT VARIABLES ==========
CONFLUENCE_API_USER = os.getenv("CONFLUENCE_API_USER")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")
CONFLUENCE_PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID")  # Optional

if not all([CONFLUENCE_API_USER, CONFLUENCE_API_TOKEN, CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY]):
    print("❌ Missing one or more required environment variables.")
    sys.exit(1)

AUTH = (CONFLUENCE_API_USER, CONFLUENCE_API_TOKEN)
HEADERS = {"Content-Type": "application/json"}

# ========== FUNCTIONS ==========

def get_latest_and_previous_tags():
    tags = subprocess.check_output(['git', 'tag', '--sort=-creatordate']).decode().splitlines()
    if len(tags) < 2:
        print("❌ Need at least two tags to generate changelog.")
        sys.exit(1)
    return tags[0], tags[1]

def get_commits_between_tags(new_tag, old_tag):
    output = subprocess.check_output(['git', 'log', '--pretty=format:%s', f'{old_tag}..{new_tag}'])
    messages = output.decode().splitlines()
    return messages

def autolink_jira_tickets(message):
    return re.sub(r'\b([A-Z]+-\d+)\b', fr'<a href="{JIRA_BASE_URL}\1">\1</a>', message)

def build_html_body(commits):
    timestamp = datetime.now().strftime("%H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    page_title = f"HIF-Release - {date_str}"

    repo_name = os.getenv("GITHUB_REPOSITORY", "unknown-repo").split("/")[-1]

    lines = [f"<h2>{repo_name} – {timestamp}</h2>", "<ul>"]
    for msg in commits:
        linked = autolink_jira_tickets(msg)
        lines.append(f"<li>{linked}</li>")
    lines.append("</ul>")

    return page_title, "\n".join(lines)

def find_page_by_title(title):
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    params = {
        "title": title,
        "spaceKey": CONFLUENCE_SPACE_KEY,
        "expand": "version,body.storage"
    }
    response = requests.get(url, auth=AUTH, headers=HEADERS, params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None

def update_page(page, new_content):
    page_id = page["id"]
    old_body = page["body"]["storage"]["value"]
    version = page["version"]["number"] + 1

    new_body = new_content + old_body

    payload = {
        "id": page_id,
        "type": "page",
        "title": page["title"],
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": new_body,
                "representation": "storage"
            }
        },
        "version": {"number": version}
    }

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
    response = requests.put(url, auth=AUTH, headers=HEADERS, json=payload)
    response.raise_for_status()

    page_url = f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={page_id}"
    print(f"✅ Page '{page['title']}' updated successfully.")
    print(f"🔗 Confluence page: {page_url}")

def create_page(title, body):
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": body,
                "representation": "storage"
            }
        }
    }

    if CONFLUENCE_PARENT_PAGE_ID:
        payload["ancestors"] = [{"id": CONFLUENCE_PARENT_PAGE_ID}]

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/"
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=payload)
    response.raise_for_status()

    new_page = response.json()
    page_url = f"{CONFLUENCE_BASE_URL}/pages/viewpage.action?pageId={new_page['id']}"

    print(f"✅ Page '{title}' created successfully.")
    print(f"🔗 Confluence page: {page_url}")

# ========== MAIN EXECUTION ==========

def main():
    try:
        new_tag, old_tag = get_latest_and_previous_tags()
        print(f"🔍 Comparing commits between tags: {old_tag} → {new_tag}")

        commits = get_commits_between_tags(new_tag, old_tag)
        if not commits:
            print("⚠️ No commits found between tags.")
            return

        title, html = build_html_body(commits)
        existing_page = find_page_by_title(title)

        if existing_page:
            print(f"🔄 Page '{title}' found — updating...")
            update_page(existing_page, html)
        else:
            print(f"🆕 Page '{title}' not found — creating...")
            create_page(title, html)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
