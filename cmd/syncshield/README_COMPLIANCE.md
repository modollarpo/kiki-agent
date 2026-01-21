# SyncShield™ - Regulatory Guardrail Agent

## Overview

**SyncShield™** is KIKI's compliance and security agent, providing GDPR/CCPA-compliant audit logging, consent management, and ISO 27001 security controls. It serves as the regulatory guardrail for all KIKI operations.

## 🔒 Compliance Frameworks

### ✅ GDPR (General Data Protection Regulation)
- **Article 5**: Data retention policies
- **Article 7**: Consent management
- **Article 15-22**: Data subject rights (access, deletion, portability)
- **Article 30**: Records of processing activities
- **Article 33**: Personal data breach notification

### ✅ CCPA (California Consumer Privacy Act)
- **Right to Know**: Data access requests
- **Right to Delete**: Data deletion requests
- **Right to Opt-Out**: Do Not Sell tracking
- **Non-Discrimination**: Equal service guarantees

### ✅ ISO 27001 (Information Security Management)
- **A.9.2.1**: User access control logging
- **A.9.4.1**: Information access restriction
- **A.12.4.1**: Event logging
- **A.12.4.3**: Administrator logs
- **A.18.1.4**: Privacy and PII protection

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              SyncShield™ Agent                      │
│                                                     │
│  ┌──────────────┐    ┌─────────────────┐          │
│  │ Budget       │    │ GDPR Audit      │          │
│  │ Governor     │    │ Logger          │          │
│  └──────────────┘    └─────────────────┘          │
│         │                     │                     │
│         │                     ▼                     │
│         │            ┌─────────────────┐           │
│         │            │ Consent         │           │
│         │            │ Manager         │           │
│         │            └─────────────────┘           │
│         │                     │                     │
│         ▼                     ▼                     │
│  ┌──────────────────────────────────────┐          │
│  │   Compliance Validation Engine       │          │
│  │   - ISO 27001 Controls               │          │
│  │   - CCPA Requirements                │          │
│  │   - Data Subject Requests            │          │
│  └──────────────────────────────────────┘          │
│                     │                               │
│                     ▼                               │
│  ┌──────────────────────────────────────┐          │
│  │  Dual Audit Trail                    │          │
│  │  - CSV (structured, 7-year retention)│          │
│  │  - JSON (metadata, searchable)       │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
```

## 📊 Features

### 1. **GDPR-Compliant Audit Logging**
All events are logged with:
- **Timestamp**: RFC3339 format
- **Event ID**: SHA-256 hash-based unique identifier
- **Hashed PII**: Customer/User IDs hashed for privacy
- **Data Accessed**: List of PII fields touched
- **Retention Period**: 7 years for audit logs (legal requirement)
- **Dual Format**: CSV (parsing) + JSON (metadata)

### 2. **Consent Management**
Tracks user consent for:
- Marketing communications
- Analytics tracking
- Targeting/profiling
- Data sharing with third parties

**Consent Types:**
```go
ConsentMarketing   // Email, SMS campaigns
ConsentAnalytics   // Usage tracking
ConsentTargeting   // Personalized ads
ConsentProfiling   // AI-driven profiling
ConsentDataSharing // Third-party data sales
```

### 3. **Data Subject Rights (DSR)**
Handles GDPR/CCPA requests:
- **Right to Access**: Retrieve all customer data
- **Right to Deletion**: Permanent data erasure
- **Right to Portability**: Export data in machine-readable format
- **Right to Rectification**: Update incorrect data

### 4. **Budget Governance**
Sliding window budget enforcement:
- **MaxBurst Budget**: $500 per 60-second window
- **LTV Validation**: Reject bids > $10,000 or < $10
- **Fallback Mode**: Allows operations if Redis unavailable

### 5. **ISO 27001 Security Controls**
- User access logging (A.9.2.1)
- PII access validation (A.18.1.4)
- Administrator action tracking (A.12.4.3)
- Security event logging (A.12.4.1)

### 6. **CCPA Compliance**
- "Do Not Sell" opt-out tracking
- Data sale transaction logging
- Buyer/seller audit trail

## 🌐 API Endpoints

### Health Check
```bash
GET http://localhost:8081/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "SyncShield™ Regulatory Guardrail",
  "gdpr_compliant": true,
  "iso27001_active": true,
  "ccpa_compliant": true,
  "redis_connected": true,
  "timestamp": "2026-01-20T10:00:00Z"
}
```

### Bid Validation (Budget Check)
```bash
GET http://localhost:8081/check?ltv=150.00
```

**Response:**
- 200: Compliance check passed
- 403: Bid validation failed

### Record Spend
```bash
GET http://localhost:8081/spend?amount=10.00
```

### Grant Consent
```bash
POST http://localhost:8081/consent/grant?customer_id=cust_123&type=marketing
```

**Response:**
```json
{
  "status": "granted",
  "message": "Consent successfully recorded"
}
```

### Revoke Consent
```bash
POST http://localhost:8081/consent/revoke?customer_id=cust_123&type=marketing
```

### Check Consent Status
```bash
GET http://localhost:8081/consent/status?customer_id=cust_123
```

**Response:**
```json
{
  "marketing": {
    "customer_id": "e3b0c44298fc1c14",
    "consent_type": "marketing",
    "status": "GRANTED",
    "granted_at": "2026-01-20T10:00:00Z",
    "ip_address": "192.168.1.1",
    "version": "1.0",
    "legal_basis": "Consent"
  }
}
```

### Create Data Subject Request
```bash
POST http://localhost:8081/dsr/create?customer_id=cust_123&type=DELETION&requested_by=customer
```

**Response:**
```json
{
  "request_id": "DSR-1705752000-e3b0c442",
  "customer_id": "cust_123",
  "request_type": "DELETION",
  "status": "PENDING",
  "requested_at": "2026-01-20T10:00:00Z",
  "requested_by": "customer"
}
```

### Compliance Report
```bash
GET http://localhost:8081/compliance/report?period=monthly
```

**Response:**
```json
{
  "generated_at": "2026-01-20T10:00:00Z",
  "period": "monthly",
  "total_events": 1234,
  "security_events": 45,
  "consent_changes": 78,
  "data_deletions": 12,
  "data_access_requests": 34,
  "data_breaches": 0,
  "compliance_score": 95.5,
  "frameworks": ["GDPR", "CCPA", "ISO 27001"],
  "findings": [
    "All PII access logged and hashed",
    "Consent management operational",
    "Data retention policies enforced"
  ]
}
```

## 📁 Audit Log Format

### CSV Format (shield_audit_gdpr.csv)
```csv
timestamp,event_id,level,event_type,user_id_hash,customer_id_hash,action,resource,outcome,reason,ip_address,data_accessed,retention_days
2026-01-20T10:00:00Z,3f5a8b9c,INFO,bid_validation,,e3b0c442,validate_bid,ltv_prediction,APPROVED,Within safe parameters,,[customer_id predicted_ltv],2555
```

### JSON Format (shield_audit_gdpr.json)
```json
{
  "timestamp": "2026-01-20T10:00:00Z",
  "event_id": "3f5a8b9c",
  "level": "INFO",
  "event_type": "bid_validation",
  "customer_id": "e3b0c44298fc1c14",
  "action": "validate_bid",
  "resource": "ltv_prediction",
  "outcome": "APPROVED",
  "reason": "Within safe parameters",
  "data_accessed": ["customer_id", "predicted_ltv"],
  "retention_days": 2555,
  "metadata": {
    "ltv": 150.0
  }
}
```

## 🔐 Data Protection

### PII Hashing
All customer and user IDs are hashed using **SHA-256** before logging:
```go
customerID := "cust_12345"
hashedID := "e3b0c44298fc1c14" // SHA-256 truncated to 16 bytes
```

### Encryption Standards
- **Data at Rest**: AES-256-GCM
- **Data in Transit**: TLS 1.3
- **Key Management**: AWS KMS / HashiCorp Vault
- **File Permissions**: 0600 (owner read/write only)

### Data Retention
| Data Type | Retention Period | Legal Basis |
|-----------|-----------------|-------------|
| Audit Logs | 7 years (2555 days) | Legal obligation |
| Customer Data | 3 years (1095 days) | Contract performance |
| Marketing Data | 2 years (730 days) | Consent |
| Session Logs | 90 days | Legitimate interest |

## 🚀 Running SyncShield

### Local Development
```bash
cd cmd/syncshield
go build -o syncshield.exe
./syncshield.exe
```

### Expected Output
```
🛡️ SyncShield™ - Regulatory Guardrail Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ GDPR-compliant audit logging enabled
✅ CCPA compliance framework active
✅ ISO 27001 security controls operational
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 SyncShield API starting on :8081
   Compliance: http://localhost:8081/check
   Health: http://localhost:8081/health
   Consent: http://localhost:8081/consent/*
   DSR: http://localhost:8081/dsr/*
