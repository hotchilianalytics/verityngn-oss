# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

**Note:** VerityNgn is currently in soft launch (v0.1.x alpha). Security updates will be released as needed.

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in VerityNgn, please report it responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security issues via:

1. **GitHub Security Advisories** (preferred):
   - Go to https://github.com/hotchilianalytics/verityngn-oss/security/advisories
   - Click "Report a vulnerability"
   - Provide details using the template below

2. **Email** (if GitHub Security Advisories unavailable):
   - Email: security@hotchilianalytics.com (replace with actual email)
   - Subject: [SECURITY] VerityNgn Vulnerability Report
   - Include the report template below

### Report Template

```
**Summary:**
Brief description of the vulnerability

**Type of Vulnerability:**
(e.g., credential exposure, injection, authentication bypass, etc.)

**Severity:**
Critical / High / Medium / Low

**Affected Components:**
List of affected files/modules

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. ...

**Proof of Concept:**
Code/commands demonstrating the vulnerability (if applicable)

**Impact:**
What can an attacker do with this vulnerability?

**Suggested Fix:**
(Optional) Your recommendation for fixing the issue

**Your Information:**
- Name (optional):
- Contact:
- Would you like to be credited in the fix announcement? (Yes/No)
```

### Response Timeline

- **Initial Response**: Within 48 hours
- **Triage & Assessment**: Within 7 days
- **Fix Development**: Varies by severity (1-30 days)
- **Public Disclosure**: After fix is released + 7 days

### What to Expect

1. **Acknowledgment**: We'll confirm receipt of your report
2. **Assessment**: We'll evaluate severity and impact
3. **Fix Development**: We'll work on a patch
4. **Disclosure**: We'll coordinate disclosure timing with you
5. **Credit**: We'll credit you (if desired) in release notes

---

## Security Best Practices

### For Users

#### 1. Protect Your Credentials

**DO:**
- Store service account keys in secure locations (e.g., `~/.config/gcp/`)
- Use environment variables or `.env` files (never commit to git)
- Rotate API keys regularly (every 90 days recommended)
- Use separate service accounts for dev/staging/production
- Enable Cloud Audit Logs for monitoring

**DON'T:**
- Commit credentials to git (check `.gitignore`)
- Share service account keys via email/Slack
- Use production credentials for development
- Store keys in public locations

#### 2. Secure Your Environment

**Local Development:**
```bash
# Use restrictive file permissions
chmod 600 .env
chmod 600 verityngn/config/*.json

# Check for exposed credentials before committing
git diff --cached | grep -E "(private_key|api_key|secret)"
```

**Docker:**
```bash
# Use secrets for credentials (not environment variables in Dockerfile)
docker secret create gcp_key verityngn/config/your-key.json
docker service create --secret gcp_key verityngn:latest

# Or use .env file mounting
docker run -v $(pwd)/.env:/app/.env verityngn:latest
```

**Cloud Run:**
```bash
# Use Secret Manager (not environment variables)
gcloud secrets create verityngn-gcp-key --data-file=your-key.json
gcloud run services update verityngn-api \
  --update-secrets=GOOGLE_APPLICATION_CREDENTIALS=verityngn-gcp-key:latest
```

#### 3. Network Security

- Use HTTPS for all API endpoints
- Implement rate limiting to prevent abuse
- Use authentication/API keys for production deployments
- Monitor for unusual activity (e.g., spike in API usage)

#### 4. Input Validation

- Only process public YouTube URLs
- Sanitize all user inputs
- Implement URL validation before processing
- Set processing timeouts to prevent DoS

### For Contributors

#### 1. Code Security

**Before Committing:**
```bash
# Check for exposed secrets
git diff --cached | grep -iE "(password|secret|key|token|api)"

# Verify .gitignore is working
git status --ignored

# Use pre-commit hooks (recommended)
# Create .git/hooks/pre-commit:
#!/bin/bash
if git diff --cached | grep -iE "(private_key|api_key|password)"; then
    echo "ERROR: Potential secret detected in commit!"
    exit 1
fi
```

