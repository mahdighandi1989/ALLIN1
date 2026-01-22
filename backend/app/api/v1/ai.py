"""
AI API
API هوش مصنوعی
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO
import json

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.services.ai_service import ai_service

router = APIRouter()


class GenerateRequest(BaseModel):
    prompt: str
    provider: Optional[str] = None
    system_prompt: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


class AnalyzeRequest(BaseModel):
    content: str
    analysis_type: str = "summary"
    provider: Optional[str] = None


class ProviderConfig(BaseModel):
    api_key: str
    model: Optional[str] = None
    enabled: bool = True


@router.get("/status")
async def get_ai_status(current_user: TokenData = Depends(get_current_user)):
    """Get AI service status"""
    providers = ai_service.get_available_providers()
    return {
        "available": len(providers) > 0,
        "providers": providers,
        "default_provider": ai_service.get_default_provider(),
        "features": ["generate", "analyze", "extract"]
    }


@router.post("/generate")
async def generate_text(
    request: GenerateRequest,
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """Generate text with AI"""
    try:
        result = await ai_service.generate(
            prompt=request.prompt,
            provider=request.provider,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return {"result": result, "provider": request.provider or ai_service.get_default_provider()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/analyze")
async def analyze_document(
    request: AnalyzeRequest,
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """Analyze document content"""
    try:
        result = await ai_service.analyze_document(
            content=request.content,
            analysis_type=request.analysis_type,
            provider=request.provider
        )
        return {"analysis": result, "type": request.analysis_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/extract-document")
async def extract_from_document(
    file: UploadFile = File(...),
    provider: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("use:ai"))
):
    """Extract data from uploaded document"""
    content = await file.read()
    filename = file.filename.lower()

    # Extract text based on file type
    try:
        if filename.endswith('.txt'):
            text_content = content.decode('utf-8')

        elif filename.endswith(('.xlsx', '.xls')):
            import pandas as pd
            xl = pd.ExcelFile(BytesIO(content))
            text_parts = []
            records = []
            for sheet in xl.sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet)
                df = df.dropna(how='all')
                if not df.empty:
                    text_parts.append(f"Sheet: {sheet}\n{df.to_string()}")
                    records.extend(df.to_dict('records'))
            text_content = "\n\n".join(text_parts)

        elif filename.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(BytesIO(content))
            text_content = df.to_string()
            records = df.to_dict('records')

        elif filename.endswith('.pdf'):
            import pdfplumber
            with pdfplumber.open(BytesIO(content)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
                text_content = "\n\n".join(pages)

        elif filename.endswith(('.doc', '.docx')):
            from docx import Document
            doc = Document(BytesIO(content))
            text_content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Use AI to extract and categorize data
        extracted = await ai_service.extract_data(text_content[:8000], provider)

        # Add IDs
        for i, item in enumerate(extracted):
            item["id"] = str(i + 1)

        # Count by category
        categories = {}
        for item in extracted:
            cat = item.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "items": extracted,
            "summary": f"Extracted {len(extracted)} items from {file.filename}",
            "totalItems": len(extracted),
            "categories": categories
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/providers/{provider_id}")
async def configure_provider(
    provider_id: str,
    config: ProviderConfig,
    current_user: TokenData = Depends(require_permission("admin:ai"))
):
    """Configure AI provider"""
    if provider_id not in ["openai", "anthropic", "google"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    if config.enabled and config.api_key:
        ai_service.add_provider(provider_id, config.api_key, config.model)
        return {"message": f"Provider {provider_id} configured successfully"}
    else:
        if provider_id in ai_service.providers:
            del ai_service.providers[provider_id]
        return {"message": f"Provider {provider_id} disabled"}


@router.get("/providers")
async def list_providers(current_user: TokenData = Depends(get_current_user)):
    """List available AI providers"""
    providers = []
    for pid in ["openai", "anthropic", "google"]:
        providers.append({
            "id": pid,
            "name": pid.title(),
            "enabled": pid in ai_service.providers,
            "is_default": pid == ai_service.get_default_provider()
        })
    return {"providers": providers}
