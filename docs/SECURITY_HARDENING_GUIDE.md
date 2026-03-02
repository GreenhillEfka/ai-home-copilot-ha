# Security Hardening Guide — PilotSuite Styx Core

**Version:** 1.0  
**Last Updated:** 2026-03-02  
**Based on:** OWASP Top 10 2021 Audit

---

## Quick Start

This guide provides step-by-step instructions to harden your PilotSuite Styx Core deployment based on the OWASP security audit findings.

### Priority Levels
- 🔴 **CRITICAL** — Fix immediately (within 24 hours)
- 🟠 **HIGH** — Fix within 2 weeks
- 🟡 **MEDIUM** — Fix within 1 month
- 🟢 **LOW** — Fix within 3 months

---

## Table of Contents

1. [Environment Configuration](#1-environment-configuration)
2. [Access Control Hardening](#2-access-control-hardening)
3. [Injection Prevention](#3-injection-prevention)
4. [SSRF Protection](#4-ssrf-protection)
5. [Authentication Strengthening](#5-authentication-strengthening)
6. [Security Headers](#6-security-headers)
7. [Logging & Monitoring](#7-logging--monitoring)
8. [Dependency Management](#8-dependency-management)
9. [Deployment Checklist](#9-deployment-checklist)

---

## 1. Environment Configuration 🟠

### 1.1 Set Security Environment Variables

Create or update your `.env` file:

```bash
# Security Configuration
COPILOT_AUTH_REQUIRED=true
COPILOT_AUTH_TOKEN=<generate-secure-token>
COPILOT_TOKEN_EXPIRATION_HOURS=24

# Rate Limiting
COPILOT_RATE_LIMIT_DEFAULT=100
COPILOT_RATE_LIMIT_AUTH=10  # Stricter for auth endpoints
COPILOT_RATE_LIMIT_ADMIN=50

# Request Limits
COPILOT_MAX_REQUEST_SIZE=1048576  # 1MB
COPILOT_SECURITY_HEADERS=true
COPILOT_REQUEST_LOGGING=true

# Injection Protection
COPILOT_INJECTION_CHECKS=true

# SSRF Protection
COPILOT_SSRF_PROTECTION=true
COPILOT_SSRF_ALLOWED_DOMAINS=api.example.com,webhooks.trusted.com

# CORS Configuration
COPILOT_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# HSTS (1 year)
COPILOT_HSTS_MAX_AGE=31536000

# Production Mode
FLASK_ENV=production
DEBUG=false
```

### 1.2 Generate Secure Auth Token

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**⚠️ Important:** Store this token securely! It won't be shown again.

### 1.3 Configure Token Rotation

Set up automatic token rotation (recommended: every 24 hours):

```bash
# Add to crontab
0 2 * * * /path/to/pilotsuite/scripts/rotate_token.sh
```

Example rotation script:
```bash
#!/bin/bash
# scripts/rotate_token.sh

NEW_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "export COPILOT_AUTH_TOKEN=$NEW_TOKEN" >> /path/to/.env

# Restart service
systemctl restart pilotsuite-styx-core
```

---

## 2. Access Control Hardening 🟠

### 2.1 Enable OWASP Middleware

Update your Flask app initialization:

```python
# copilot_core/rootfs/usr/src/app/main.py
from copilot_core.security.owasp_middleware import init_owasp_middleware

def create_app():
    app = Flask(__name__)
    
    # Initialize OWASP security middleware
    init_owasp_middleware(app)
    
    # ... rest of initialization
    
    return app
```

### 2.2 Implement Role-Based Access Control

Add role requirements to sensitive endpoints:

```python
from copilot_core.security.owasp_middleware import require_role

@bp.get("/admin/users")
@require_role("admin")
def list_users():
    """List all users (admin only)."""
    ...

@bp.post("/api/data")
@require_role("user")
def create_data():
    """Create data (authenticated users)."""
    ...

@bp.get("/api/public/info")
@require_role("guest")  # Anyone can access
def get_public_info():
    """Get public information."""
    ...
```

### 2.3 Configure CORS

Update CORS allowed origins in your environment:

```bash
COPILOT_CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**⚠️ Never use `*` in production!** Always specify exact origins.

### 2.4 Add Resource Ownership Validation

For endpoints that access specific resources:

```python
@bp.get("/api/v1/users/<user_id>/data")
@require_role("user")
def get_user_data(user_id):
    """Get user data with ownership check."""
    current_user = g.user_id  # Set by auth middleware
    
    # Verify ownership
    if current_user != user_id and not g.is_admin:
        return jsonify({
            "ok": False,
            "error": "access_denied",
            "message": "You can only access your own data"
        }), 403
    
    # ... proceed with request
```

---

## 3. Injection Prevention 🔴

### 3.1 Enable Input Validation Decorator

Apply to all endpoints that accept user input:

```python
from copilot_core.security.input_validator import validate_input

@bp.post("/api/v1/users")
@validate_input(checks=["sql", "xss", "path", "length"])
def create_user(data):
    """Create user with input validation."""
    # Use sanitized data from Flask g object
    safe_data = g.sanitized_data
    ...
```

### 3.2 Audit Database Queries

**CRITICAL:** Find and fix all SQL injection vulnerabilities.

#### Step 1: Find potentially vulnerable queries

```bash
# Search for string concatenation in SQL
grep -r "execute.*%" copilot_core/ --include="*.py"
grep -r "f\"SELECT" copilot_core/ --include="*.py"
grep -r "f\"INSERT" copilot_core/ --include="*.py"
grep -r "f\"UPDATE" copilot_core/ --include="*.py"
grep -r "f\"DELETE" copilot_core/ --include="*.py"
```

#### Step 2: Fix with parameterized queries

❌ **Vulnerable:**
```python
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

✅ **Secure:**
```python
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
```

### 3.3 Add NoSQL Injection Protection

If using MongoDB or similar:

```python
from copilot_core.security.owasp_middleware import check_injection

@bp.post("/api/v1/search")
def search():
    data = request.get_json()
    
    # Check for NoSQL injection
    query = data.get("query", "")
    safe, inj_type, pattern = check_injection(query)
    
    if not safe:
        return jsonify({
            "ok": False,
            "error": "injection_detected",
            "message": f"Potentially dangerous {inj_type} pattern"
        }), 400
    
    # ... proceed with search
```

### 3.4 Audit Command Execution

Find and review all `subprocess`, `os.system`, `eval()` calls:

```bash
grep -r "subprocess\." copilot_core/ --include="*.py"
grep -r "os\.system" copilot_core/ --include="*.py"
grep -r "eval(" copilot_core/ --include="*.py"
grep -r "exec(" copilot_core/ --include="*.py"
```

**Never pass user input directly to command execution!**

---

## 4. SSRF Protection 🟠

### 4.1 Enable SSRF Protection

The OWASP middleware includes SSRF protection by default. Configure allowed domains:

```bash
COPILOT_SSRF_PROTECTION=true
COPILOT_SSRF_ALLOWED_DOMAINS=api.example.com,webhooks.trusted.com,*.trusted.com
```

### 4.2 Validate User-Provided URLs

For endpoints accepting URLs:

```python
from copilot_core.security.owasp_middleware import validate_url

@bp.post("/api/v1/webhooks")
def create_webhook():
    data = request.get_json()
    webhook_url = data.get("url")
    
    # Validate URL
    valid, error = validate_url(webhook_url)
    if not valid:
        return jsonify({
            "ok": False,
            "error": "invalid_url",
            "message": error
        }), 400
    
    # ... proceed with webhook creation
```

### 4.3 Block Internal IP Ranges

The middleware automatically blocks:
- 10.0.0.0/8
- 172.16.0.0/12
- 192.168.0.0/16
- 127.0.0.0/8
- 169.254.0.0/16 (link-local)
- AWS metadata: 169.254.169.254

---

## 5. Authentication Strengthening 🟡

### 5.1 Implement Rate Limiting for Auth Endpoints

```python
from copilot_core.security.rate_limiter import get_rate_limiter

# In app initialization
limiter = get_rate_limiter()
limiter.set_endpoint_limit("/api/v1/auth/login", 10)  # 10 requests/minute
limiter.set_endpoint_limit("/api/v1/auth/register", 5)  # 5 requests/minute
```

### 5.2 Add Account Lockout

Implement account lockout after failed attempts:

```python
from collections import defaultdict
import time

_failed_attempts = defaultdict(list)

def check_account_lockout(username):
    """Check if account is locked due to failed attempts."""
    now = time.time()
    window = 300  # 5 minutes
    
    # Clean old attempts
    _failed_attempts[username] = [
        t for t in _failed_attempts[username]
        if now - t < window
    ]
    
    # Check if locked
    if len(_failed_attempts[username]) >= 5:
        return True, "Account locked. Try again in 5 minutes."
    
    return False, None

def record_failed_attempt(username):
    """Record failed login attempt."""
    _failed_attempts[username].append(time.time())
```

### 5.3 Plan for Multi-Factor Authentication (MFA)

**Roadmap:** Implement TOTP-based MFA

```python
# Future implementation (not yet available)
from copilot_core.security.mfa import require_mfa

@bp.post("/api/v1/auth/login")
def login():
    # ... validate credentials
    
    if user.mfa_enabled:
        return jsonify({
            "ok": True,
            "mfa_required": True,
            "message": "MFA code required"
        }), 200
```

---

## 6. Security Headers 🟡

### 6.1 Configure Reverse Proxy (Nginx Example)

If using Nginx as reverse proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Embedder-Policy "require-corp" always;
    add_header Cross-Origin-Resource-Policy "same-origin" always;
    
    # Hide server version
    server_tokens off;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.2 Force HTTPS Redirect

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect all HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}
```

---

## 7. Logging & Monitoring 🟢

### 7.1 Configure Security Logging

The OWASP middleware automatically logs:
- Injection attempts
- SSRF attempts
- Access control violations
- Rate limit exceeded events

Logs are written to the application log. For production, configure centralized logging.

### 7.2 Set Up Log Aggregation (Optional)

For production deployments, consider:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Graylog
- Datadog

Example Logstash configuration:
```conf
input {
  file {
    path => "/var/log/pilotsuite/*.log"
    start_position => "beginning"
  }
}

filter {
  grok {
    match => { "message" => "%{LOGLEVEL:level}: %{GREEDYDATA:log_message}" }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "pilotsuite-security-%{+YYYY.MM.dd}"
  }
}
```

### 7.3 Set Up Alerts

Configure alerts for:
- More than 10 injection attempts in 5 minutes
- Any SSRF attempt
- More than 50 failed login attempts from same IP
- Rate limit exceeded for admin endpoints

---

## 8. Dependency Management 🟢

### 8.1 Pin All Dependencies

Create `requirements.txt` with pinned versions:

```bash
# Generate from current environment
pip freeze > requirements.txt

# Or manually pin:
Flask==2.3.3
requests==2.31.0
# ... etc
```

### 8.2 Set Up Automated Scanning

#### Option A: GitHub Dependabot

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
  
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

#### Option B: Manual Security Scanning

```bash
# Install safety
pip install safety

# Check for vulnerabilities
safety check -r requirements.txt

# Or use pip-audit
pip install pip-audit
pip-audit -r requirements.txt
```

### 8.3 Monthly Dependency Review

Add to your maintenance checklist:
```bash
# Check for outdated packages
pip list --outdated

# Check for security vulnerabilities
safety check

# Update packages (review changes first!)
pip install --upgrade -r requirements.txt
```

---

## 9. Deployment Checklist 🟠

### Pre-Deployment Security Checklist

#### Environment Configuration
- [ ] `DEBUG=false` in production
- [ ] `FLASK_ENV=production`
- [ ] Secure auth token generated and stored
- [ ] Token expiration configured (24 hours)
- [ ] Rate limits configured

#### Access Control
- [ ] OWASP middleware initialized
- [ ] CORS origins configured (no `*`)
- [ ] Role requirements added to sensitive endpoints
- [ ] Resource ownership validation implemented

#### Injection Prevention
- [ ] All endpoints use `@validate_input` decorator
- [ ] All SQL queries use parameterized statements
- [ ] No `eval()` or `exec()` with user input
- [ ] NoSQL injection protection enabled

#### SSRF Protection
- [ ] SSRF protection enabled
- [ ] Allowed domains configured
- [ ] All user-provided URLs validated

#### Authentication
- [ ] Auth endpoints have stricter rate limits (10 req/min)
- [ ] Account lockout implemented
- [ ] Token rotation scheduled

#### Security Headers
- [ ] HTTPS enforced (reverse proxy)
- [ ] HSTS header configured
- [ ] CSP header configured
- [ ] All security headers present

#### Logging
- [ ] Security logging enabled
- [ ] Log retention policy configured (90+ days)
- [ ] Alert thresholds defined

#### Dependencies
- [ ] All dependencies pinned
- [ ] No known vulnerabilities (run `safety check`)
- [ ] Dependabot or similar configured

### Post-Deployment Verification

Run the security test suite:

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core
pytest tests/security/test_owasp.py -v
```

Expected output: All tests pass ✅

### Ongoing Maintenance

- **Daily:** Review security logs for anomalies
- **Weekly:** Check for new dependency vulnerabilities
- **Monthly:** Review and rotate auth tokens
- **Quarterly:** Full security audit (use `OWASP_SECURITY_AUDIT.md`)

---

## Appendix A: Quick Reference

### Environment Variables Summary

```bash
# Authentication
COPILOT_AUTH_REQUIRED=true
COPILOT_AUTH_TOKEN=<secure-token>
COPILOT_TOKEN_EXPIRATION_HOURS=24

# Rate Limiting
COPILOT_RATE_LIMIT_DEFAULT=100
COPILOT_RATE_LIMIT_AUTH=10

# Request Limits
COPILOT_MAX_REQUEST_SIZE=1048576

# Security Features
COPILOT_SECURITY_HEADERS=true
COPILOT_REQUEST_LOGGING=true
COPILOT_INJECTION_CHECKS=true
COPILOT_SSRF_PROTECTION=true

# CORS
COPILOT_CORS_ORIGINS=https://yourdomain.com

# SSRF
COPILOT_SSRF_ALLOWED_DOMAINS=api.example.com

# HSTS
COPILOT_HSTS_MAX_AGE=31536000

# Production
FLASK_ENV=production
DEBUG=false
```

### Test Commands

```bash
# Run all security tests
pytest tests/security/test_owasp.py -v

# Run specific test category
pytest tests/security/test_owasp.py::TestA03Injection -v
pytest tests/security/test_owasp.py::TestA10SSRF -v

# Check dependencies
safety check -r requirements.txt
```

---

## Appendix B: Troubleshooting

### Issue: CORS errors in browser

**Solution:** Check `COPILOT_CORS_ORIGINS` includes your frontend domain exactly (including protocol).

### Issue: False positive injection detection

**Solution:** Some legitimate inputs may trigger detection. Review the pattern and adjust if needed, or whitelist specific safe patterns.

### Issue: SSRF blocking legitimate internal services

**Solution:** Add internal service domains to `COPILOT_SSRF_ALLOWED_DOMAINS` with explicit domain names (not IPs).

### Issue: Rate limiting too aggressive

**Solution:** Adjust `COPILOT_RATE_LIMIT_DEFAULT` or set endpoint-specific limits.

---

## Appendix C: References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)

---

**Document Owner:** Security Team  
**Next Review:** 2026-06-02  
**Distribution:** Development Team, DevOps, Management
