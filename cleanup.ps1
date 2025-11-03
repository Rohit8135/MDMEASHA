# Ensure we're at repo root
Set-Location (git rev-parse --show-toplevel)

# 0) Abort if uncommitted changes exist
if (git status --porcelain) {
  Write-Error "Commit or stash changes before running this cleanup. Exiting."
  exit 1
}

# 1) Ensure .env is in .gitignore (create .gitignore if missing) and commit
if (-not (Test-Path .gitignore)) { New-Item -Path .gitignore -ItemType File -Force | Out-Null }
if (-not (Select-String -Path .gitignore -Pattern '^\.env$' -Quiet)) {
  Add-Content -Path .gitignore -Value '.env'
  git add .gitignore
  git commit -m "chore: add .env to .gitignore"
} else {
  Write-Host ".env already in .gitignore"
}

# 2) Stop tracking .env but keep local file
if (Test-Path .env) {
 try { git rm --cached .env -q 2>$null } catch { Write-Host "No .env tracked in Git (skipping)." }

git add -A
if (-not (git diff --cached --quiet)) {
  git commit -m "chore: stop tracking .env (keep local copy)"
} else {
  Write-Host "No change to commit for .env untracking."
}

# 3) Create a safety backup branch before history rewrite
git branch backup-main-before-secret-clean

# 4) Install git-filter-repo (required)
python -m pip install --upgrade git-filter-repo

# 5) Create a replacement file to redact common key patterns (Groq/OpenAI)
@'
# redact Groq and OpenAI key patterns
regex:gsk_[A-Za-z0-9_-]+==>[REDACTED-GROQ-KEY]
regex:sk-[A-Za-z0-9._-]+==>[REDACTED-OPENAI-KEY]
'@ > replacements.txt

# 6) Rewrite history: remove any .env blobs and apply replacements to wipe keys from all commits
#    --invert-paths --paths .env  => remove .env entirely from history
#    --replace-text replacements.txt => replace sensitive tokens in files/commit messages
git filter-repo --force --replace-text replacements.txt --invert-paths --paths .env

# 7) Remove the temporary replacements file
Remove-Item replacements.txt -Force

# 8) Verify .env no longer exists in history (no output expected)
if (git rev-list --all -- .env 2>$null) {
  Write-Error ".env still appears in history. Do not push. Investigate."
  exit 1
} else {
  Write-Host ".env removed from history (good)."
}

# 9) Double-check no Groq/OpenAI patterns remain in commits (should return nothing)
if (git log --all -S 'gsk_' --oneline) {
  Write-Error "Groq key pattern still found in history. Investigate."
  exit 1
} else {
  Write-Host "No Groq key pattern found in history."
}
if (git log --all -S 'sk-' --oneline) {
  Write-Error "OpenAI key pattern still found in history. Investigate."
  exit 1
} else {
  Write-Host "No OpenAI key pattern found in history."
}

# 10) Expire reflogs and aggressively garbage-collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 11) Force-push cleaned main to origin (this rewrites remote history)
#       Confirm with collaborators before running. This will replace remote main.
git checkout -B main
git push --force --set-upstream origin main
git push --force origin --tags

# 12) Final local checks: ensure .env is not tracked and remains local
if (Test-Path .env) {
  if (git ls-files --error-unmatch .env 2>$null) {
    Write-Error ".env is still tracked locally -- something went wrong."
  } else {
    Write-Host ".env is local and ignored (do not commit)."
  }
} else {
  Write-Host "No local .env found. Create one locally and keep it out of git."
}

# 13) (Optional) delete the local backup branch once you're fully confident
# git branch -D backup-main-before-secret-clean

# IMPORTANT: After push, rotate/revoke the exposed API keys at Groq/OpenAI providers immediately.