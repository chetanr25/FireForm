"""Contract Layer 6 template registry endpoints (contracts/path/templates.yaml).

Serves the form-template registry at /api/v1/templates, backed by the
UUID-keyed `FormTemplate` model. Handlers are thin — business logic lives in
app/services/form_templates.py. The legacy prototype template routes (upload /
create / make-fillable / preview / delete) were removed in the contract
migration; the legacy int-PK `Template` model survives only as the lookup target
of the fill pipeline (forms.py / jobs.py / tasks/fill.py).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_db
from app.api.schemas.templates import (
    CreateTemplateRequest,
    TemplateDetail,
    TemplateFieldsResponse,
    TemplateSummary,
)
from app.services import form_templates as service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateSummary])
def list_templates(db: Session = Depends(get_db)):
    return service.list_templates(db)


@router.post("", response_model=TemplateDetail, status_code=201)
def create_template(body: CreateTemplateRequest, db: Session = Depends(get_db)):
    return service.create_template(db, body)


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: UUID, db: Session = Depends(get_db)):
    return service.get_template(db, template_id)


@router.put("/{template_id}", response_model=TemplateDetail)
def replace_template(
    template_id: UUID, body: CreateTemplateRequest, db: Session = Depends(get_db)
):
    return service.replace_template(db, template_id, body)


@router.get("/{template_id}/fields", response_model=TemplateFieldsResponse)
def get_template_fields(
    template_id: UUID,
    required_only: bool = Query(False, description="Return only required fields"),
    db: Session = Depends(get_db),
):
    return service.get_template_fields(db, template_id, required_only)
