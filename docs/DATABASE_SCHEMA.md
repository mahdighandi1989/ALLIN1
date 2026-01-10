# 🏦 Banking Operations - Comprehensive Database Schema
# طراحی دیتابیس جامع سیستم عملیات بانکی

## Based on Analysis of Excel Files:
- Backend_Database.xlsm (592 customers, facilities, guarantors, tasks, journal)
- PROPERTIES - IRAN.xlsx (265 properties)
- PROPERTIES - UAE.xlsx (56 properties)
- Securities List 2022-2026.xlsx (annual security records)

---

## 📊 ENTITY RELATIONSHIP DIAGRAM

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   CUSTOMERS     │◄──────│    BRANCHES     │       │   CATEGORIES    │
│   (مشتریان)     │       │   (شعبات)       │       │  (دسته‌بندی‌ها)  │
└────────┬────────┘       └─────────────────┘       └─────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER RELATED                                │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│ CustomerProfile │    Partners     │   Documents     │  Attachments    │
│   (پروفایل)     │    (شرکا)       │    (مدارک)      │   (پیوست‌ها)    │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FACILITIES & SECURITIES                         │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│   Facilities    │   Guarantors    │   Securities    │ SecurityRecords │
│   (تسهیلات)     │   (ضامنین)      │   (تضمینات)     │ (لیست سالانه)   │
└────────┬────────┴────────┬────────┴─────────────────┴─────────────────┘
         │                 │
         │ 1:N             │ 1:N
         ▼                 ▼
┌─────────────────┐ ┌─────────────────┐
│ FacilityDocs    │ │ GuarantorCheques│
│(مدارک تسهیلات)  │ │   (چک ضامنین)   │
└─────────────────┘ └─────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         PROPERTIES & TASKS                              │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│   Properties    │PropertyValuation│     Tasks       │    Journal      │
│    (املاک)      │  (ارزیابی ملک)  │   (وظایف)       │    (لاگ)        │
└────────┬────────┴─────────────────┴─────────────────┴─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│PropertyInsurance│
│  (بیمه ملک)     │
└─────────────────┘
```

---

## 📋 TABLE DEFINITIONS

### 1. CUSTOMERS (مشتریان)
```
Primary entity for all banking customers
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| account_no | VARCHAR(50) | شماره حساب (UNIQUE) |
| branch_id | FK → branches | شعبه |
| category_id | FK → categories | دسته‌بندی (Retail/Corporate) |
| customer_name | VARCHAR(255) | نام مشتری |
| customer_name_fa | VARCHAR(255) | نام فارسی |
| country | ENUM | کشور (UAE/IRAN) |
| status | ENUM | وضعیت (Active/Inactive/Blocked) |
| open_date | DATE | تاریخ افتتاح |
| rating | VARCHAR(10) | رتبه‌بندی (A/B/C/D) |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### 2. BRANCHES (شعبات)
```
Bank branches
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| branch_code | VARCHAR(10) | کد شعبه (1741, etc.) |
| branch_name | VARCHAR(100) | نام شعبه |
| city | VARCHAR(100) | شهر |
| country | VARCHAR(50) | کشور |

### 3. CATEGORIES (دسته‌بندی‌ها)
```
Customer categories - expandable
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| name | VARCHAR(100) | نام (Retail, Corporate, VIP, ...) |
| name_fa | VARCHAR(100) | نام فارسی |
| parent_id | FK → categories | دسته والد (برای زیرگروه‌ها) |
| description | TEXT | توضیحات |

### 4. CUSTOMER_PROFILES (پروفایل مشتری)
```
Detailed customer profile - one-to-one with customers
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| business_type | VARCHAR(255) | نوع کسب‌وکار |
| call_report | DATE | گزارش تماس |
| previous_files | TEXT | پرونده‌های قبلی |
| profile_completeness | INTEGER | درصد تکمیل |
| missing_fields | TEXT | فیلدهای ناقص |
| notes | TEXT | یادداشت‌ها |

### 5. DOCUMENTS (مدارک)
```
All customer documents - normalized
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| document_type | ENUM | نوع (TradeLicense/Passport/EmiratesID/Visa/Tenancy) |
| document_no | VARCHAR(100) | شماره مدرک |
| issue_date | DATE | تاریخ صدور |
| expiry_date | DATE | تاریخ انقضا |
| nationality | VARCHAR(100) | ملیت (برای پاسپورت) |
| address | TEXT | آدرس (برای اجاره‌نامه) |
| remarks | TEXT | توضیحات |
| file_path | VARCHAR(500) | مسیر فایل |
| is_golden | BOOLEAN | طلایی (امارات آی‌دی) |

