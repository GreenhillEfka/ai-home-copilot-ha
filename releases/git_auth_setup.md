# Git Authentication Setup Guide
**Status:** CRITICAL - Required for Production Deployment

## Current Issue
8 production-ready releases are tagged locally but cannot be pushed to GitHub:
- **Core Add-on:** v0.4.6, v0.4.7, v0.4.8, v0.4.9
- **HA Integration:** v0.4.3, v0.4.4, v0.4.5, v0.4.6

**Error:** `could not read Username for 'https://github.com': No such device or address`

## Solution Options

### Option 1: GitHub CLI Authentication (Recommended)
```bash
# Install GitHub CLI if not available
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Authenticate
gh auth login --web
gh auth setup-git
```

### Option 2: Personal Access Token
```bash
# Create token at: https://github.com/settings/personal-access-tokens/new
# Scopes needed: repo, workflow

# Configure git credentials
git config --global credential.helper store
echo "https://<USERNAME>:<TOKEN>@github.com" > ~/.git-credentials
```

### Option 3: SSH Key Setup
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "ai-home-copilot-deploy" -f ~/.ssh/copilot_deploy

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/copilot_deploy

# Add public key to GitHub: https://github.com/settings/ssh/new
cat ~/.ssh/copilot_deploy.pub

# Update remotes to use SSH
cd /config/.openclaw/workspace/ha-copilot-repo
git remote set-url origin git@github.com:GreenhillEfka/Home-Assistant-Copilot.git

cd /config/.openclaw/workspace/ai_home_copilot_hacs_repo  
git remote set-url origin git@github.com:GreenhillEfka/ai-home-copilot-ha.git
```

## Post-Authentication Deployment
Once authentication is resolved, run:
```bash
# Automated deployment (10 minutes)
bash /config/.openclaw/workspace/releases/deployment_scripts.sh
```

## Verification
Test authentication:
```bash
cd /config/.openclaw/workspace/ha-copilot-repo
git push --dry-run origin main
git push --dry-run --tags origin
```

## Timeline
- **Authentication Setup:** 5-15 minutes (depending on method)
- **Deployment Execution:** 10 minutes (automated)
- **Total Time to Production:** 15-25 minutes

## Impact
Once resolved, all 8 releases deploy immediately with complete documentation, enabling:
- Public availability on HACS and Home Assistant Add-on Store
- Community adoption with production-ready Quick Start Guide
- API v1 availability for third-party integrations
- Health scoring and dashboard capabilities for end users