import re
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.api.schemas.enums import TemplateFieldType, TemplateStatus, TextAlign

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_FORM_TYPE = re.compile(r"^[a-z0-9_-]+$")


# ---------------------------------------------------------------------------
# Contract Layer 6 schemas (contracts/schemas/template.yaml)
# ---------------------------------------------------------------------------
class TemplateFieldLayout(BaseModel):
    """Visual placement of a field on the PDF (schemas/template.yaml#/TemplateFieldLayout).

    Coordinates are PDF points with the origin at the bottom-left of the page:
    box = start (x, y) .. end (x + width, y + height).
    """

    page: int = Field(ge=0, description="Zero-based page index")
    x: float = Field(ge=0, description="Lower-left X in PDF points")
    y: float = Field(ge=0, description="Lower-left Y in PDF points (origin bottom-left)")
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    font: str = "Helvetica"
    font_size: float = Field(default=10, gt=0)
    color: str = "#000000"
    align: TextAlign = TextAlign.left

    @field_validator("font")
    @classmethod
    def _font_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("font must not be blank")
        return v

    @field_validator("color")
    @classmethod
    def _color_is_hex(cls, v: str) -> str:
        if not _HEX_COLOR.match(v):
            raise ValueError('color must be a hex string like "#000000"')
        return v


class TemplateField(BaseModel):
    """One field definition within a template (schemas/template.yaml#/TemplateField).

    A field draws its value from either `incident_mapping` (data binding) or
    `static_text` (fixed text) — exactly one. `layout` places it on the PDF.
    """

    field_name: str
    field_type: TemplateFieldType
    required: bool
    description: str | None = None
    max_length: int | None = Field(default=None, gt=0)
    min_value: float | None = Field(default=None, gt=0)
    max_value: float | None = Field(default=None, gt=0)
    allowed_values: list[str] | None = None
    incident_mapping: str | None = None
    static_text: str | None = None
    default_value: object | None = None
    layout: TemplateFieldLayout | None = None

    @field_validator("field_name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field_name must not be empty")
        return v

    @model_validator(mode="after")
    def _check_field(self) -> "TemplateField":
        has_mapping = bool(self.incident_mapping and self.incident_mapping.strip())
        has_static = self.static_text is not None
        if has_mapping and has_static:
            raise ValueError(
                f"field '{self.field_name}': set only one of incident_mapping or static_text"
            )
        if not has_mapping and not has_static:
            raise ValueError(
                f"field '{self.field_name}': one of incident_mapping or static_text is required"
            )
        if self.field_type == TemplateFieldType.enum and not self.allowed_values:
            raise ValueError(
                f"field '{self.field_name}': allowed_values is required when field_type is 'enum'"
            )
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"field '{self.field_name}': min_value must be <= max_value"
            )
        return self


class CreateTemplateRequest(BaseModel):
    """POST/PUT request body (schemas/template.yaml#/CreateTemplateRequest)."""

    form_type: str
    display_name: str
    jurisdiction: str | None = None
    agency_type: str | None = None
    fields: list[TemplateField] = Field(min_length=1)
    source_standard: str | None = None
    pdf_template_ref: str | None = None

    @field_validator("form_type")
    @classmethod
    def _form_type_slug(cls, v: str) -> str:
        v = v.strip()
        if not _FORM_TYPE.match(v):
            raise ValueError(
                "form_type must contain only lowercase letters, digits, underscores or hyphens"
            )
        return v

    @field_validator("display_name")
    @classmethod
    def _display_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("display_name must not be empty")
        return v

    @model_validator(mode="after")
    def _unique_field_names(self) -> "CreateTemplateRequest":
        names = [f.field_name for f in self.fields]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise ValueError(f"duplicate field_name(s): {', '.join(dupes)}")
        return self


class TemplateSummary(BaseModel):
    """List item (schemas/template.yaml#/TemplateSummary)."""

    template_id: UUID
    form_type: str
    display_name: str
    jurisdiction: str | None = None
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
    """GET /templates/{id}/fields response (path/templates.yaml#/template_fields)."""

    template_id: UUID
    form_type: str
    total_fields: int
    required_fields: int
    optional_fields: int
    fields: list[TemplateField]
