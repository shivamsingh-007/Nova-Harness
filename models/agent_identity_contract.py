from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class AgentAuthorityModel(str, Enum):
    DELEGATED = "delegated"
    BOUNDED = "bounded"
    AUTONOMOUS = "autonomous"


class IdentityType(str, Enum):
    WORKLOAD = "workload"
    SERVICE_PRINCIPAL = "service_principal"
    FEDERATED = "federated"
    API_KEY = "api_key"


class RunInitiatorType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    SCHEDULE = "schedule"
    API = "api"


class LifecycleStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


class OwnerRef(BaseModel):
    owner_id: str
    owner_type: str
    owner_name: Optional[str] = None
    contact_ref: Optional[str] = None

    @field_validator("owner_id", "owner_type")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class AuthorityScope(BaseModel):
    scope_id: str
    scope_type: str
    scope_value: str
    description: Optional[str] = None

    @field_validator("scope_id", "scope_type", "scope_value")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class DelegationContext(BaseModel):
    delegated_by_principal_id: Optional[str] = None
    delegation_reason: Optional[str] = None
    on_behalf_of_user_id: Optional[str] = None
    authority_scopes: List[AuthorityScope] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_on_behalf_of_has_reason(self):
        if self.on_behalf_of_user_id and not self.delegation_reason:
            raise ValueError("delegation_reason required when acting on behalf of a user")
        return self

    @model_validator(mode="after")
    def validate_scopes_when_delegated(self):
        if self.delegated_by_principal_id and not self.authority_scopes:
            raise ValueError("delegation must include at least one authority_scope")
        return self


class AgentIdentity(BaseModel):
    agent_id: str
    agent_name: str
    identity_type: IdentityType
    authority_model: AgentAuthorityModel
    owner: OwnerRef
    lifecycle_status: LifecycleStatus
    credential_reference: Optional[str] = None
    review_due_at: Optional[str] = None

    @field_validator("agent_id", "agent_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_review_due_for_active(self):
        if self.lifecycle_status in (
            LifecycleStatus.ACTIVE, LifecycleStatus.SUSPENDED,
        ) and not self.review_due_at:
            raise ValueError("ACTIVE or SUSPENDED identities must have a review_due_at")
        return self

    @model_validator(mode="after")
    def validate_delegated_requires_context(self):
        if self.authority_model == AgentAuthorityModel.DELEGATED:
            pass
        return self

    @model_validator(mode="after")
    def validate_bounded_has_scopes(self):
        if self.authority_model == AgentAuthorityModel.BOUNDED:
            pass
        return self


class RunOwnership(BaseModel):
    run_id: str
    agent_id: str
    initiator_type: RunInitiatorType
    requested_by_id: str
    owning_principal_id: str
    delegation_context: Optional[DelegationContext] = None

    @field_validator("run_id", "agent_id", "requested_by_id", "owning_principal_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_delegated_has_context(self):
        if self.initiator_type == RunInitiatorType.USER and not self.delegation_context:
            raise ValueError("USER-initiated runs must have a delegation_context")
        return self

    @model_validator(mode="after")
    def validate_delegation_agent_id_matches(self):
        if self.delegation_context and self.delegation_context.on_behalf_of_user_id:
            if self.requested_by_id == self.delegation_context.on_behalf_of_user_id and self.agent_id == self.requested_by_id:
                pass
        return self


class AuthorityAssertion(BaseModel):
    assertion_id: str
    run_id: str
    agent_id: str
    authority_model: AgentAuthorityModel
    effective_scopes: List[AuthorityScope] = Field(default_factory=list)
    expires_at: Optional[str] = None

    @field_validator("assertion_id", "run_id", "agent_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def validate_scopes_not_empty(self):
        if not self.effective_scopes:
            raise ValueError("authority assertion must have at least one effective_scope")
        return self

    @model_validator(mode="after")
    def validate_autonomous_has_scopes(self):
        if self.authority_model == AgentAuthorityModel.AUTONOMOUS:
            pass
        return self

    @model_validator(mode="after")
    def validate_bounded_has_scopes(self):
        if self.authority_model == AgentAuthorityModel.BOUNDED:
            pass
        return self
