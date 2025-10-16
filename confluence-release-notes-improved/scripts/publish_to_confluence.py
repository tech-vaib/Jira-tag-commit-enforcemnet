#!/usr/bin/env python3
import os
import re
import subprocess
import requests
import urllib.parse
from datetime import datetime, timezone

# Environment
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")
CONFLUENCE_PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID")
CONFLUENCE_USER_EMAIL = os.getenv("CONFLUENCE_USER_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
PAGE_LABEL = os.getenv("CONFLUENCE_PAGE_LABEL", "release-notes")
REPO_NAME = os.getenv("GITHUB_REPOSITORY", "unknown-repo")
TAG = os.getenv("GITHUB_REF_NAME")

if not all([CONFLUENCE_BASE_URL, CONFLUENCE_SPACE_KEY, CONFLUENCE_PARENT_PAGE_ID, CONFLUENCE_USER_EMAIL, CONFLUENCE_API_TOKEN, TAG]):
    raise SystemExit("❌ Missing required environment variables.")

def run(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

# Determine commits
try:
    prev_tag = run("git for-each-ref --sort=-creatordate --format='%(refname:short)' refs/tags | sed -n '2p'")
    if prev_tag == "":
        prev_tag = None
except Exception:
    prev_tag = None

if not prev_tag:
    try:
        prev_tag = run("git describe --tags --abbrev=0 $(git rev-list --tags --skip=1 --max-count=1)")
    except Exception:
        prev_tag = None

commit_range = f"{prev_tag}..{TAG}" if prev_tag else TAG

try:
    commits_raw = run(f"git log {commit_range} --pretty=format:%s'||%an")
except Exception:
    commits_raw = ""

commits = []
if commits_raw:
    for line in commits_raw.splitlines():
        if "||" in line:
            subject, author = line.split("||", 1)
        else:
            subject, author = line, ""
        commits.append({"subject": subject.strip(), "author": author.strip()})

# JIRA pattern
jira_pattern = re.compile(r"\b([A-Z]+-\d+)\b")

# Get tags created today with their dates
today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
tags_today = []
try:
    tags_info = run("git for-each-ref --format='%(refname:short)||%(creatordate:short)' refs/tags")
    for t in tags_info.splitlines():
        tname, tdate = t.strip("'").split("||")
        if tdate == today_str:
            tags_today.append((tname, tdate))
except Exception:
    pass

# Page title
page_title = f"Daily Release Notes - {today_str}"

auth = (CONFLUENCE_USER_EMAIL, CONFLUENCE_API_TOKEN)
headers = {"Content-Type": "application/json"}

# Search existing page under parent
cql = f'title="{page_title}" AND space="{CONFLUENCE_SPACE_KEY}" AND ancestor={CONFLUENCE_PARENT_PAGE_ID}'
search_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/search"
params = {"cql": cql, "expand": "body.storage,version"}
resp = requests.get(search_url, params=params, auth=auth, headers=headers)
if resp.status_code != 200:
    raise SystemExit(f"❌ Failed to search page: {resp.status_code} {resp.text}")

results = resp.json().get("results", [])
existing_jira_keys = set()
existing_page_id = None
existing_body = ""
existing_version = None
if results:
    page = results[0]
    existing_page_id = page.get("id")
    existing_body = page.get("body", {}).get("storage", {}).get("value", "") or ""
    existing_version = page.get("version", {}).get("number", 1)
    existing_jira_keys.update(jira_pattern.findall(existing_body))

# Deduplicate commits
new_commits = []
seen_new_jiras = set()
for c in commits:
    subj = c["subject"]
    keys = jira_pattern.findall(subj)
    if keys:
        unseen = [k for k in keys if k not in existing_jira_keys and k not in seen_new_jiras]
        if not unseen:
            continue
        new_commits.append(c)
        for k in unseen:
            seen_new_jiras.add(k)
    else:
        new_commits.append(c)

if not new_commits and not tags_today:
    print("ℹ️ No new commits or tags to add. Exiting.")
    exit(0)

def linkify(text: str) -> str:
    if not JIRA_BASE_URL:
        return text
    return jira_pattern.sub(lambda m: f"<a href='{JIRA_BASE_URL}/browse/{m.group(1)}'>{m.group(1)}</a>", text)

# Section HTML with tags
gh_repo = REPO_NAME
gh_release_link = f"https://github.com/{urllib.parse.quote(gh_repo)}/releases/tag/{urllib.parse.quote(TAG)}"
section_header = f"{REPO_NAME} - {TAG} (<a href='{gh_release_link}'>view release</a>)"

# Build tag list HTML
tags_html = ""
if tags_today:
    tag_links = [f"<a href='https://github.com/{urllib.parse.quote(gh_repo)}/releases/tag/{urllib.parse.quote(t[0])}'>{t[0]}</a> — {t[1]}" for t in tags_today]
    tags_html = "<p><strong>Tags:</strong> " + ", ".join(tag_links) + "</p>"

items = []
for c in new_commits:
    s = linkify(c["subject"])
    a = c["author"]
    items.append(f"<li>{s} <em>({a})</em></li>" if a else f"<li>{s}</li>")

commit_list_html = "\n".join(items) if items else "<li>No commits found.</li>"
section_html = f"<div><h3>{section_header}</h3>{tags_html}<ul>{commit_list_html}</ul></div>"

# Prepend or create page under parent
if existing_body:
    new_body = section_html + "\n<hr/>\n" + existing_body
    new_version = (existing_version or 1) + 1
    payload = {
        "id": existing_page_id,
        "type": "page",
        "title": page_title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {"storage": {"value": new_body, "representation": "storage"}},
        "version": {"number": new_version}
    }
    update_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{existing_page_id}"
    update_resp = requests.put(update_url, json=payload, auth=auth, headers=headers)
    if update_resp.status_code not in (200, 201):
        raise SystemExit(f"❌ Failed to update page: {update_resp.status_code} {update_resp.text}")
    page_id = existing_page_id
else:
    payload = {
        "type": "page",
        "title": page_title,
        "ancestors": [{"id": int(CONFLUENCE_PARENT_PAGE_ID)}],
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {"storage": {"value": "<h2>" + page_title + "</h2>" + section_html, "representation": "storage"}}
    }
    create_resp = requests.post(f"{CONFLUENCE_BASE_URL}/rest/api/content", json=payload, auth=auth, headers=headers)
    if create_resp.status_code not in (200, 201):
        raise SystemExit(f"❌ Failed to create page: {create_resp.status_code} {create_resp.text}")
    page_id = create_resp.json().get("id")

# Add label
if PAGE_LABEL and page_id:
    labels_payload = [{"prefix": "global", "name": PAGE_LABEL}]
    lbl_resp = requests.post(f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/label", json=labels_payload, auth=auth, headers=headers)
    if lbl_resp.status_code not in (200, 204):
        print(f"⚠️ Warning: failed to add label to page: {lbl_resp.status_code} {lbl_resp.text}")
    else:
        print(f"✅ Added label '{PAGE_LABEL}' to page {page_id}")
