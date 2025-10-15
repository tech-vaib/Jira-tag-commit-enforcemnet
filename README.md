# 🪝 Git Commit Message Enforcement (JIRA Format)

This repository enforces commit messages to include a valid **JIRA tag**, such as:

✅ `HIF-1234: Implement feature X`  
✅ `HIF-1234 Fix typo in docs`  
❌ `HIF1234`, `HIF_1234`, or missing tag

---

## 🚀 Local Setup (One-time per Developer)

1. Clone the repository and navigate into it:
   ```bash
   cd your-repo
   ```

2. Run the setup script:
   ```bash
   sh hooks/setup-githooks.sh
   ```

   or manually configure:
   ```bash
   git config core.hooksPath hooks
   ```

3. Test by making a commit:
   ```bash
   git commit -m "HIF-1234: added feature X"
   ```
   ✅ Passes  
   ```bash
   git commit -m "feature: added feature X"
   ```
   ❌ Fails with validation message

---

## 🧪 Continuous Integration (GitHub Actions)

This repo includes a CI workflow that validates **all PR commit messages** to ensure compliance even if a developer bypasses local hooks.

Located in: `.github/workflows/validate-commits.yml`

### ✅ Rules:
- All commits in the PR must start with `HIF-<number>` followed by a space or colon
- Validation **skipped** if PR is targeting the `main` branch
- Runs automatically on PR creation and updates

---

## 🧰 Supported Platforms
- macOS
- Linux
- Windows (via Git Bash / WSL)

---

## 🛠 Troubleshooting

**Hook not running locally?**
- Ensure `core.hooksPath` is set:
  ```bash
  git config core.hooksPath
  ```
  Should output `hooks`

**Permission denied?**
- Ensure scripts are executable:
  ```bash
  chmod +x hooks/commit-msg hooks/setup-githooks.sh
  ```

---

## 📄 License
MIT
