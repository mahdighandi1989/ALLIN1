# 🏦 Banking Operations - Comprehensive Database Schema
# طراحی دیتابیس جامع سیستم عملیات بانکی

## Based on Analysis of Excel Files:
- Backend_Database.xlsm (592 customers, facilities, guarantors, tasks, journal)
- PROPERTIES - IRAN.xlsx (265 properties)
- PROPERTIES - UAE.xlsx (56 properties)
- Securities List 2022-2026.xlsx (annual security records)

---

## 🔒 SECURITY CONSIDERATIONS

### Field-Level Security
- **Encrypted Fields**: All PII fields (SSN, passport, national_id, bank_account_no) encrypted at rest using AES-256
- **Masked Fields**: Phone numbers, emails partially masked in logs and non-admin views
- **Audit Trail**: All CUD operations logged with user_id, timestamp, old/new values
- **Data Classification**: 
  - 🔴 **Critical**: Financial amounts, account numbers, identification numbers
  - 🟡 **Sensitive**: Names, addresses, phone numbers, emails
  - 🟢 **Public**: Account types, statuses, created dates

### Access Control
- **Row-Level Security (RLS)**: Customers can only access their own records
- **Column-Level Security**: Sensitive fields restricted by user role
- **Database Roles**:
  - `banking_admin`: Full access to all tables
  - `banking_user`: Read/write access to assigned customers only
  - `banking_readonly`: Read-only access to non-sensitive data
  - `banking_audit`: Read-only access to audit logs

### Data Protection
- **Encryption at Rest**: Database files encrypted with TDE (Transparent Data Encryption)
- **Encryption in Transit**: All connections use TLS 1.3
- **Key Management**: Encryption keys rotated quarterly, stored in HSM
- **Data Masking**: Production data masked in non-production environments
- **Backup Security**: Encrypted backups with separate key storage

### Compliance & Auditing
- **Audit Logging**: All database operations logged to immutable audit table
- **Data Retention**: Customer data retained per regulatory requirements (7 years)
- **Right to be Forgotten**: Soft delete with anonymization after retention period
- **Compliance Standards**: SOX, PCI DSS Level 1, GDPR, UAE Data Protection Law

---

## 📊 ENTITY RELATIONSHIP DIAGRAM