### 6. PARTNERS (شرکا)
```
Customer partners - for corporate accounts
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| partner_name | VARCHAR(255) | نام شریک |
| nationality | VARCHAR(100) | ملیت |
| share_percent | DECIMAL(5,2) | درصد سهم |
| order_no | INTEGER | ترتیب |

### 7. FACILITIES (تسهیلات)
```
All facility types in one table
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| facility_type | ENUM | نوع (OD/Loan/LG/TR/LC_Sight/LC_Usance/ChqDisc/LoG) |
| facility_no | VARCHAR(100) | شماره تسهیلات |
| amount | DECIMAL(18,2) | مبلغ |
| currency | VARCHAR(10) | ارز |
| rate | DECIMAL(5,2) | نرخ سود |
| approval_date | DATE | تاریخ تصویب |
| expiry_date | DATE | تاریخ انقضا |
| maturity_date | DATE | تاریخ سررسید |
| installments | INTEGER | تعداد اقساط |
| margin | DECIMAL(5,2) | مارجین (برای LC) |
| status | ENUM | وضعیت (Active/Closed/Defaulted) |
| notices | TEXT | اخطارها |
| notes | TEXT | یادداشت‌ها |

### 8. GUARANTORS (ضامنین)
```
Guarantors linked to customers
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری (ضمانت‌شده) |
| facility_id | FK → facilities | تسهیلات (اختیاری) |
| guarantor_name | VARCHAR(255) | نام ضامن |
| guarantor_account | VARCHAR(50) | حساب ضامن |
| order_no | INTEGER | ترتیب |

### 9. GUARANTOR_CHEQUES (چک‌های ضامنین)
```
Cheques provided by guarantors
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| guarantor_id | FK → guarantors | ضامن |
| cheque_no | VARCHAR(50) | شماره چک |
| amount | DECIMAL(18,2) | مبلغ |
| currency | VARCHAR(10) | ارز |
| bank_name | VARCHAR(100) | بانک صادرکننده |
| cheque_date | DATE | تاریخ چک |
| status | ENUM | وضعیت (Pending/Cleared/Bounced) |

### 10. SECURITIES (تضمینات)
```
Securities and collaterals
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| security_type | ENUM | نوع (Underlien/Cheques/Collateral/FD) |
| amount_aed | DECIMAL(18,2) | مبلغ درهم |
| amount_usd | DECIMAL(18,2) | مبلغ دلار |
| amount_irr | DECIMAL(18,2) | مبلغ ریال |
| amount_other | DECIMAL(18,2) | سایر ارزها |
| other_currency | VARCHAR(10) | ارز دیگر |
| details | TEXT | جزئیات |

### 11. SECURITY_RECORDS (لیست اوراق بهادار سالانه)
```
Annual security records from Securities List files
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| year | INTEGER | سال |
| category | ENUM | دسته (Retail/Corporate) |
| entry_date | DATE | تاریخ ثبت |
| row_no | INTEGER | شماره ردیف |
| fd_info | TEXT | اطلاعات FD |
| guarantor_info | TEXT | اطلاعات ضامن |
| cheque_no | VARCHAR(50) | شماره چک |
| cheque_amount | DECIMAL(18,2) | مبلغ چک |
| cheque_bank | VARCHAR(100) | بانک چک |
| undertaking_127 | BOOLEAN | تعهد 127 |
| undertaking_128 | BOOLEAN | تعهد 128 |
| remarks | TEXT | توضیحات |

### 12. PROPERTIES (املاک)
```
Properties in Iran and UAE
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| location | ENUM | موقعیت (IRAN/UAE) |
| property_type | ENUM | نوع (Apartment/Villa/Land/Building/Shop/Office) |
| plate_no | VARCHAR(100) | شماره پلاک ثبتی (ایران) |
| deed_no | VARCHAR(100) | شماره سند (امارات) |
| mortgage_doc_no | VARCHAR(100) | شماره سند رهنی |
| city | VARCHAR(100) | شهر |
| zone | VARCHAR(100) | منطقه |
| address | TEXT | آدرس کامل |
| area_sqm | DECIMAL(10,2) | مساحت (متر مربع) |
| building_age | INTEGER | عمر ساختمان |
| owner_name | VARCHAR(255) | نام مالک |
| contact_no | VARCHAR(50) | شماره تماس |
| mortgage_amount_aed | DECIMAL(18,2) | مبلغ رهن (درهم) |
| mortgage_amount_irr | DECIMAL(18,2) | مبلغ رهن (ریال) |
| mortgage_date | DATE | تاریخ ترهین |
| mortgage_bank | VARCHAR(100) | بانک رهنی |
| infrastructure_check | BOOLEAN | بررسی زیرساخت (CNBC) |
| status | ENUM | وضعیت (Mortgaged/Released/Sold) |

### 13. PROPERTY_VALUATIONS (ارزیابی‌های ملک)
```
Property valuation history - yearly
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| property_id | FK → properties | ملک |
| valuation_year | INTEGER | سال ارزیابی |
| valuation_date | DATE | تاریخ ارزیابی |
| value | DECIMAL(18,2) | ارزش |
| currency | VARCHAR(10) | ارز |
| valuator | VARCHAR(255) | ارزیاب |
| notes | TEXT | یادداشت |

