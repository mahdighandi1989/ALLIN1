"""AI providers, models, and task-routing admin API.

Backs the "AI models & providers" section of the Settings page. Reads are open
to any signed-in user; all mutations are admin-only and audited. API keys are
never returned in full — only a masked hint and a "configured" flag.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import ai_manager
from app.ai import catalog
from app.database import get_db
from app.models.ai_config import (
    AIModel,
    AIProvider,
    AITaskRoute,
    ModelCreate,
    ModelUpdate,
    ProviderUpdate,
    TaskRouteUpdate,
)
from app.routers.auth import get_current_active_user, require_admin
from app.services.audit import record_audit

router = APIRouter(tags=["ai"])


async def _overview(db: AsyncSession) -> Dict[str, Any]:
    """Everything the Settings UI needs in one payload."""
    providers = (await db.execute(select(AIProvider))).scalars().all()
    models = (
        await db.execute(select(AIModel).order_by(AIModel.priority, AIModel.display_name))
    ).scalars().all()
    routes = (await db.execute(select(AITaskRoute))).scalars().all()

    return {
        "providers": [
            p.to_dict(env_configured=ai_manager.provider_configured(p)) for p in providers
        ],
        "models": [m.to_dict() for m in models],
        "routes": [r.to_dict() for r in routes],
        "tasks": catalog.TASK_TYPES,
        "capabilities": catalog.CAPABILITIES,
        "status": await ai_manager.status(db),
    }


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_active_user),
):
    return await _overview(db)


@router.put("/providers/{key}")
async def update_provider(
    key: str,
    payload: ProviderUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    provider = await db.get(AIProvider, key)
    if provider is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {key}")

    if payload.enabled is not None:
        provider.enabled = payload.enabled
    if payload.base_url is not None:
        provider.base_url = payload.base_url.strip() or None
    if payload.notes is not None:
        provider.notes = payload.notes
    # api_key: omitted = leave as-is; "" = clear; value = set. Never logged.
    if payload.api_key is not None:
        provider.api_key = payload.api_key.strip() or None

    await db.commit()
    await record_audit(
        action="update", entity_type="ai_provider", entity_id=key,
        detail=f"Updated AI provider {key} (enabled={provider.enabled})",
        user=actor, request=request, db=db,
    )
    await db.refresh(provider)
    return provider.to_dict(env_configured=ai_manager.provider_configured(provider))


@router.post("/models")
async def create_model(
    payload: ModelCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    provider = await db.get(AIProvider, payload.provider_key)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {payload.provider_key}")

    model_key = payload.model_key.strip()
    if not model_key:
        raise HTTPException(status_code=422, detail="model_key is required")
    existing = (
        await db.execute(select(AIModel).where(AIModel.model_key == model_key))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Model already exists: {model_key}")

    valid_caps = {c["id"] for c in catalog.CAPABILITIES}
    caps = [c for c in payload.capabilities if c in valid_caps]

    model = AIModel(
        model_key=model_key,
        provider_key=payload.provider_key,
        display_name=(payload.display_name or model_key).strip(),
        enabled=True,
        capabilities=caps,
        max_output_tokens=payload.max_output_tokens,
        context_window=payload.context_window,
        temperature=payload.temperature,
        priority=payload.priority,
        input_cost_per_1m=payload.input_cost_per_1m,
        output_cost_per_1m=payload.output_cost_per_1m,
        source="custom",
        is_custom=True,
        notes=payload.notes,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    await record_audit(
        action="create", entity_type="ai_model", entity_id=model_key,
        detail=f"Added custom AI model {model_key} ({payload.provider_key})",
        user=actor, request=request, db=db,
    )
    return model.to_dict()


@router.put("/models/{model_id}")
async def update_model(
    model_id: int,
    payload: ModelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    model = await db.get(AIModel, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    data = payload.model_dump(exclude_unset=True)
    if "capabilities" in data and data["capabilities"] is not None:
        valid_caps = {c["id"] for c in catalog.CAPABILITIES}
        data["capabilities"] = [c for c in data["capabilities"] if c in valid_caps]
    for attr, value in data.items():
        setattr(model, attr, value)

    await db.commit()
    await db.refresh(model)
    await record_audit(
        action="update", entity_type="ai_model", entity_id=model.model_key,
        detail=f"Updated AI model {model.model_key} (enabled={model.enabled})",
        user=actor, request=request, db=db,
    )
    return model.to_dict()


@router.post("/providers/{key}/sync-models")
async def sync_provider_models_endpoint(
    key: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    """Pull the provider's current model list and reconcile it into the DB."""
    from app.ai.tester import sync_provider_models
    result = await sync_provider_models(db, key)
    if result.get("ok"):
        await record_audit(
            action="update", entity_type="ai_provider", entity_id=key,
            detail=(f"Synced models for {key}: +{result.get('added')} "
                    f"-{result.get('removed')} (total {result.get('total')})"),
            user=actor, request=request, db=db,
        )
    return result


@router.post("/models/{model_id}/test")
async def test_model_connection(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Make a tiny live request to verify the model's credential actually works."""
    from app.ai.tester import test_model
    return await test_model(db, model_id)


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    model = await db.get(AIModel, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    if not model.is_custom:
        # Catalog models are managed in code — disable instead of deleting, so a
        # re-seed doesn't silently bring them back.
        raise HTTPException(
            status_code=400,
            detail="Catalog models cannot be deleted; disable them instead.",
        )
    model_key = model.model_key
    await db.delete(model)
    await db.commit()
    await record_audit(
        action="delete", entity_type="ai_model", entity_id=model_key,
        detail=f"Deleted custom AI model {model_key}",
        user=actor, request=request, db=db,
    )
    return {"deleted": model_key}


@router.put("/routes/{task}")
async def update_route(
    task: str,
    payload: TaskRouteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor=Depends(require_admin),
):
    if task not in {t["id"] for t in catalog.TASK_TYPES}:
        raise HTTPException(status_code=404, detail=f"Unknown task: {task}")

    route = await db.get(AITaskRoute, task)
    if route is None:
        route = AITaskRoute(task=task)
        db.add(route)

    data = payload.model_dump(exclude_unset=True)
    if "model_id" in data and data["model_id"] is not None:
        if (await db.get(AIModel, data["model_id"])) is None:
            raise HTTPException(status_code=400, detail="model_id does not exist")
    for attr, value in data.items():
        setattr(route, attr, value)

    await db.commit()
    await db.refresh(route)
    await record_audit(
        action="update", entity_type="ai_route", entity_id=task,
        detail=f"Routed AI task {task} -> model_id={route.model_id}",
        user=actor, request=request, db=db,
    )
    return route.to_dict()