```

## 🔗 Integration with KIKI Ecosystem

| Agent | Port | Integration |
|-------|------|-------------|
| SyncValue™ | 50051 | LTV predictions validated by SyncShield |
| SyncFlow™ | 8082 | Budget checks before bid placement |
| SyncEngage™ | 8083 | Consent validation for retention campaigns |
| SyncCreate™ | 5002 | GDPR compliance for creative assets |
| Dashboard | 8502 | Real-time compliance metrics |

## 📋 Compliance Checklist

### GDPR Compliance
- [x] Consent management (Article 7)
- [x] Data subject rights (Articles 15-22)
- [x] Audit trail (Article 30)
- [x] Data retention policies (Article 5)
- [x] PII hashing/anonymization
- [x] Right to erasure implementation
- [x] Data portability support
- [x] Breach notification logging

### CCPA Compliance
- [x] Do Not Sell opt-out tracking
- [x] Data access requests
- [x] Data deletion requests
- [x] Sale transaction logging
- [x] Non-discrimination enforcement

### ISO 27001 Compliance
- [x] Access control logging (A.9.2.1)
- [x] PII access validation (A.18.1.4)
- [x] Administrator tracking (A.12.4.3)
- [x] Event logging (A.12.4.1)
- [x] Encryption standards (A.10.1.1)

## 🎯 Future Enhancements

- [ ] Real-time breach detection with ML
- [ ] Automated GDPR Article 33 breach notification
- [ ] Multi-region data residency support
- [ ] Blockchain-based immutable audit trail
- [ ] Advanced PII detection with NER models
- [ ] Automated compliance report generation
- [ ] Integration with Data Loss Prevention (DLP) tools

## 📞 Support

For compliance or security inquiries:
- Email: compliance@kiki-agent.com
- Docs: `docs/SYNCSHIELD_COMPLIANCE.md`
- Audit Requests: dpo@kiki-agent.com
