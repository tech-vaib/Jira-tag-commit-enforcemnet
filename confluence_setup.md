Prerequisites

Before this will work, make sure:

✅ Your project follows semver
 release tags (e.g., v1.2.3).

✅ You have a Confluence API token
.

✅ You store the following in your GitHub repo secrets:

CONFLUENCE_API_USER – usually your Atlassian email

CONFLUENCE_API_TOKEN – your Atlassian API token

CONFLUENCE_BASE_URL – e.g., https://yourcompany.atlassian.net/wiki

CONFLUENCE_SPACE_KEY – your Confluence space key (e.g., ENG)

CONFLUENCE_PARENT_PAGE_ID – optional, to organize under one parent page

# 🚀 Confluence Release Notifier

Automatically posts your release commits to Confluence when a GitHub release is published.

---

## ✅ What It Does

- Collects commits between latest two tags
- Formats them as a Confluence HTML page
- Auto-links JIRA ticket IDs (e.g., HIF-1234 → clickable)
- Creates or updates daily page (`YYYY-MM-DD`)
- Appends new release entries **on top**

---

## 📁 Folder Structure

.github/workflows/confluence-release.yml
scripts/post_to_confluence.py
requirements.txt


---

## 🔐 Required GitHub Secrets

| Name | Description |
|------|-------------|
| `CONFLUENCE_API_USER` | Your Atlassian username/email |
| `CONFLUENCE_API_TOKEN` | Your API token (create [here](https://id.atlassian.com/manage-profile/security/api-tokens)) |
| `CONFLUENCE_BASE_URL` | e.g. `https://yourcompany.atlassian.net/wiki` |
| `CONFLUENCE_SPACE_KEY` | e.g. `ENG` |
| `CONFLUENCE_PARENT_PAGE_ID` | *(Optional)* ID of parent page to nest under |

---

## 💡 Usage

1. Create a new release in GitHub.
2. GitHub Action runs, finds commits since last release.
3. Commits are posted to a Confluence page titled `YYYY-MM-DD`.
   - If page exists → prepend.
   - If not → create new.

---

## 🤝 Sharing Across Repos

Place this exact folder structure in each repo. The script identifies the page by **current date**, so all repos posting on the same day will append to the same page.

---

## 🛠️ Testing Locally

```bash
export CONFLUENCE_API_USER="your-email"
export CONFLUENCE_API_TOKEN="your-token"
export CONFLUENCE_BASE_URL="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="ENG"

python scripts/post_to_confluence.py

Notes

JIRA links are hardcoded to https://yourcompany.atlassian.net/browse/. Update if needed.

Only HIF-1234 style tickets will be auto-linked.