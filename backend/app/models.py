from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ValidationPolicy(BaseModel):
    required_keys: list[str] = Field(default_factory=lambda: ["model", "temperature", "timeout_ms"])
    forbidden_keys: list[str] = Field(default_factory=list)
    max_temperature: float = Field(default=1.2, ge=0.0, le=2.0)
    min_timeout_ms: int = Field(default=250, ge=1)
    max_timeout_ms: int = Field(default=60000, ge=1)


class ConfigCreate(BaseModel):
    service_name: str = Field(min_length=1, max_length=120, pattern=r"^[a-zA-Z0-9_.-]+$")
    environment: Literal["dev", "staging", "prod"]
    provider: Literal["openai", "azure-openai", "anthropic", "ollama", "custom"]
    parameters: dict[str, Any]
    policy: ValidationPolicy = Field(default_factory=ValidationPolicy)
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("parameters must not be empty")
        return value


class ConfigVersion(BaseModel):
    id: int
    service_name: str
    environment: str
    provider: str
    parameters: dict[str, Any]
    policy: ValidationPolicy
    notes: str | None
    status: Literal["draft", "validated", "rejected", "promoted"]
    created_at: str
    updated_at: str


class ValidationResult(BaseModel):
    config_id: int
    passed: bool
    issues: list[str]
    evaluated_at: str


class PromotionRequest(BaseModel):
    target_environment: Literal["staging", "production"]
    rollout_percent: int = Field(ge=1, le=100)
    change_ticket: str = Field(min_length=1, max_length=80)
    approved_by: str = Field(min_length=1, max_length=120)


class ReleaseRecord(BaseModel):
    id: int
    config_id: int
    target_environment: Literal["staging", "production"]
    rollout_percent: int
    change_ticket: str
    approved_by: str
    created_at: str
