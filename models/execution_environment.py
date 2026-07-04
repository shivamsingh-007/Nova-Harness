from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class EnvironmentProvider(str, Enum):
    DOCKER = "docker"
    E2B = "e2b"
    DAYTONA = "daytona"
    LOCAL = "local"


class NetworkMode(str, Enum):
    DISABLED = "disabled"
    ALLOWLIST = "allowlist"
    FULL = "full"


class SecretAccessMode(str, Enum):
    NONE = "none"
    EXPLICIT = "explicit"


class LifecycleMode(str, Enum):
    EPHEMERAL = "ephemeral"
    PERSISTENT = "persistent"


class FilesystemPolicy(BaseModel):
    workspace_root: str
    writable_paths: List[str] = Field(default_factory=list)
    read_only_paths: List[str] = Field(default_factory=list)
    blocked_paths: List[str] = Field(default_factory=list)

    @field_validator("workspace_root")
    @classmethod
    def non_empty_root(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("workspace_root must not be empty")
        return value

    @model_validator(mode="after")
    def validate_no_path_overlap(self):
        writable_set = set(self.writable_paths)
        if writable_set & set(self.read_only_paths):
            raise ValueError("writable_paths and read_only_paths overlap")
        if writable_set & set(self.blocked_paths):
            raise ValueError("writable_paths and blocked_paths overlap")
        if set(self.read_only_paths) & set(self.blocked_paths):
            raise ValueError("read_only_paths and blocked_paths overlap")
        return self


class NetworkPolicy(BaseModel):
    mode: NetworkMode = NetworkMode.DISABLED
    allowed_hosts: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_network_consistency(self):
        if self.mode == NetworkMode.ALLOWLIST and not self.allowed_hosts:
            raise ValueError("ALLOWLIST mode requires at least one allowed_host")
        if self.mode == NetworkMode.DISABLED and self.allowed_hosts:
            raise ValueError("DISABLED mode must not specify allowed_hosts")
        return self


class ResourceLimits(BaseModel):
    max_cpu_cores: float = 2.0
    max_memory_mb: int = 2048
    max_disk_mb: int = 4096
    max_runtime_seconds: int = 600
    max_process_count: int = 20

    @field_validator("max_cpu_cores", "max_memory_mb", "max_disk_mb", "max_runtime_seconds", "max_process_count")
    @classmethod
    def positive_limits(cls, value) -> float | int:
        if value <= 0:
            raise ValueError("resource limit must be positive")
        return value


class SecretPolicy(BaseModel):
    access_mode: SecretAccessMode = SecretAccessMode.NONE
    allowed_secret_names: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_secret_policy(self):
        if self.access_mode == SecretAccessMode.NONE and self.allowed_secret_names:
            raise ValueError("NONE access mode must not specify allowed_secret_names")
        return self


class LifecyclePolicy(BaseModel):
    mode: LifecycleMode = LifecycleMode.EPHEMERAL
    ttl_seconds: int = 1800
    preserve_on_failure: bool = True

    @field_validator("ttl_seconds")
    @classmethod
    def positive_ttl(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ttl_seconds must be positive")
        return value


class AuditPolicy(BaseModel):
    log_tool_calls: bool = True
    log_resource_usage: bool = True
    capture_stdout_stderr: bool = True
    capture_fs_diff: bool = True


class EnvironmentDefinition(BaseModel):
    environment_id: str
    provider: EnvironmentProvider
    filesystem: FilesystemPolicy
    network: NetworkPolicy
    resources: ResourceLimits
    secrets: SecretPolicy
    lifecycle: LifecyclePolicy
    audit: AuditPolicy

    @field_validator("environment_id")
    @classmethod
    def non_empty_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("environment_id must not be empty")
        return value
