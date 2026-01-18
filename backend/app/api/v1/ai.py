"""
AI API Routes
روت‌های قابلیت‌های هوش مصنوعی
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select
import json
import structlog

from app.core.security import get_current_user, TokenData, require_permission

logger = structlog.get_logger()
from app.core.database import get_db
from app.services.ai_service import ai_service, AIService
from app.models.settings import SystemSetting
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ========== Schemas ==========
class GenerateRequest(BaseModel):
    prompt: str
    provider: Optional[str] = None
    system_prompt: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


class AnalyzeDocumentRequest(BaseModel):
    content: str
    analysis_type: str = "summary"  # summary, risk_assessment, data_extraction
    provider: Optional[str] = None


class ExtractDataRequest(BaseModel):
    document_content: str
    provider: Optional[str] = None


class RiskAssessmentRequest(BaseModel):
    customer_data: Dict[str, Any]
    facilities_data: Optional[List[Dict[str, Any]]] = None
    provider: Optional[str] = None


class SummaryReportRequest(BaseModel):
    customer_data: Dict[str, Any]
    facilities_data: List[Dict[str, Any]]
    provider: Optional[str] = None


# ========== Helper Functions ==========
async def get_configured_providers_from_db(db: AsyncSession) -> List[str]:
    """
    دریافت لیست پرووایدرهای پیکربندی شده از دیتابیس
    Get list of configured AI providers from database settings
    """
    result = await db.execute(
        select(SystemSetting).where(
            SystemSetting.key.like("ai_provider_%"),
            SystemSetting.is_active == True
        )
    )
    settings = result.scalars().all()

    providers = []
    for setting in settings:
        provider_id = setting.key.replace("ai_provider_", "")
        try:
            data = json.loads(setting.value) if setting.value else {}
            # Check if provider has API key
            # If API key exists, consider enabled unless explicitly disabled
            if data.get("api_key"):
                # Default to enabled=True if not explicitly set to False
                if data.get("enabled", True) != False:
                    providers.append(provider_id)
        except json.JSONDecodeError:
            continue

    return providers


def reinitialize_ai_service_with_keys(providers_data: Dict[str, Dict]) -> None:
    """
    بروزرسانی AIService با کلیدهای API از دیتابیس
    Reinitialize AIService with API keys from database
    """
    from app.services.ai_service import OpenAIProvider, AnthropicProvider, GoogleAIProvider, AIProvider

    for provider_id, data in providers_data.items():
        api_key = data.get("api_key")
        # Skip if no API key or explicitly disabled
        if not api_key or data.get("enabled", True) == False:
            continue

        if provider_id == "openai" and AIProvider.OPENAI not in ai_service.providers:
            provider = OpenAIProvider()
            provider.api_key = api_key
            ai_service.providers[AIProvider.OPENAI] = provider

        elif provider_id == "anthropic" and AIProvider.ANTHROPIC not in ai_service.providers:
            provider = AnthropicProvider()
            provider.api_key = api_key
            ai_service.providers[AIProvider.ANTHROPIC] = provider

        elif provider_id == "google" and AIProvider.GOOGLE not in ai_service.providers:
            provider = GoogleAIProvider()
            provider.api_key = api_key
            ai_service.providers[AIProvider.GOOGLE] = provider


async def ensure_ai_providers_loaded(db: AsyncSession) -> AIService:
    """
    اطمینان از بارگذاری پرووایدرها از دیتابیس
    Ensure AI providers are loaded from database before using them
    """
    # If service already has providers, return it
    if await ai_service.get_available_providers():
        return ai_service

    # Load from database
    result = await db.execute(
        select(SystemSetting).where(
            SystemSetting.key.like("ai_provider_%"),
            SystemSetting.is_active == True
        )
    )
    settings = result.scalars().all()

    providers_data = {}
    for setting in settings:
        provider_id = setting.key.replace("ai_provider_", "")
        try:
            providers_data[provider_id] = json.loads(setting.value) if setting.value else {}
        except json.JSONDecodeError:
            continue

    if providers_data:
        reinitialize_ai_service_with_keys(providers_data)

    return ai_service


# ========== Routes ==========
@router.get("/status")
async def get_ai_status(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت وضعیت سرویس‌های AI
    """
    # First check providers initialized from environment variables
    env_providers = await ai_service.get_available_providers()

    # Then check providers from database
    db_providers = await get_configured_providers_from_db(db)

    # Combine both sources (removing duplicates)
    all_providers = list(set(env_providers + db_providers))

    # If we have db providers but not in service, reinitialize them
    if db_providers and not env_providers:
        # Get full provider data for reinitialization
        result = await db.execute(
            select(SystemSetting).where(
                SystemSetting.key.like("ai_provider_%"),
                SystemSetting.is_active == True
            )
        )
        settings = result.scalars().all()
        providers_data = {}
        for setting in settings:
            provider_id = setting.key.replace("ai_provider_", "")
            try:
                providers_data[provider_id] = json.loads(setting.value) if setting.value else {}
            except json.JSONDecodeError:
                continue

        reinitialize_ai_service_with_keys(providers_data)
        # Update available providers after reinitialization
        all_providers = list(set(await ai_service.get_available_providers() + db_providers))

    return {
        "available": len(all_providers) > 0,
        "enabled": len(all_providers) > 0,
        "available_providers": all_providers,
        "default_provider": "openai" if "openai" in all_providers else (all_providers[0] if all_providers else None),
        "features": [
            "document_analysis",
            "risk_assessment",
            "data_extraction",
            "report_generation",
            "smart_suggestions"
        ]
    }


