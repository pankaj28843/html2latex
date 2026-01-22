# GitHub Hardening Plan (Step 0.3)

Date: 2026-01-21
Scope: repository settings, branch protections, merge policy

## Merge policy (single draft PR, squash by default)
Use `gh repo edit` flags to enforce merge methods:

```bash
# Enable squash merges; disable merge commits and rebase merges
gh repo edit pankaj28843/html2latex \
  --enable-squash-merge \
  --enable-merge-commit=false \
  --enable-rebase-merge=false \
  --delete-branch-on-merge
```

## Branch protection / ruleset
Preferred (modern) approach: create a ruleset that targets `main` and enforces:
- Required status checks: CI workflow jobs (test matrix, latex-validity, e2e)
- Require PRs, prohibit direct pushes
- Require linear history (optional, if rebase/merge commits disabled)
- Require signed commits (optional)

Example (API-based) approach:
```bash
# Example only; adjust JSON for required checks once known.
# Use gh api to POST to /repos/{owner}/{repo}/rulesets
```

Fallback (branch protection API) approach:
```bash
# Example placeholders: adjust required_status_checks contexts.
gh api -X PUT \
  repos/pankaj28843/html2latex/branches/main/protection \
  -F required_status_checks.strict=true \
  -F required_pull_request_reviews.dismiss_stale_reviews=true \
  -F required_pull_request_reviews.required_approving_review_count=1 \
  -F enforce_admins=true \
  -F required_linear_history=true \
  -F allow_force_pushes=false \
  -F allow_deletions=false
```

## Security features
```bash
gh repo edit pankaj28843/html2latex --enable-secret-scanning
# Push protection requires secret scanning to be enabled first
gh repo edit pankaj28843/html2latex --enable-secret-scanning-push-protection
```

## Repository hygiene
- Ensure Issues enabled, Discussions optional.
- Consider CODEOWNERS in `.github/CODEOWNERS` for PR routing.
- Dependabot config in `.github/dependabot.yml` (weekly updates).

## Validation
- Confirm merge options in repo settings.
- Confirm branch protection/ruleset exists and required checks are listed.
- Confirm CI checks are required and passing for PR merge.
