# فهرستِ سطحِ سامانه (Inventory)

> این فایل را **ناظرِ خودکار** در هر اجرا بازتولید می‌کند — دستی ویرایشش نکن.
> هر صفحه/دکمه/endpointی که بعداً اضافه شود، خودکار این‌جا ظاهر می‌شود.

| سنجه | تعداد |
|---|---|
| صفحه‌ها | 32 |
| آیتم‌های منو | 19 |
| دکمه‌ها | 333 |
| ورودی‌ها (input/select/textarea) | 342 |
| مسیرهای API | 213 |
| متدهای کلاینتِ API | 170 |
| سرویس‌ها | 39 |
| مدل‌ها | 26 |

## منوی کناری

| مسیر | برچسب |
|---|---|
| `/dashboard` | Dashboard |
| `/customers` | Customers |
| `/facilities` | Facilities |
| `/properties` | Mortgaged Properties |
| `/forms` | Forms |
| `/general` | General Checklists |
| `/personal` | Personal Notes |
| `/staff` | Staff Directory |
| `/daily-log` | Daily Log |
| `/knowledge` | Knowledge Base |
| `/reports` | Reports |
| `/charge-tariff` | Charge Tariff |
| `/data-quality` | Data Quality |
| `/import` | Import |
| `/users` | Users |
| `/audit` | Audit Log |
| `/cleanup` | Database Cleanup |
| `/settings` | Settings |
| `/trash` | Recycle Bin |

## صفحه‌ها و کنترل‌هایشان

| مسیر | خط | دکمه | ورودی | لینک | فراخوانیِ API |
|---|---|---|---|---|---|
| `/audit` | 155 | 4 | 5 | 0 | 1 |
| `/auth/callback` | 53 | 0 | 0 | 0 | 0 |
| `/charge-tariff` | 215 | 5 | 12 | 0 | 3 |
| `/cleanup` | 344 | 3 | 3 | 0 | 6 |
| `/credit-file` | 122 | 3 | 1 | 0 | 2 |
| `/credit-file-corporate` | 666 | 15 | 41 | 0 | 7 |
| `/credit-file-retail` | 613 | 13 | 40 | 0 | 4 |
| `/customer-detail` | 1423 | 42 | 32 | 0 | 27 |
| `/customers` | 564 | 12 | 12 | 0 | 5 |
| `/daily-log` | 71 | 1 | 2 | 0 | 1 |
| `/dashboard` | 427 | 0 | 0 | 0 | 2 |
| `/data-quality` | 201 | 3 | 2 | 1 | 1 |
| `/facilities` | 579 | 13 | 18 | 0 | 5 |
| `/facility-detail` | 250 | 5 | 2 | 0 | 2 |
| `/forms` | 154 | 0 | 0 | 2 | 0 |
| `/general` | 168 | 6 | 4 | 0 | 9 |
| `/import` | 296 | 3 | 3 | 0 | 2 |
| `/knowledge` | 247 | 1 | 1 | 0 | 2 |
| `/letter` | 3667 | 101 | 37 | 0 | 26 |
| `/login` | 219 | 2 | 2 | 1 | 0 |
| `/offer-letter` | 1890 | 38 | 35 | 0 | 8 |
| `/` | 40 | 0 | 0 | 0 | 0 |
| `/personal` | 107 | 3 | 3 | 0 | 5 |
| `/profile` | 150 | 2 | 5 | 0 | 2 |
| `/properties` | 287 | 8 | 6 | 0 | 5 |
| `/reports` | 194 | 5 | 0 | 0 | 3 |
| `/sanction` | 450 | 9 | 25 | 0 | 2 |
| `/settings` | 449 | 12 | 2 | 0 | 13 |
| `/staff` | 177 | 6 | 14 | 0 | 5 |
| `/trash` | 116 | 1 | 0 | 0 | 2 |
| `/users` | 275 | 7 | 7 | 0 | 5 |
| `/voucher` | 1033 | 10 | 28 | 0 | 10 |

## مسیرهای API

