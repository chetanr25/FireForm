from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.schemas.enums import TemplateFieldType, TemplateStatus


# ---------------------------------------------------------------------------
# Contract Layer 6 schemas (contracts/schemas/template.yaml)
# ---------------------------------------------------------------------------
class TemplateField(BaseModel):
    """One field definition within a template (schemas/template.yaml#/TemplateField)."""

    field_name: str
    field_type: TemplateFieldType
    required: bool
    description: str | None = None
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: list[str] | None = None
    incident_mapping: str | None = None
    default_value: object | None = None


class CreateTemplateRequest(BaseModel):
    """POST/PUT request body (schemas/template.yaml#/CreateTemplateRequest)."""

    form_type: str
    display_name: str
    jurisdiction: str
    agency_type: str | None = None
    fields: list[TemplateField]
    field_mappings_from_incident: dict[str, str]
    source_standard: str | None = None
    pdf_template_ref: str | None = None


class TemplateSummary(BaseModel):
    """List item (schemas/template.yaml#/TemplateSummary)."""

    template_id: UUID
    form_type: str
    display_name: str
    jurisdiction: str
    agency_type: str | None = None
    version: str
    last_updated: date
    field_count: int
    status: TemplateStatus


class TemplateDetail(CreateTemplateRequest):
    """Full template definition (schemas/template.yaml#/Template).

    Server-generated fields layered on top of CreateTemplateRequest.
    """

    template_id: UUID
    version: str
    last_updated: date
    field_count: int
    status: TemplateStatus
    created_at: datetime
    updated_at: datetime


class TemplateFieldsResponse(BaseModel):
    """GET /templates/{id}/fields response (path/templates.yaml#L226-L244)."""

    template_id: UUID
    form_type: str
    total_fields: int
    required_fields: int
    optional_fields: int
    fields: list[TemplateField]