### 14. PROPERTY_INSURANCES (بیمه‌های ملک)
```
Property insurance records
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| property_id | FK → properties | ملک |
| policy_no | VARCHAR(100) | شماره بیمه‌نامه |
| issue_date | DATE | تاریخ صدور |
| expiry_date | DATE | تاریخ انقضا |
| coverage_amount | DECIMAL(18,2) | مبلغ پوشش |
| premium | DECIMAL(18,2) | حق بیمه |
| insurer | VARCHAR(255) | بیمه‌گر |

### 15. TASKS (وظایف/پیگیری‌ها)
```
Follow-up tasks and reminders
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| customer_id | FK → customers | مشتری |
| facility_id | FK → facilities | تسهیلات (اختیاری) |
| task_name | VARCHAR(500) | عنوان |
| description | TEXT | توضیحات |
| status | ENUM | وضعیت (Pending/InProgress/Completed/Cancelled) |
| priority | ENUM | اولویت (Low/Medium/High/Urgent) |
| follow_up_date | DATE | تاریخ پیگیری |
| completed_date | DATE | تاریخ تکمیل |
| assigned_to | VARCHAR(100) | ارجاع به |
| created_by | VARCHAR(100) | ایجادکننده |

### 16. JOURNAL (لاگ فعالیت‌ها)
```
Activity log and audit trail
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| timestamp | TIMESTAMP | زمان |
| action_type | VARCHAR(50) | نوع عمل |
| entity_type | VARCHAR(50) | نوع موجودیت |
| entity_id | UUID | شناسه موجودیت |
| account_no | VARCHAR(50) | شماره حساب |
| item | VARCHAR(255) | آیتم |
| status | VARCHAR(50) | وضعیت |
| priority | VARCHAR(50) | اولویت |
| notes | TEXT | یادداشت |
| source | VARCHAR(100) | منبع |
| user_name | VARCHAR(100) | کاربر |

### 17. ATTACHMENTS (پیوست‌ها)
```
File attachments for any entity
```
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| entity_type | VARCHAR(50) | نوع موجودیت (customer/facility/property) |
| entity_id | UUID | شناسه موجودیت |
| file_name | VARCHAR(255) | نام فایل |
| original_name | VARCHAR(255) | نام اصلی |
| file_path | VARCHAR(500) | مسیر فایل |
| file_size | INTEGER | حجم فایل |
| mime_type | VARCHAR(100) | نوع فایل |
| is_shared | BOOLEAN | مشترک |
| uploaded_by | VARCHAR(100) | آپلودکننده |
| notes | TEXT | یادداشت |

---

## 🔄 EXTENSIBILITY FEATURES

### Dynamic Categories
- Categories table with parent_id for hierarchical structure
- Can add subcategories without schema changes

### Custom Fields (Future)
```sql
CREATE TABLE custom_fields (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50),  -- customer, facility, property
    field_name VARCHAR(100),
    field_label VARCHAR(255),
    field_type VARCHAR(50),   -- text, number, date, select, boolean
    options JSONB,            -- for select type
    is_required BOOLEAN,
    display_order INTEGER
);

CREATE TABLE custom_field_values (
    id UUID PRIMARY KEY,
    custom_field_id UUID REFERENCES custom_fields,
    entity_id UUID,
    value TEXT
);
```

### Audit Trail
- All tables have created_at, updated_at
- Journal table for detailed activity log
- Soft delete support (is_deleted flag)

---

## 📈 DATA SUMMARY FROM EXCEL FILES

| Entity | Records | Source File |
|--------|---------|-------------|
| Customers | 592 | Backend_Database.xlsm |
| Facilities | 22 | Backend_Database.xlsm |
| Guarantors | 22 | Backend_Database.xlsm |
| Tasks | 25 | Backend_Database.xlsm |
| Journal | 389 | Backend_Database.xlsm |
| CustomerProfiles | 3 | Backend_Database.xlsm |
| Attachments | 3 | Backend_Database.xlsm |
| Properties Iran | 265 | PROPERTIES - IRAN.xlsx |
| Properties UAE | 56 | PROPERTIES - UAE.xlsx |
| Security Records | ~500+ | Securities List 2022-2026.xlsx |

**Total: ~1,900+ records**