| متد | مسیر |
|---|---|
| POST | `/api/ai/models` |
| PUT | `/api/ai/models/{model_id}` |
| DELETE | `/api/ai/models/{model_id}` |
| POST | `/api/ai/models/{model_id}/test` |
| GET | `/api/ai/overview` |
| PUT | `/api/ai/providers/{key}` |
| POST | `/api/ai/providers/{key}/sync-models` |
| PUT | `/api/ai/routes/{task}` |
| GET | `/api/audit/` |
| POST | `/api/audit/activity` |
| GET | `/api/audit/customer/{account_no}` |
| GET | `/api/audit/customer/{account_no}/export.csv` |
| POST | `/api/auth/change-password` |
| GET | `/api/auth/config` |
| GET | `/api/auth/google/callback` |
| GET | `/api/auth/google/drive/connect` |
| POST | `/api/auth/google/drive/disconnect` |
| GET | `/api/auth/google/login` |
| POST | `/api/auth/login` |
| POST | `/api/auth/logout` |
| GET | `/api/auth/me` |
| PUT | `/api/auth/me` |
| POST | `/api/auth/refresh` |
| POST | `/api/auth/verify` |
| GET | `/api/charge-tariff` |
| POST | `/api/charge-tariff` |
| GET | `/api/charge-tariff/` |
| POST | `/api/charge-tariff/` |
| POST | `/api/charge-tariff/compute` |
| DELETE | `/api/charge-tariff/{rule_id}` |
| POST | `/api/cleanup/ai-review` |
| POST | `/api/cleanup/apply` |
| GET | `/api/cleanup/config` |
| PUT | `/api/cleanup/config` |
| GET | `/api/cleanup/history` |
| POST | `/api/cleanup/scan` |
| POST | `/api/crm/attachments/{account_no}` |
| DELETE | `/api/crm/attachments/{attachment_id}` |
| GET | `/api/crm/attachments/{attachment_id}/download` |
| GET | `/api/crm/attachments/{attachment_id}/view` |
| GET | `/api/crm/backup/drive/status` |
| POST | `/api/crm/backup/drive/sync` |
| GET | `/api/crm/backup/export.json` |
| PATCH | `/api/crm/checklist/{account_no}` |
| GET | `/api/crm/completeness/{account_no}` |
| GET | `/api/crm/credit-reviews/{account_no}` |
| POST | `/api/crm/daily-log` |
| GET | `/api/crm/data-quality` |
| POST | `/api/crm/email-summary/{account_no}` |
| POST | `/api/crm/extract-draft` |
| POST | `/api/crm/facilities/{account_no}` |
| PATCH | `/api/crm/facility-checklist/{facility_id}` |
| GET | `/api/crm/facility-types` |
| POST | `/api/crm/facility-types` |
| POST | `/api/crm/fixed-deposits/{account_no}` |
| PATCH | `/api/crm/fixed-deposits/{item_id}` |
| DELETE | `/api/crm/fixed-deposits/{item_id}` |
| GET | `/api/crm/guarantors/{account_no}` |
| POST | `/api/crm/guarantors/{account_no}` |
| POST | `/api/crm/guarantors/{account_no}/release` |
| GET | `/api/crm/merge-status` |
| POST | `/api/crm/notes/{account_no}` |
| GET | `/api/crm/offer-letter-data/{account_no}` |
| POST | `/api/crm/offer-letter-data/{account_no}` |
| GET | `/api/crm/partner-names` |
| POST | `/api/crm/partners/{account_no}` |
| PATCH | `/api/crm/partners/{item_id}` |
| DELETE | `/api/crm/partners/{item_id}` |
| PATCH | `/api/crm/profile/{account_no}` |
| POST | `/api/crm/properties/{account_no}` |
| PATCH | `/api/crm/properties/{item_id}` |
| DELETE | `/api/crm/properties/{item_id}` |
| POST | `/api/crm/properties/{property_id}/events` |
| DELETE | `/api/crm/property-events/{event_id}` |
| GET,POST | `/api/crm/run-expiry-scan` |
| GET,POST | `/api/crm/run-merge` |
| POST | `/api/crm/sanction/{account_no}` |
| GET | `/api/crm/summary/{account_no}/export.pdf` |
| POST | `/api/crm/tasks/{account_no}` |
| PATCH | `/api/crm/tasks/{task_id}` |
| GET | `/api/customers/` |
| POST | `/api/customers/` |
| POST | `/api/customers/bulk/delete` |
| GET | `/api/customers/export.csv` |
| GET | `/api/customers/export.xlsx` |
| GET | `/api/customers/stats/summary` |
| GET | `/api/customers/{customer_id}` |
| PUT | `/api/customers/{customer_id}` |
| DELETE | `/api/customers/{customer_id}` |
| GET | `/api/customers/{customer_id}/detail` |
| GET | `/api/customers/{customer_id}/facilities` |
| POST | `/api/customers/{customer_id}/restore` |
| GET | `/api/departments/` |
| POST | `/api/departments/resolve` |
| PATCH | `/api/departments/{dept_id}` |
| DELETE | `/api/departments/{dept_id}` |
| GET | `/api/facilities/` |
| POST | `/api/facilities/` |
| POST | `/api/facilities/bulk/delete` |
| GET | `/api/facilities/export.csv` |
| GET | `/api/facilities/export.xlsx` |
| GET | `/api/facilities/search/advanced` |
| GET | `/api/facilities/{facility_id}` |
| PUT | `/api/facilities/{facility_id}` |
| DELETE | `/api/facilities/{facility_id}` |
| GET | `/api/facilities/{facility_id}/detail` |
| POST | `/api/facilities/{facility_id}/restore` |
| PATCH | `/api/facilities/{facility_id}/status` |
| GET | `/api/fx/` |
| PUT | `/api/fx/` |
| GET | `/api/fx/convert` |
| DELETE | `/api/general/checklists/{checklist_id}` |
| POST | `/api/general/checklists/{checklist_id}/items` |
| PATCH | `/api/general/items/{item_id}` |
| DELETE | `/api/general/items/{item_id}` |
| GET | `/api/general/profiles` |
| POST | `/api/general/profiles` |
| DELETE | `/api/general/profiles/{profile_id}` |
| GET | `/api/general/profiles/{profile_id}/checklists` |
| POST | `/api/general/profiles/{profile_id}/checklists` |
| GET | `/api/imports/ai-models` |
| POST | `/api/imports/analyze` |
| POST | `/api/imports/customers` |
| GET | `/api/imports/customers/template` |
| POST | `/api/imports/facilities` |
| GET | `/api/imports/facilities/template` |
| GET | `/api/imports/jobs/{job_id}` |
| GET | `/api/knowledge/` |
| POST | `/api/knowledge/entries` |
| DELETE | `/api/knowledge/entries/{entry_id}` |
| DELETE | `/api/knowledge/topics/{topic_id}` |
| POST | `/api/letter-ai/analyze` |
| POST | `/api/letter-ai/apply-db` |
| GET | `/api/letter-ai/attachment-job/{job_id}` |
| POST | `/api/letter-ai/attachment-text/{attachment_id}` |
| POST | `/api/letter-ai/extract-attachment/{attachment_id}` |
| POST | `/api/letter-ai/extract-attachments-job` |
| POST | `/api/letter-ai/generate-attachment` |
| GET | `/api/letter-ai/models` |
| POST | `/api/letter-ai/template-text` |
| GET | `/api/letters/` |
| POST | `/api/letters/` |
| GET | `/api/letters/{letter_id}` |
| PATCH | `/api/letters/{letter_id}` |
| DELETE | `/api/letters/{letter_id}` |
| GET | `/api/letters/{letter_id}/attachments` |
| GET | `/api/notifications/` |
| POST | `/api/notifications/read-all` |
| GET | `/api/notifications/unread-count` |
| POST | `/api/notifications/{notification_id}/read` |
| GET | `/api/offer-letters/` |
| POST | `/api/offer-letters/` |
| GET | `/api/offer-letters/{offer_id}` |
| PUT | `/api/offer-letters/{offer_id}` |
| DELETE | `/api/offer-letters/{offer_id}` |
| GET | `/api/offer-letters/{offer_id}/export.csv` |
| GET | `/api/offer-letters/{offer_id}/export.pdf` |
| POST | `/api/offer-letters/{offer_id}/generate-schedule` |
| POST | `/api/offer-letters/{offer_id}/restore` |
| POST | `/api/offer-letters/{offer_id}/status` |
| GET | `/api/personal/notes` |
| POST | `/api/personal/notes` |
| POST | `/api/personal/notes/send-email` |
| PATCH | `/api/personal/notes/{note_id}` |
| DELETE | `/api/personal/notes/{note_id}` |
| POST | `/api/policy-inbox/apply` |
| POST | `/api/policy-inbox/ensure` |
| POST | `/api/policy-inbox/import-file` |
| POST | `/api/policy-inbox/scan` |
| GET | `/api/properties/` |
| POST | `/api/properties/` |
| GET | `/api/properties/export.csv` |
| GET | `/api/properties/facets` |
| PUT | `/api/properties/{item_id}` |
| DELETE | `/api/properties/{item_id}` |
| GET | `/api/reports/portfolio` |
| GET | `/api/reports/portfolio/export.csv` |
| GET | `/api/reports/portfolio/export.pdf` |
| GET | `/api/reports/portfolio/export.xlsx` |
| GET | `/api/reports/top-exposures` |
| GET | `/api/settings/` |
| PUT | `/api/settings/` |
| GET | `/api/simulate-unhandled-error` |
| GET | `/api/staff/` |
| POST | `/api/staff/` |
| GET | `/api/staff/departments` |
| PATCH | `/api/staff/{staff_id}` |
| DELETE | `/api/staff/{staff_id}` |
| GET | `/api/stats/dashboard` |
| GET | `/api/stats/expiring-documents` |
| POST | `/api/stats/snapshot` |
| POST | `/api/telegram/delete-webhook` |
| PUT | `/api/telegram/prefs` |
| POST | `/api/telegram/set-webhook` |
| GET | `/api/telegram/status` |
| POST | `/api/telegram/test` |
| POST | `/api/telegram/webhook` |
| GET | `/api/telegram/webhook-info` |
| GET | `/api/trash/` |
| POST | `/api/trash/{entity}/{item_id}/restore` |
| GET | `/api/users/` |
| POST | `/api/users/` |
| GET | `/api/users/{user_id}` |
| PUT | `/api/users/{user_id}` |
| DELETE | `/api/users/{user_id}` |
| POST | `/api/vouchers/export-excel` |
| GET | `/health` |
