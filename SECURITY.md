# Security Policy and Guidelines
## Apollo GovCon Suite (sammySosa)

### 🚨 CRITICAL SECURITY ALERT

**This repository previously contained exposed secrets and credentials in version control. Immediate action has been taken to secure the codebase, but additional steps are required for full security.**

---

## Security Status

| Component | Status | Priority | Action Required |
|-----------|--------|----------|-----------------|
| Secrets Management | 🔴 CRITICAL | HIGH | Implement proper secrets management |
| Authentication | 🔴 MISSING | CRITICAL | Implement authentication system |
| Authorization | 🔴 MISSING | CRITICAL | Implement RBAC |
| Input Validation | 🔴 VULNERABLE | HIGH | Add comprehensive validation |
| Data Encryption | 🔴 MISSING | HIGH | Implement encryption at rest/transit |
| Audit Logging | 🔴 MISSING | MEDIUM | Add security event logging |

---

## Immediate Security Actions Required

### 1. Secrets Management (CRITICAL - Do This First)

#### Current Issues
- ❌ Real API keys were committed to version control
- ❌ Database passwords hardcoded in multiple files
- ❌ Slack webhook URLs exposed
- ❌ Personal information in repository

#### Immediate Actions
```bash
# 1. Remove the exposed secrets file (if still present)
rm .streamlit/secrets.toml

# 2. Copy the template and configure with new secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# 3. Generate new API keys
# - SAM.gov: https://sam.gov/data-services
# - Slack: Regenerate webhook URL in Slack app settings

# 4. Update database password
# - Change password in PostgreSQL
# - Update docker-compose.yml with new password
# - Update secrets.toml with new password
```

#### Revoke Compromised Credentials
1. **SAM.gov API Key**: `d57QFEQCIIdegq3Y2nndqD4iyruX5ktwEXSev7MG`
   - Log into SAM.gov account
   - Revoke this key immediately
   - Generate new API key
   
2. **Slack Webhook**: `https://hooks.slack.com/services/[REDACTED_WEBHOOK_URL]`
   - Go to Slack app settings
   - Delete the exposed webhook
   - Create new webhook URL

3. **Database Password**: `mysecretpassword`
   - Change PostgreSQL password
   - Update all configuration files

### 2. Git History Cleanup (CRITICAL)

The exposed secrets are in git history and must be removed:

```bash
# WARNING: This rewrites git history - backup your repository first
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch .streamlit/secrets.toml' \
--prune-empty --tag-name-filter cat -- --all

# Force push to update remote repository
git push origin --force --all
git push origin --force --tags
```

### 3. Environment Variable Configuration

For production deployments, use environment variables instead of files:

```bash
# Set environment variables (Linux/Mac)
export SAM_API_KEY="your_new_sam_api_key"
export SLACK_WEBHOOK_URL="your_new_slack_webhook"
export DB_PASSWORD="your_new_secure_password"

# Set environment variables (Windows)
set SAM_API_KEY=your_new_sam_api_key
set SLACK_WEBHOOK_URL=your_new_slack_webhook
set DB_PASSWORD=your_new_secure_password
```

---

## Security Architecture Requirements

### Authentication System (NOT IMPLEMENTED)

**Current State**: No authentication - anyone can access the system
**Required Implementation**:

```python
# Required authentication components
class AuthenticationService:
    def __init__(self):
        self.oauth_provider = "government_sso"
        self.mfa_required = True
        self.session_timeout = 1800  # 30 minutes
        
    def authenticate_user(self, credentials):
        # Multi-factor authentication
        # Government CAC/PIV card integration
        # Session management
        pass
        
    def validate_clearance_level(self, user, resource):
        # Security clearance validation
        # Need-to-know basis access
        pass
```

### Authorization System (NOT IMPLEMENTED)

**Required RBAC Implementation**:
- **Admin**: Full system access
- **Analyst**: Read/write access to opportunities and analysis
- **Viewer**: Read-only access to dashboards
- **Partner**: Limited access to partner portal only

### Input Validation (VULNERABLE)

**Current Issues**:
- No input sanitization
- SQL injection vulnerabilities
- XSS vulnerabilities

