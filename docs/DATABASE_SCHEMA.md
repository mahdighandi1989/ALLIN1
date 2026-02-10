markdown
# 🏦 Banking Operations - Comprehensive Database Schema
# طراحی دیتابیس جامع سیستم عملیات بانکی

## Based on Analysis of Excel Files:
- Backend_Database.xlsm (592 customers, facilities, guarantors, tasks, journal)
- PROPERTIES - IRAN.xlsx (265 properties)
- PROPERTIES - UAE.xlsx (56 properties)
- Securities List 2022-2026.xlsx (annual security records)

---

## 📊 ENTITY RELATIONSHIP DIAGRAM

### Table: facilities
ستون‌های اصلی:
- id: INTEGER (PRIMARY KEY)
- customer_id: INTEGER (FOREIGN KEY به customers)
- amount: NUMERIC  -- این ستون برای ذخیره مبلغ تسهیلات است
- currency: VARCHAR
- facility_type: VARCHAR
- start_date: DATE
- end_date: DATE
- status: VARCHAR
- created_at: TIMESTAMP
- updated_at: TIMESTAMP

### Table: customers
- id: INTEGER (PRIMARY KEY)
- name: VARCHAR
- national_id: VARCHAR
- ...

### Table: guarantors
- id: INTEGER (PRIMARY KEY)
- facility_id: INTEGER (FOREIGN KEY به facilities)
- name: VARCHAR
- ...

### Table: tasks
- id: INTEGER (PRIMARY KEY)
- facility_id: INTEGER (FOREIGN KEY به facilities)
- task_type: VARCHAR
- due_date: DATE
- status: VARCHAR
- ...

### Table: journal
- id: INTEGER (PRIMARY KEY)
- facility_id: INTEGER (FOREIGN KEY به facilities)
- entry_date: DATE
- description: TEXT
- ...

### Table: properties
- id: INTEGER (PRIMARY KEY)
- facility_id: INTEGER (FOREIGN KEY به facilities)
- country: VARCHAR (مثلاً 'IRAN' یا 'UAE')
- address: TEXT
- estimated_value: NUMERIC
- ...

### Table: securities
- id: INTEGER (PRIMARY KEY)
- facility_id: INTEGER (FOREIGN KEY به facilities)
- year: INTEGER (مثلاً 2022 تا 2026)
- security_type: VARCHAR
- value: NUMERIC
- ...

---

## 🔗 Relationships:
- یک مشتری می‌تواند چندین تسهیلات داشته باشد (یک به چند).
- هر تسهیلات می‌تواند چندین ضامن داشته باشد (یک به چند).
- هر تسهیلات می‌تواند چندین وظیفه (تسک) داشته باشد (یک به چند).
- هر تسهیلات می‌تواند چندین سند روزنامه (ژورنال) داشته باشد (یک به چند).
- هر تسهیلات می‌تواند چندین ملک داشته باشد (یک به چند).
- هر تسهیلات می‌تواند چندین وثیقه (security) داشته باشد (یک به چند).

---

## 🛠️ Notes:
- ستون `amount` در جدول `facilities` برای محاسبه جمع کل در داشبورد استفاده می‌شود.
- اطمینان حاصل کنید که مدل‌های backend با این طرح دیتابیس هماهنگ باشند.