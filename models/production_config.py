from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class DeploymentEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecretSource(str, Enum):
    ENV = "env"
    FILE = "file"
    VAULT = "vault"


class SecretReference(BaseModel):
    secret_name: str
    source: SecretSource
    reference: str
    required: bool = True
    allow_in_env_only: bool = False
    description: Optional[str] = None

    @field_validator("secret_name")
    @classmethod
    def validate_secret_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("secret_name must not be empty")
        return value

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reference must not be empty")
        return value


class ProviderConfig(BaseModel):
    provider_name: str
    model_name: str
    api_base: Optional[str] = None
    api_key_secret: Optional[SecretReference] = None
    timeout_seconds: int = 60
    max_retries: int = 2
    enabled: bool = True

    @field_validator("provider_name", "model_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value < 1:
            raise ValueError("timeout_seconds must be at least 1")
        return value

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_retries must be non-negative")
        return value


class RuntimeBudgetConfig(BaseModel):
    max_steps_per_run: int = 12
    max_tool_calls_per_run: int = 8
    max_runtime_seconds: int = 120
    max_cost_usd_per_run: float = 1.0

    @field_validator("max_steps_per_run", "max_tool_calls_per_run")
    @classmethod
    def validate_positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be at least 1")
        return value

    @field_validator("max_runtime_seconds")
    @classmethod
    def validate_positive_seconds(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_runtime_seconds must be at least 1")
        return value

    @field_validator("max_cost_usd_per_run")
    @classmethod
    def validate_positive_cost(cls, value: float) -> float:
        if value < 0:
            raise ValueError("max_cost_usd_per_run must be non-negative")
        return value


class TracingConfig(BaseModel):
    enabled: bool = True
    redact_sensitive_fields: bool = True
    store_prompt_bodies: bool = False
    store_tool_arguments: bool = False


class SecurityConfig(BaseModel):
    allowed_egress_hosts: List[str] = Field(default_factory=list)
    secrets_redaction_enabled: bool = True
    enforce_secret_scoping: bool = True
    require_approval_for_secret_access: bool = True


class AppConfig(BaseModel):
    environment: DeploymentEnvironment
    app_name: str
    provider: ProviderConfig
    runtime_budget: RuntimeBudgetConfig
    tracing: TracingConfig
    security: SecurityConfig

    @field_validator("app_name")
    @classmethod
    def validate_app_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("app_name must not be empty")
        return value

    @model_validator(mode="after")
    def validate_production_secret(self):
        if self.environment == DeploymentEnvironment.PRODUCTION:
            if self.provider.enabled and self.provider.api_key_secret is None:
                raise ValueError("production provider must have an api_key_secret")
            if self.tracing.store_prompt_bodies:
                raise ValueError("production must not store prompt bodies")
            if self.tracing.store_tool_arguments:
                raise ValueError("production must not store tool arguments")
        return self

    @model_validator(mode="after")
    def validate_production_egress(self):
        if self.environment == DeploymentEnvironment.PRODUCTION:
            if self.provider.enabled and self.provider.api_base is not None:
                pass
            if not self.security.allowed_egress_hosts:
                pass
        return self


class ResolvedSecret(BaseModel):
    secret_name: str
    resolved_from: SecretSource
    value_present: bool
    redacted_preview: str

    @field_validator("redacted_preview")
    @classmethod
    def validate_redacted_preview(cls, value: str) -> str:
        if not value.endswith("...") and len(value) < 10:
            raise ValueError("redacted_preview must be at least 10 characters or end with '...'")
        return value


class ResolvedRuntimeConfig(BaseModel):
    app_config: AppConfig
    resolved_secrets: List[ResolvedSecret] = Field(default_factory=list)


class ConfigValidationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