**Required Implementation**:
```python
from marshmallow import Schema, fields, validate

class OpportunitySearchSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(max=200))
    agency = fields.Str(validate=validate.Length(max=100))
    date_from = fields.Date()
    date_to = fields.Date()
    
def validate_search_input(data):
    schema = OpportunitySearchSchema()
    return schema.load(data)
```

### Data Encryption (NOT IMPLEMENTED)

**Requirements**:
- **At Rest**: AES-256 encryption for database
- **In Transit**: TLS 1.3 for all communications
- **Field-Level**: Encrypt PII and sensitive government data

---

## Compliance Requirements

### Government Contracting Compliance

This system handles government contracting data and must comply with:

1. **FISMA (Federal Information Security Management Act)**
   - Security categorization required
   - NIST SP 800-53 controls implementation
   - Continuous monitoring

2. **FedRAMP (Federal Risk and Authorization Management Program)**
   - Cloud security assessment
   - Continuous monitoring
   - Incident response procedures

3. **NIST Cybersecurity Framework**
   - Identify, Protect, Detect, Respond, Recover

### Data Classification

Government contracting data must be classified and handled appropriately:

- **Public**: General opportunity information
- **Sensitive**: Company proprietary information
- **Controlled**: Government sensitive information
- **Classified**: Requires security clearance

---

## Security Testing Requirements

### Automated Security Testing

Implement these security tests in CI/CD pipeline:

```yaml
# .github/workflows/security.yml
name: Security Testing
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      # Static Application Security Testing (SAST)
      - name: Run Bandit Security Scan
        run: bandit -r . -f json -o bandit-report.json
        
      # Dependency Vulnerability Scanning
      - name: Run Safety Check
        run: safety check --json --output safety-report.json
        
      # Secret Scanning
      - name: Run TruffleHog
        run: trufflehog --regex --entropy=False .
```

### Manual Security Testing

Regular security assessments required:
- **Penetration Testing**: Quarterly
- **Code Review**: All changes
- **Vulnerability Assessment**: Monthly
- **Compliance Audit**: Annually

---

## Incident Response Plan

### Security Incident Classification

1. **Critical**: Data breach, system compromise
2. **High**: Unauthorized access attempt, service disruption
3. **Medium**: Security policy violation, suspicious activity
4. **Low**: Minor security configuration issue

### Response Procedures

1. **Immediate Response** (0-1 hours):
   - Isolate affected systems
   - Preserve evidence
   - Notify security team

2. **Investigation** (1-24 hours):
   - Assess scope and impact
   - Identify root cause
   - Document findings

3. **Recovery** (24-72 hours):
   - Implement fixes
   - Restore services
   - Verify security

4. **Post-Incident** (1-2 weeks):
   - Lessons learned review
   - Update security procedures
   - Compliance reporting

---

## Security Contacts

### Internal Security Team
- **Security Officer**: [Contact Information]
- **System Administrator**: [Contact Information]
- **Compliance Officer**: [Contact Information]

### External Resources
- **CISA**: https://www.cisa.gov/
- **NIST**: https://www.nist.gov/cybersecurity
- **FedRAMP**: https://www.fedramp.gov/

---

## Reporting Security Vulnerabilities

### How to Report

1. **Email**: security@company.com
2. **Encrypted Communication**: Use PGP key [Key ID]
3. **Anonymous Reporting**: [Secure reporting portal]

### What to Include

- Detailed description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested remediation (if known)

### Response Timeline

- **Acknowledgment**: Within 24 hours
- **Initial Assessment**: Within 72 hours
- **Resolution**: Based on severity (Critical: 7 days, High: 30 days)

---

## Security Training Requirements

All team members must complete:

1. **Security Awareness Training**: Annually
2. **Government Compliance Training**: Annually
3. **Incident Response Training**: Bi-annually
4. **Secure Coding Training**: For developers

---

## Security Metrics and Monitoring

### Key Security Metrics

- Authentication failure rate
- Unauthorized access attempts
- Vulnerability remediation time
- Security training completion rate
- Incident response time

### Monitoring Tools

- **SIEM**: Security Information and Event Management
- **IDS/IPS**: Intrusion Detection/Prevention System
- **Vulnerability Scanner**: Regular security assessments
- **Log Analysis**: Centralized security logging

---

**Document Version**: 1.0
**Last Updated**: [Current Date]
**Next Review**: [Date + 6 months]
**Owner**: Security Team