**Secure Coding Practices:**
- Validate and sanitize all inputs
- Use parameterized queries (if database added)
- Avoid `eval()` or `exec()` on user input
- Use safe YAML/JSON parsing (no `yaml.unsafe_load`)
- Implement proper error handling (don't expose stack traces)

#### 2. Dependency Security

```bash
# Check for vulnerable dependencies
pip audit

# Or use safety
pip install safety
safety check

# Update dependencies regularly
pip list --outdated
```

#### 3. Code Review

All contributions must:
- Pass automated security checks
- Be reviewed by at least one maintainer
- Not introduce new credential exposure risks
- Follow secure coding guidelines

---

## Known Security Considerations

### 1. API Costs

**Risk:** Malicious users could trigger expensive API calls

**Mitigations:**
- Implement rate limiting (5 videos/hour per user recommended)
- Set Cloud billing budget alerts
- Use quota limits on Vertex AI API
- Monitor usage patterns

### 2. Credential Exposure

**Risk:** Service account keys have broad permissions

**Mitigations:**
- Use principle of least privilege (minimal IAM roles)
- Rotate keys every 90 days
- Use Workload Identity in Kubernetes
- Enable Cloud Audit Logs
- Never commit keys to git (.gitignore configured)

### 3. YouTube Video Content

**Risk:** Processing malicious video files

**Mitigations:**
- yt-dlp has built-in security features
- Videos processed in isolated environment
- No arbitrary code execution from video content
- Timeout limits on processing

### 4. LLM Output Parsing

**Risk:** Malformed LLM responses could cause parsing errors

**Mitigations:**
- Robust JSON parsing with error handling
- Validation of LLM output structure
- Fallback mechanisms for parsing failures
- Logging of all parsing errors

### 5. Web Search Results

**Risk:** Malicious websites in search results

**Mitigations:**
- Domain reputation checking
- HTTPS-only sources (where possible)
- Timeout on web requests (10s max)
- No execution of downloaded code
- Content sanitization before display

---

## Vulnerability Disclosure Policy

### Our Commitment

We are committed to:
- Responding to security reports within 48 hours
- Providing regular updates on fix progress
- Crediting researchers (if desired) in release notes
- Following coordinated disclosure practices
- Maintaining transparency with the community

### Scope

**In Scope:**
- Credential exposure in code or documentation
- Authentication/authorization bypass
- Injection vulnerabilities (SQL, command, etc.)
- Remote code execution
- Denial of service attacks
- Data leakage or privacy issues

**Out of Scope:**
- Social engineering attacks
- Physical attacks
- Issues in third-party dependencies (report upstream)
- Theoretical vulnerabilities without PoC
- Spam or content issues

### Safe Harbor

We will not pursue legal action against researchers who:
- Report vulnerabilities responsibly (private disclosure)
- Avoid accessing user data beyond what's necessary for PoC
- Do not perform DoS or destructive testing
- Follow this policy

---

## Security Updates

Security updates will be announced via:
- GitHub Security Advisories
- GitHub Releases (with `[SECURITY]` tag)
- README.md (for critical issues)

Subscribe to repository notifications to stay informed.

---

## Compliance

VerityNgn handles:
- Public YouTube videos (no personal data collection)
- User-provided configuration (stored locally)
- Generated reports (stored locally or in user's GCS bucket)

**We do NOT:**
- Collect user personal information
- Store user credentials on our servers
- Track user activity across sessions
- Share data with third parties

**Users are responsible for:**
- Securing their own credentials
- Complying with YouTube Terms of Service
- Respecting copyright and fair use
- GDPR/privacy compliance if deploying publicly

---

## Contact

For security issues:
- **Preferred**: GitHub Security Advisories
- **Alternative**: security@hotchilianalytics.com (if email exists, otherwise use GitHub Issues with SECURITY label)

For general questions:
- GitHub Discussions
- GitHub Issues (non-security)

---

**Last Updated:** October 23, 2025  
**Policy Version:** 1.0

