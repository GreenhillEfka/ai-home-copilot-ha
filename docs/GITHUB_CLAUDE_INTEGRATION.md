# Claude CLI Integration für AI Home CoPilot

## Überblick

Dieses Dokument beschreibt die Claude CLI Integration für GitHub und kontinuierliche Code-Reviews.

---

## GitHub Authentication

### Automatische Authentifizierung

```bash
# GitHub CLI ist bereits konfiguriert
gh auth status
```

### Repository Access

```bash
# Repositories
export REPO_HA="GreenhillEfka/ai-home-copilot-ha"
export REPO_CORE="GreenhillEfka/ai-home-copilot-addon"

# Clonen (falls nicht vorhanden)
gh repo clone "$REPO_HA" /config/.openclaw/workspace/ai_home_copilot_hacs_repo
gh repo clone "$REPO_CORE" /config/.openclaw/workspace/ha-copilot-repo
```

---

## Claude CLI Commands

### Code Review

```bash
# Review neueste Änderungen
cd /config/.openclaw/workspace/ai_home_copilot_hacs_repo
claude -p "Review the latest changes in this HA Integration. Check for:
- Code quality issues
- Security vulnerabilities
- Architecture consistency
- Test coverage
- Documentation

Report your findings."

# Review Core Add-on
cd /config/.openclaw/workspace/ha-copilot-repo  
claude -p "Review the latest changes in this Core Add-on. Check for:
- Neuron implementation
- API design
- Brain Graph integration
- Test coverage

Report your findings."
```

### Pull Request Review

```bash
# Review offener PRs
gh pr list --repo "$REPO_HA" --state open
gh pr view <PR-NUMBER> --repo "$REPO_HA" --web  # Im Browser öffnen

# Claude Review für PR
claude -p "Review this PR: $(gh pr view <PR-NUMBER> --repo "$REPO_HA" --json title,body -q '.title + \"\\n\" + .body')"
```

### Issue Tracking

```bash
# Offene Issues anzeigen
gh issue list --repo "$REPO_HA" --state open
gh issue list --repo "$REPO_CORE" --state open

# Neues Issue erstellen
gh issue create --repo "$REPO_HA" --title "Bug: ..." --body "..."
```

---

## Automatisierte Workflows

### Daily Review Script

```bash
#!/bin/bash
# daily_review.sh - Tägliche Code-Review Routine

REPOS=(
    "/config/.openclaw/workspace/ai_home_copilot_hacs_repo"
    "/config/.openclaw/workspace/ha-copilot-repo"
)

for repo in "${REPOS[@]}"; do
    echo "=== Reviewing $(basename $repo) ==="
    cd "$repo"
    
    # Neueste Commits
    echo "Latest commits:"
    git log --oneline -5
    
    # Offene Changes
    echo -e "\nUncommitted changes:"
    git status --short
    
    # Claude Review
    claude -p "Quick review of $(basename $repo). Any critical issues?"
done
```

### Continuous Integration

```bash
#!/bin/bash
# ci_check.sh - CI/CD Prüfung

# Tests ausführen
cd /config/.openclaw/workspace/ai_home_copilot_hacs_repo
pytest custom_components/ai_home_copilot/tests/ -v

# Claude Verification
claude -p "Verify the test results. Are all tests passing? Any concerns?"
```

---

## Repository-Struktur

```
ai_home_copilot_hacs_repo/
├── custom_components/
│   └── ai_home_copilot/
│       ├── __init__.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── entities/
│       ├── core/
│       │   └── modules/
│       └── services/
├── tests/
├── docs/
├── CHANGELOG.md
└── README.md

ha-copilot-repo/
├── copilot/
│   ├── api/
│   ├── brain_graph/
│   ├── neurons/
│   └── config.py
├── tests/
├── addon/
├── docs/
├── CHANGELOG.md
└── README.md
```

---

## Best Practices

### Code Review Checklist

- [ ] Alle Tests bestanden
- [ ] Typ-Hints vorhanden
- [ ] Docstrings vollständig
- [ ] Keine hardcoded Secrets
- [ ] Architecture eingehalten
- [ ] CHANGELOG aktualisiert
- [ ] README/Docs aktualisiert

### Commit Messages

```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: Neue Feature
- `fix`: Bug Fix
- `docs`: Dokumentation
- `refactor`: Code-Umstrukturierung
- `test`: Tests hinzugefügt
- `chore`: Wartungsarbeiten

---

## Troubleshooting

### GitHub Authentication

```bash
# Auth Status
gh auth status

# Login
gh auth login

# Token setzen
export GH_TOKEN="ghp_..."
```

### Claude CLI Issues

```bash
# Version prüfen
claude --version

# Help
claude --help

# Logs prüfen
tail -f ~/.config/claude/logs/
```

---

## Nützliche Aliase

```bash
# In ~/.bashrc oder ~/.zshrc hinzufügen

alias ghstatus='gh repo view --json name,defaultBranchRef,updatedAt'
alias claude-review='claude -p "Review my code changes for quality and issues."'
alias git-log='git log --oneline -10'
alias sync-repos='./scripts/claude_orchestrate.sh sync'
```

---

*Letzte Aktualisierung: 2026-02-14*
