"""
AI API Routes
روت‌های قابلیت‌های هوش مصنوعی
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.core.security import get_current_user, TokenData, require_permission
from app.services.ai_service import ai_service

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
    # Read file content
    content = await file.read()

    # Extract text based on file type
    filename = file.filename.lower()

    if filename.endswith('.txt'):
        text_content = content.decode('utf-8')
    elif filename.endswith('.pdf'):
        # در عمل از PyPDF2 یا pdfplumber استفاده کنید
        text_content = "PDF content extraction would go here"
    elif filename.endswith(('.doc', '.docx')):
        # در عمل از python-docx استفاده کنید
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