@router.post("/generate")
async def generate_text(
    request: GenerateRequest,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    تولید متن با AI
    """
    try:
        # Ensure providers are loaded from database
        service = await ensure_ai_providers_loaded(db)

        result = await service.generate(
            prompt=request.prompt,
            provider=request.provider,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        return {
            "result": result,
            "provider": request.provider or "default"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/analyze")
async def analyze_document(
    request: AnalyzeDocumentRequest,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    تحلیل سند با AI
    """
    try:
        service = await ensure_ai_providers_loaded(db)

        result = await service.analyze_document(
            content=request.content,
            analysis_type=request.analysis_type,
            provider=request.provider
        )

        return {
            "analysis": result,
            "analysis_type": request.analysis_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/extract-data")
async def extract_customer_data(
    request: ExtractDataRequest,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    استخراج اطلاعات مشتری از سند
    """
    try:
        service = await ensure_ai_providers_loaded(db)

        result = await service.extract_customer_data(
            document_content=request.document_content,
            provider=request.provider
        )

        return {
            "extracted_data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/risk-assessment")
async def assess_risk(
    request: RiskAssessmentRequest,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    ارزیابی ریسک با AI
    """
    try:
        service = await ensure_ai_providers_loaded(db)

        result = await service.assess_risk(
            customer_data=request.customer_data,
            facilities_data=request.facilities_data,
            provider=request.provider
        )

        return {
            "risk_assessment": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.post("/generate-summary")
async def generate_summary_report(
    request: SummaryReportRequest,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    تولید گزارش خلاصه با AI
    """
    try:
        service = await ensure_ai_providers_loaded(db)

        result = await service.generate_summary_report(
            customer_data=request.customer_data,
            facilities_data=request.facilities_data,
            provider=request.provider
        )

        return {
            "summary_report": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/suggest-missing-fields")
async def suggest_missing_fields(
    profile_data: Dict[str, Any],
    provider: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    پیشنهاد فیلدهای ناقص پروفایل
    """
    try:
        service = await ensure_ai_providers_loaded(db)

        result = await service.suggest_missing_fields(
            profile_data=profile_data,
            provider=provider
        )

        return {
            "missing_fields": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestion failed: {str(e)}")


@router.post("/analyze-document-file")
async def analyze_uploaded_document(
    file: UploadFile = File(...),
    analysis_type: str = "summary",
    provider: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    تحلیل فایل آپلود شده
    """
    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith('.txt'):
        text_content = content.decode('utf-8')
    elif filename.endswith('.pdf'):
        text_content = "PDF content extraction would go here"
    elif filename.endswith(('.doc', '.docx')):
        text_content = "Word document content extraction would go here"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    try:
        service = await ensure_ai_providers_loaded(db)

        result = await service.analyze_document(
            content=text_content,
            analysis_type=analysis_type,
            provider=provider
        )

        return {
            "filename": file.filename,
            "analysis": result,
            "analysis_type": analysis_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/extract-document")
async def extract_document_data(
    file: UploadFile = File(...),
    provider: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    استخراج و دسته‌بندی هوشمند داده‌ها از فایل
    Extract and intelligently categorize data from uploaded file
    """
    from io import BytesIO

    # Ensure AI providers are loaded
    service = await ensure_ai_providers_loaded(db)

    content = await file.read()
    filename = file.filename.lower()
    extracted_items = []

    # Import pandas for all file type handling
    import pandas as pd

    try:
        # Extract text/data based on file type
        if filename.endswith(('.xlsx', '.xls')):

            # Read all sheets from Excel file
            all_records = []
            text_parts = []

            try:
                xl = pd.ExcelFile(BytesIO(content))
                sheet_names = xl.sheet_names
                logger.info(f"Excel file has sheets: {sheet_names}")

                for sheet_name in sheet_names:
                    try:
                        df = pd.read_excel(xl, sheet_name=sheet_name)
                        df = df.dropna(how='all')  # Remove empty rows

                        if not df.empty:
                            text_parts.append(f"Sheet: {sheet_name}\n{df.to_string()}")

                            # Add sheet records with sheet name context
                            sheet_records = df.to_dict('records')
                            for record in sheet_records:
                                record['_sheet'] = sheet_name
                            all_records.extend(sheet_records)

                            logger.info(f"Sheet '{sheet_name}': {len(sheet_records)} records")
                    except Exception as sheet_error:
                        logger.warning(f"Error reading sheet {sheet_name}: {sheet_error}")
                        continue

            except Exception as xl_error:
                # Fallback to single sheet reading
                logger.warning(f"Error reading Excel file, trying single sheet: {xl_error}")
                df = pd.read_excel(BytesIO(content))
                df = df.dropna(how='all')
                text_parts = [df.to_string()]
                all_records = df.to_dict('records')

            text_content = "\n\n".join(text_parts)
            records = all_records
            logger.info(f"Total extracted records: {len(records)}")

        elif filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
            text_content = df.to_string()
            records = df.to_dict('records')

        elif filename.endswith('.pdf'):
            # Use pdfplumber for PDF extraction
            try:
                import pdfplumber
                with pdfplumber.open(BytesIO(content)) as pdf:
                    pages_text = []
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            pages_text.append(f"--- Page {i+1} ---\n{page_text}")
                        # Also try to extract tables
                        tables = page.extract_tables()
                        for table in tables:
                            if table:
                                table_str = "\n".join(["\t".join([str(cell) if cell else "" for cell in row]) for row in table])
                                pages_text.append(f"--- Table on Page {i+1} ---\n{table_str}")
                    text_content = "\n\n".join(pages_text)
                    if not text_content.strip():
                        text_content = "[PDF file contains no extractable text - may be scanned/image-based]"
                    logger.info(f"Extracted {len(pages_text)} sections from PDF")
            except ImportError as e:
                logger.error(f"pdfplumber not installed: {e}")
                raise HTTPException(status_code=500, detail="PDF library (pdfplumber) not installed on server")
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to extract PDF: {str(e)}")
            records = []

        elif filename.endswith(('.doc', '.docx')):
            try:
                from docx import Document
                doc = Document(BytesIO(content))
                text_parts = []

                # Extract paragraphs
                for para in doc.paragraphs:
                    if para.text.strip():
                        text_parts.append(para.text)

                # Extract tables
                for table in doc.tables:
                    table_rows = []
                    for row in table.rows:
                        cells = [cell.text.strip() for cell in row.cells]
                        if any(cells):
                            table_rows.append("\t".join(cells))
                    if table_rows:
                        text_parts.append("--- Table ---")
                        text_parts.extend(table_rows)

                text_content = "\n".join(text_parts)
                if not text_content.strip():
                    text_content = "[Word document appears to be empty or contains only images]"
                logger.info(f"Extracted {len(text_parts)} sections from Word document")
            except ImportError as e:
                logger.error(f"python-docx not installed: {e}")
                raise HTTPException(status_code=500, detail="Word document library (python-docx) not installed on server")
            except Exception as e:
                logger.error(f"Word extraction error: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to extract Word document: {str(e)}")
            records = []

        elif filename.endswith('.txt'):
            text_content = content.decode('utf-8')
            records = []

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")

        # Use AI to analyze and categorize the extracted data
        categorization_prompt = f"""
Analyze the following document content and extract structured data items.
For each item found, categorize it into one of these categories:
- customer: Customer/client information (name, contact, ID numbers, etc.)
- facility: Credit facility/loan information (amounts, dates, types)
- property: Real estate/collateral information (addresses, values)
- checklist: Tasks, to-dos, pending items, requirements
- guarantor: Guarantor information
- note: General notes or comments

Return a JSON array with this format:
[
  {{
    "category": "customer|facility|property|checklist|guarantor|note",
    "confidence": 0.0-1.0,
    "data": {{ extracted field/value pairs }},
    "originalText": "source text for this item"
  }}
]

Document content:
{text_content[:8000]}
"""

        try:
            ai_result = await service.generate(
                prompt=categorization_prompt,
                provider=provider,
                system_prompt="You are a data extraction AI. Return only valid JSON arrays. Be precise and accurate.",
                max_tokens=4096,
                temperature=0.3
            )

            # Parse AI response
            try:
                # Find JSON in response
                json_start = ai_result.find('[')
                json_end = ai_result.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = ai_result[json_start:json_end]
                    extracted_items = json.loads(json_str)
            except json.JSONDecodeError:
                pass

        except Exception as ai_error:
            logger.warning(f"AI extraction failed: {ai_error}")

        # If AI returned no items, use basic extraction from records
        if not extracted_items and records:
            logger.info(f"Using fallback extraction for {len(records)} records")

            # Check filename for category hints
            filename_lower = file.filename.lower()
            default_category = "unknown"
            if 'propert' in filename_lower or 'iran' in filename_lower or 'uae' in filename_lower:
                default_category = "property"
            elif 'customer' in filename_lower or 'client' in filename_lower:
                default_category = "customer"
            elif 'facilit' in filename_lower or 'loan' in filename_lower:
                default_category = "facility"
            elif 'guarantor' in filename_lower:
                default_category = "guarantor"
            elif 'task' in filename_lower or 'checklist' in filename_lower:
                default_category = "checklist"

            # Extended keyword lists for better detection
            customer_keywords = ['name', 'email', 'phone', 'customer', 'client', 'contact', 'account']
            facility_keywords = ['amount', 'loan', 'facility', 'credit', 'overdraft', 'od', 'lg', 'lc', 'sanction']
            property_keywords = ['property', 'address', 'location', 'sqft', 'deed', 'mortgage', 'real estate',
                                 'land', 'building', 'apartment', 'villa', 'plot', 'city', 'country', 'iran',
                                 'uae', 'dubai', 'tehran', 'area', 'meter', 'sqm', 'value', 'ملک', 'آدرس']
            guarantor_keywords = ['guarantor', 'guarantee', 'cheque', 'chq', 'ضامن']
            checklist_keywords = ['task', 'pending', 'due', 'check', 'todo', 'action', 'status']

            for i, record in enumerate(records):  # Process all records
                record_str = str(record).lower()
                record_keys = ' '.join([str(k).lower() for k in record.keys()])

                # Try to guess category based on fields and content
                category = default_category

                if any(k in record_str or k in record_keys for k in customer_keywords):
                    category = "customer"
                elif any(k in record_str or k in record_keys for k in facility_keywords):
                    category = "facility"
                elif any(k in record_str or k in record_keys for k in property_keywords):
                    category = "property"
                elif any(k in record_str or k in record_keys for k in guarantor_keywords):
                    category = "guarantor"
                elif any(k in record_str or k in record_keys for k in checklist_keywords):
                    category = "checklist"

                # Get sheet name if available
                sheet_name = record.pop('_sheet', 'Sheet1')

                extracted_items.append({
                    "category": category,
                    "confidence": 0.7 if category != "unknown" else 0.5,
                    "data": {k: v for k, v in record.items() if pd.notna(v) and k != '_sheet'},
                    "originalText": f"Sheet: {sheet_name}, Row {i+1}"
                })

            logger.info(f"Fallback extracted {len(extracted_items)} items")

        # Add unique IDs to items
        for i, item in enumerate(extracted_items):
            item["id"] = str(i + 1)

        # Calculate category counts
        categories = {}
        for item in extracted_items:
            cat = item.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "items": extracted_items,
            "summary": f"Extracted {len(extracted_items)} items from {file.filename}",
            "totalItems": len(extracted_items),
            "categories": categories
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/import-extracted")
async def import_extracted_data(
    data: Dict[str, Any],
    current_user: TokenData = Depends(require_permission("use:ai")),
    db: AsyncSession = Depends(get_db)
):
    """
    ذخیره داده‌های استخراج شده در دیتابیس
    Import extracted data items into the database
    """
    from sqlalchemy import select
    from decimal import Decimal
    from app.models.customer import Customer, CustomerProfile, AccountType, CustomerStatus
    from app.models.facility import Facility, FacilityType, FacilityStatus
    from app.models.property import Property, PropertyLocation, PropertyType, PropertyStatus
    from app.models.guarantor import Guarantor
    from app.models.task import CustomTask, TaskStatus, TaskPriority
    from app.models.note import Note, NoteCategory, NotePriority
    from app.models.base import generate_uuid, generate_short_id

    items = data.get("items", [])
    target_customer_id = data.get("customer_id")  # Optional: merge to specific customer

    if not items:
        raise HTTPException(status_code=400, detail="No items to import")

    imported_count = 0
    errors = []
    results = {"customers": 0, "facilities": 0, "properties": 0, "guarantors": 0, "tasks": 0, "notes": 0}

    try:
        for item in items:
            category = item.get("category", "unknown")
            item_data = item.get("data", {})

            try:
                if category == "customer":
                    # Create or update customer
                    account_no = str(item_data.get("account_no") or item_data.get("AccountNo") or generate_short_id(""))
                    name = item_data.get("name") or item_data.get("customer_name") or item_data.get("full_name") or "Unknown"

                    # Check if exists
                    result = await db.execute(
                        select(Customer).where(Customer.account_no == account_no)
                    )
                    existing = result.scalar_one_or_none()

                    if not existing:
                        customer = Customer(
                            id=generate_uuid(),
                            account_no=account_no,
                            customer_name=name,
                            branch=str(item_data.get("branch", "")),
                            email=item_data.get("email"),
                            phone=item_data.get("phone"),
                            mobile=item_data.get("mobile"),
                            address=item_data.get("address"),
                            account_type=AccountType.CORPORATE if "corporate" in str(item_data.get("type", "")).lower() else AccountType.RETAIL,
                            status=CustomerStatus.ACTIVE,
                        )
                        db.add(customer)
                        results["customers"] += 1
                        imported_count += 1

                elif category == "facility":
                    customer_id = target_customer_id or item_data.get("customer_id")
                    if customer_id:
                        ftype = str(item_data.get("type", "")).lower()
                        if "od" in ftype or "overdraft" in ftype:
                            facility_type = FacilityType.OD
                        elif "loan" in ftype:
                            facility_type = FacilityType.LOAN
                        elif "lg" in ftype:
                            facility_type = FacilityType.LG
                        else:
                            facility_type = FacilityType.OTHER

                        amount = item_data.get("amount") or item_data.get("approved_amount") or 0
                        try:
                            amount = Decimal(str(amount).replace(",", ""))
                        except:
                            amount = Decimal("0")

                        facility = Facility(
                            id=generate_short_id("FAC-"),
                            customer_id=customer_id,
                            facility_type=facility_type,
                            facility_name=item_data.get("name") or item_data.get("facility_no"),
                            approved_amount=amount,
                            currency=item_data.get("currency", "AED"),
                            status=FacilityStatus.ACTIVE,
                        )
                        db.add(facility)
                        results["facilities"] += 1
                        imported_count += 1

                elif category == "property":
                    customer_id = target_customer_id or item_data.get("customer_id")
                    if customer_id:
                        prop = Property(
                            id=generate_short_id("PRP-"),
                            customer_id=customer_id,
                            location=PropertyLocation.UAE if "uae" in str(item_data.get("location", "")).lower() else PropertyLocation.IRAN,
                            property_type=PropertyType.BUILDING,
                            city=item_data.get("city"),
                            address=item_data.get("address"),
                            deed_no=item_data.get("deed_no"),
                            status=PropertyStatus.MORTGAGED,
                        )
                        db.add(prop)
                        results["properties"] += 1
                        imported_count += 1

                elif category == "guarantor":
                    customer_id = target_customer_id or item_data.get("customer_id")
                    if customer_id:
                        guarantor = Guarantor(
                            id=generate_short_id("GNT-"),
                            customer_id=customer_id,
                            guarantor_name=item_data.get("name") or item_data.get("guarantor_name") or "Unknown",
                            phone=item_data.get("phone") or item_data.get("account"),
                        )
                        db.add(guarantor)
                        results["guarantors"] += 1
                        imported_count += 1

                elif category == "checklist" or category == "task":
                    task = CustomTask(
                        id=generate_short_id("TSK-"),
                        customer_id=target_customer_id,
                        task_name=item_data.get("name") or item_data.get("task") or item_data.get("item") or "Task",
                        status=TaskStatus.PENDING,
                        priority=TaskPriority.MEDIUM,
                        notes=item_data.get("notes") or item_data.get("description"),
                    )
                    db.add(task)
                    results["tasks"] += 1
                    imported_count += 1

                elif category == "note":
                    if target_customer_id:
                        note = Note(
                            id=generate_short_id("NTE-"),
                            customer_id=target_customer_id,
                            title=item_data.get("title") or "Note",
                            content=item_data.get("content") or item_data.get("text") or str(item_data),
                            category=NoteCategory.GENERAL,
                            priority=NotePriority.MEDIUM,
                        )
                        db.add(note)
                        results["notes"] += 1
                        imported_count += 1

            except Exception as e:
                errors.append(f"Item error: {str(e)}")

        await db.commit()

        return {
            "success": True,
            "imported": imported_count,
            "total": len(items),
            "results": results,
            "errors": errors if errors else None
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
