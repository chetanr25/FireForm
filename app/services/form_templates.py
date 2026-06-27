"""Business logic for the contract Layer 6 template registry.

Sits between the route handlers (app/api/routes/form_templates.py) and the
repositories. No FastAPI imports here — handlers do HTTP, this does the work:
validation/conflict checks, ORM construction, and ORM -> response mapping
(including the derived `field_count` / `last_updated`).
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session

from app.api.schemas.templates import (
    CreateTemplateRequest,
    TemplateDetail,
    TemplateField,
    TemplateFieldsResponse,
    TemplateSummary,
)
from app.core.errors.base import AppError
from app.db.repositories import (
    create_form_template,
    get_form_template,
    get_form_template_by_form_type,
    list_form_templates,
    update_form_template,
)
from app.models import FormTemplate


# ---------------------------------------------------------------------------
# Mapping helpers (ORM -> response schema). field_count / last_updated are
# derived here rather than stored on the model.
# ---------------------------------------------------------------------------
def _field_count(template: FormTemplate) -> int:
    return len(template.fields or [])


def _to_summary(template: FormTemplate) -> TemplateSummary:
    return TemplateSummary(
        template_id=template.template_id,
        form_type=template.form_type,
        display_name=template.display_name,
        jurisdiction=template.jurisdiction,
        agency_type=template.agency_type,
        version=template.version,
        last_updated=template.updated_at.date(),
        field_count=_field_count(template),
        status=template.status,
    )


def _to_detail(template: FormTemplate) -> TemplateDetail:
    return TemplateDetail(
        template_id=template.template_id,
        form_type=template.form_type,
        display_name=template.display_name,
        jurisdiction=template.jurisdiction,
        agency_type=template.agency_type,
        fields=template.fields,
        field_mappings_from_incident=template.field_mappings_from_incident,
        source_standard=template.source_standard,
        pdf_template_ref=template.pdf_template_ref,
        version=template.version,
        last_updated=template.updated_at.date(),
        field_count=_field_count(template),
        status=template.status,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _require_template(db: Session, template_id: UUID) -> FormTemplate:
    template = get_form_template(db, template_id)
    if not template:
        raise AppError(
            f"Template {template_id} not found",
            status_code=404,
            error_code="TEMPLATE_NOT_FOUND",
        )
    return template


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------
def list_templates(db: Session) -> list[TemplateSummary]:
    return [_to_summary(t) for t in list_form_templates(db)]


def create_template(db: Session, body: CreateTemplateRequest) -> TemplateDetail:
    if get_form_template_by_form_type(db, body.form_type):
        raise AppError(
            f"Template with form_type '{body.form_type}' already exists",
            status_code=409,
            error_code="TEMPLATE_EXISTS",
        )

    template = FormTemplate(
        form_type=body.form_type,
        display_name=body.display_name,
        jurisdiction=body.jurisdiction,
        agency_type=body.agency_type,
        fields=[f.model_dump() for f in body.fields],
        field_mappings_from_incident=body.field_mappings_from_incident,
        source_standard=body.source_standard,
        pdf_template_ref=body.pdf_template_ref,
    )
    return _to_detail(create_form_template(db, template))


def get_template(db: Session, template_id: UUID) -> TemplateDetail:
    return _to_detail(_require_template(db, template_id))


def replace_template(
    db: Session, template_id: UUID, body: CreateTemplateRequest
) -> TemplateDetail:
    template = _require_template(db, template_id)

    # Contract defines a 409 TEMPLATE_IN_USE when submitted incidents reference
    # this template. The contract forms/incidents layers tie records to
    # extract_id + form_type, never template_id, so there is no linkage to query
    # yet. Once a form_type<->submission link exists, gate the update here.
    # TODO(contract): enforce 409 TEMPLATE_IN_USE.

    template.form_type = body.form_type
    template.display_name = body.display_name
    template.jurisdiction = body.jurisdiction
    template.agency_type = body.agency_type
    template.fields = [f.model_dump() for f in body.fields]
    template.field_mappings_from_incident = body.field_mappings_from_incident
    template.source_standard = body.source_standard
    template.pdf_template_ref = body.pdf_template_ref
    template.updated_at = datetime.now(timezone.utc)
    return _to_detail(update_form_template(db, template))


def get_template_fields(
    db: Session, template_id: UUID, required_only: bool
) -> TemplateFieldsResponse:
    template = _require_template(db, template_id)

    fields = [TemplateField(**f) for f in template.fields]
    required = [f for f in fields if f.required]
    selected = required if required_only else fields

    return TemplateFieldsResponse(
        template_id=template.template_id,
        form_type=template.form_type,
        total_fields=len(fields),
        required_fields=len(required),
        optional_fields=len(fields) - len(required),
        fields=selected,
    )
