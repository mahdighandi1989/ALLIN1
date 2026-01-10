# Data Import Folder

Place your data files here for importing into the database.

## Supported Formats
- Excel: `.xlsx`, `.xls`, `.xlsm`
- Word: `.docx`
- CSV: `.csv`
- JSON: `.json`
- PDF: `.pdf`

## File Naming Convention
Name your files based on the data type they contain:

| Prefix | Data Type | Example |
|--------|-----------|---------|
| `customers_` | Customer data | `customers_list.xlsx` |
| `facilities_` | Facility/Loan data | `facilities_2024.xlsx` |
| `properties_` | Property data | `properties_uae.xlsx` |
| `guarantors_` | Guarantor data | `guarantors.csv` |
| `checklists_` | Checklist templates | `checklists_corporate.xlsx` |
| `documents_` | Document metadata | `documents_list.json` |

## Expected Columns

### Customers
- name, name_en, customer_type, status, national_id, phone, email, address

### Facilities
- facility_type, amount, currency, interest_rate, start_date, end_date, status

### Properties
- title, location, property_type, area, value, currency

## Running Import
```bash
cd backend
python -m app.scripts.import_data
```

After import, files will be moved to `archive/imported-data/`
