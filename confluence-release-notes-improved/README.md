# Improved GitHub → Confluence Release Notes Automation

This package creates/updates a daily Confluence page under a configured parent page when a Git tag is pushed.

Features:
- Page title: Daily Release Notes - YYYY-MM-DD
- Always create/update under configured CONFLUENCE_PARENT_PAGE_ID (required)
- Prepend new repo sections (newest first)
- Deduplicate JIRA keys across the page to avoid duplicates
- Auto-link JIRA keys if JIRA_BASE_URL is provided
- Adds a label (default 'release-notes') to the page for easy discovery

Setup:
1. Add these repository secrets (Settings → Secrets and variables → Actions):
   - CONFLUENCE_BASE_URL (e.g., https://yourcompany.atlassian.net/wiki)
   - CONFLUENCE_SPACE_KEY (e.g., ENG)
   - CONFLUENCE_PARENT_PAGE_ID (numeric ID where daily pages are created)
   - CONFLUENCE_USER_EMAIL
   - CONFLUENCE_API_TOKEN
   - JIRA_BASE_URL (e.g., https://yourcompany.atlassian.net)
   - CONFLUENCE_PAGE_LABEL (optional, default 'release-notes')

2. Add files to your repo:
   - .github/workflows/release-to-confluence.yml
   - scripts/publish_to_confluence.py

3. Tag and push:
   git tag v1.0.0
   git push origin v1.0.0

Notes:
- Uses Confluence Cloud REST API.
- Requires the Confluence user (CONFLUENCE_USER_EMAIL) to have permissions to create/edit pages under the parent page.
- The script deduplicates JIRA keys by checking existing page content; if you manually have duplicates, consider cleaning them up once.

License: MIT
