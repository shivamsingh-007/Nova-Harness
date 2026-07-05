from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class EnvironmentType(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigScope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    RUN = "run"
    TASK = "task"
    AGENT = "agent"
    TOOL = "tool"


class ConfigSourceType(str, Enum):
    DEFAULT = "default"
    ENV_VAR = "env_var"
    FILE = "file"
    SECRET = "secret"
    CLI = "cli"
    REMOTE = "remote"


class SecretStorageType(str, Enum):
    ENV_VAR = "env_var"
    VAULT = "vault"
    SECRET_MANAGER = "secret_manager"
    KMS = "kms"
    FILE = "file"
    UNKNOWN = "unknown"


class ConfigKeyRef(BaseModel):
    key: str
    scope: ConfigScope
    source: ConfigSourceType
    required: bool = True
    description: Optional[str] = None

    @field_validator("key")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("key must not be blank")
        return stripped


class SecretRef(BaseModel):
    secret_id: str
    name: str
    storage_type: SecretStorageType
    required: bool = True
    source_hint: Optional[str] = None
    description: Optional[str] = None

    @field_validator("secret_id", "name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class RuntimeSettingRef(BaseModel):
    setting_id: str
    key_ref: ConfigKeyRef
    secret_ref: Optional[SecretRef] = None
    value_type: str
    default_value: Optional[str] = None
    sensitive: bool = False

    @field_validator("setting_id", "value_type")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def sensitive_masks_default(self):
        if self.sensitive and self.default_value is not None:
            raise ValueError("sensitive settings must not carry a default_value")
        return self

    def masked_repr(self) -> str:
        if self.sensitive:
            return f"RuntimeSettingRef(setting_id={self.setting_id}, value_type={self.value_type}, sensitive=True)"
        return repr(self)


class EnvironmentProfile(BaseModel):
    environment: EnvironmentType
    profile_id: str
    name: str
    description: Optional[str] = None
    config_keys: List[ConfigKeyRef] = Field(default_factory=list)
    secrets: List[SecretRef] = Field(default_factory=list)
    runtime_settings: List[RuntimeSettingRef] = Field(default_factory=list)

    @field_validator("profile_id", "name")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def no_duplicate_config_keys(self):
        seen = set()
        for ck in self.config_keys:
            if ck.key in seen:
                raise ValueError(f"duplicate config key: {ck.key}")
            seen.add(ck.key)
        return self

    @model_validator(mode="after")
    def no_duplicate_secret_names(self):
        seen = set()
        for s in self.secrets:
            if s.name in seen:
                raise ValueError(f"duplicate secret name: {s.name}")
            seen.add(s.name)
        return self

    @model_validator(mode="after")
    def settings_map_to_declared_keys(self):
        declared = {ck.key for ck in self.config_keys}
        for rs in self.runtime_settings:
            if rs.key_ref.key not in declared:
                raise ValueError(
                    f"runtime setting {rs.setting_id} references undeclared key: {rs.key_ref.key}"
                )
        return self


class ConfigBundle(BaseModel):
    bundle_id: str
    profile: EnvironmentProfile
    values: Dict[str, str] = Field(default_factory=dict)

    @field_validator("bundle_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("bundle_id must not be blank")
        return stripped

    @model_validator(mode="after")
    def required_keys_present(self):
        for ck in self.profile.config_keys:
            if ck.required and ck.key not in self.values:
                raise ValueError(f"required config key missing from values: {ck.key}")
        return self

    @model_validator(mode="after")
    def defaults_not_override_required_secrets(self):
        for rs in self.profile.runtime_settings:
            if rs.secret_ref is not None and rs.secret_ref.required and rs.key_ref.key in self.values:
                decl = self.profile.config_keys
                ck = next((c for c in decl if c.key == rs.key_ref.key), None)
                if ck and ck.source == ConfigSourceType.SECRET and not rs.sensitive:
                    raise ValueError(
                        f"default must not silently override required secret: {rs.key_ref.key}"
                    )
        return self


class SecretsManifest(BaseModel):
    manifest_id: str
    profile_id: str
    secrets: List[SecretRef] = Field(default_factory=list)

    @field_validator("manifest_id", "profile_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def no_duplicate_secret_names(self):
        seen = set()
        for s in self.secrets:
            if s.name in seen:
                raise ValueError(f"duplicate secret name in manifest: {s.name}")
            seen.add(s.name)
        return self

    @model_validator(mode="after")
    def required_secrets_declared(self):
        for s in self.secrets:
            if s.required:
                pass
        return self


class EnvironmentContractEnvelope(BaseModel):
    envelope_id: str
    bundle: ConfigBundle
    secrets_manifest: SecretsManifest

    @field_validator("envelope_id")
    @classmethod
    def non_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("envelope_id must not be blank")
        return stripped

    @model_validator(mode="after")
    def manifest_profile_matches(self):
        if self.secrets_manifest.profile_id != self.bundle.profile.profile_id:
            raise ValueError(
                "secrets_manifest.profile_id must match bundle.profile.profile_id"
            )
        return self
