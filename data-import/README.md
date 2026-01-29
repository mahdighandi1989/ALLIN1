# Data Import Folder

Place your data files here for importing into the database.

## Supported Formats
- Excel: `.xlsx`, `.xls`, `.xlsm`
- Word: `.docx`
- CSV: `.csv`
- JSON: `.json`
- PDF: `.pdf`

## Security & Validation

### File Security
- **Maximum file size**: 50MB per file
- **Virus scanning**: All files are scanned before processing
- **File type validation**: Only whitelisted file extensions are allowed
- **Content validation**: File headers are verified to match extensions

### Data Validation
- **Schema validation**: All imported data must match predefined schemas
- **Data sanitization**: HTML tags, scripts, and malicious content are stripped
- **Field validation**: Data types, lengths, and formats are strictly enforced
- **Duplicate detection**: Prevents duplicate records based on unique identifiers

### Access Control
- **Authentication required**: Only authenticated users can import data
- **Role-based access**: Import permissions based on user roles
- **Audit logging**: All import activities are logged with user details
- **Rate limiting**: Maximum 10 import operations per hour per user

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

## Expected Columns & Validation Rules

### Customers
**Required Fields:**
- `name` (string, 2-200 chars, no HTML/scripts)
- `account_no` (string, unique, 5-50 chars, alphanumeric only)

**Optional Fields:**
- `name_en` (string, 2-200 chars, Latin characters only)
- `customer_type` (enum: retail, corporate, sme)
- `status` (enum: active, inactive, suspended)
- `national_id` (string, validated format per country)
- `phone` (string, E.164 format validation)
- `email` (string, RFC 5322 compliant)
- `address` (string, max 500 chars, sanitized)

**Validation Rules:**
- Email addresses must be unique and valid
- Phone numbers validated against international formats
- National IDs checked for format and checksum validity
- Names cannot contain special characters or numbers

### Facilities
**Required Fields:**
- `customer_id` (string, must exist in customers table)
- `facility_type` (enum: loan, overdraft, lc, lg, other)
- `amount` (decimal, positive, max 999,999,999.99)
- `currency` (ISO 4217 code: AED, USD, EUR, etc.)

**Optional Fields:**
- `interest_rate` (decimal, 0-100, max 2 decimal places)
- `start_date` (ISO 8601 date format)
- `end_date` (ISO 8601 date format, must be after start_date)
- `status` (enum: active, pending, closed, defaulted)

**Validation Rules:**
- Amount must be positive and within reasonable limits
- Dates must be valid and logical (end_date > start_date)
- Interest rates within acceptable banking ranges
- Currency codes validated against ISO standards

### Properties
**Required Fields:**
- `title` (string, 5-200 chars, sanitized)
- `location` (string, 5-200 chars)
- `property_type` (enum: residential, commercial, industrial, land)
- `area` (decimal, positive, in square meters)
- `value` (decimal, positive)
- `currency` (ISO 4217 code)

**Validation Rules:**
- Property values must be reasonable for the location
- Area measurements validated against property type
- Location names sanitized and geocoded when possible

## Data Sanitization Process

### Input Sanitization
1. **HTML/Script removal**: All HTML tags and JavaScript removed
2. **SQL injection prevention**: Special characters escaped
3. **XSS protection**: Malicious scripts and content filtered
4. **File path traversal**: Directory traversal attempts blocked

### Content Validation
1. **Character encoding**: UTF-8 validation and normalization
2. **Length limits**: All fields checked against maximum lengths
3. **Format validation**: Dates, emails, phones validated against patterns
4. **Business logic**: Cross-field validation (e.g., end_date > start_date)

## Error Handling & Reporting

### Import Process
- **Pre-validation**: Files scanned before processing begins
- **Row-by-row validation**: Each record validated individually
- **Error collection**: All validation errors collected and reported
- **Rollback capability**: Failed imports can be rolled back completely

### Error Reports
- **Detailed logs**: Line numbers and specific validation failures
- **Summary reports**: Overview of successful vs failed records
- **Corrective guidance**: Suggestions for fixing validation errors
- **Export capability**: Error reports can be exported for review

## Running Import

### Prerequisites
- Valid authentication token
- Appropriate user permissions
- Files placed in correct directory
- Network connectivity to database

### Command