"""
AI API Routes
روت‌های قابلیت‌های هوش مصنوعی
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.services.ai_service import ai_service
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


# ========== Routes ==========
@router.get("/status")
async def get_ai_status(
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت وضعیت سرویس‌های AI
    """
    providers = ai_service.get_available_providers()

    return {
        "enabled": len(providers) > 0,
        "available_providers": providers,
        "default_provider": "openai" if "openai" in providers else (providers[0] if providers else None),
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    تولید متن با AI
    """
    try:
        result = await ai_service.generate(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    تحلیل سند با AI
    """
    try:
        result = await ai_service.analyze_document(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    استخراج اطلاعات مشتری از سند
    """
    try:
        result = await ai_service.extract_customer_data(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    ارزیابی ریسک با AI
    """
    try:
        result = await ai_service.assess_risk(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    تولید گزارش خلاصه با AI
    """
    try:
        result = await ai_service.generate_summary_report(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    پیشنهاد فیلدهای ناقص پروفایل
    """
    try:
        result = await ai_service.suggest_missing_fields(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
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
        result = await ai_service.analyze_document(
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
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """
    استخراج و دسته‌بندی هوشمند داده‌ها از فایل
    Extract and intelligently categorize data from uploaded file
    """
    import json
    from io import BytesIO

    content = await file.read()
    filename = file.filename.lower()
    extracted_items = []

    try:
        # Extract text/data based on file type
        if filename.endswith(('.xlsx', '.xls')):
            # Excel file - use pandas
            import pandas as pd
            df = pd.read_excel(BytesIO(content))
            text_content = df.to_string()

            # Also extract as structured data
            records = df.to_dict('records')

        elif filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(BytesIO(content))
            text_content = df.to_string()
            records = df.to_dict('records')

        elif filename.endswith('.pdf'):
            # Use pdfplumber or PyPDF2
            try:
                import pdfplumber
                with pdfplumber.open(BytesIO(content)) as pdf:
                    text_content = "\n".join([page.extract_text() or "" for page in pdf.pages])
            except ImportError:
                text_content = f"[PDF file: {file.filename}]"
            records = []

        elif filename.endswith(('.doc', '.docx')):
            try:
                from docx import Document
                doc = Document(BytesIO(content))
                text_content = "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                text_content = f"[Word file: {file.filename}]"
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
            ai_result = await ai_service.generate(
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
            # If AI fails, do basic extraction from records
            if records:
                for i, record in enumerate(records[:50]):  # Limit to 50 records
                    # Try to guess category based on fields
                    category = "unknown"
                    if any(k.lower() in str(record).lower() for k in ['name', 'email', 'phone', 'customer']):
                        category = "customer"
                    elif any(k.lower() in str(record).lower() for k in ['amount', 'loan', 'facility', 'credit']):
                        category = "facility"
                    elif any(k.lower() in str(record).lower() for k in ['property', 'address', 'location', 'sqft']):
                        category = "property"
                    elif any(k.lower() in str(record).lower() for k in ['task', 'pending', 'due', 'check']):
                        category = "checklist"

                    extracted_items.append({
                        "category": category,
                        "confidence": 0.6,
                        "data": {k: v for k, v in record.items() if pd.notna(v)},
                        "originalText": f"Row {i+1}"
                    })

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
