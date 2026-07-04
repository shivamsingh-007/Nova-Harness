import pytest
from pydantic import ValidationError
from models.execution_environment import (
    EnvironmentDefinition,
    FilesystemPolicy,
    NetworkPolicy,
    ResourceLimits,
    SecretPolicy,
    LifecyclePolicy,
    AuditPolicy,
    EnvironmentProvider,
    NetworkMode,
    SecretAccessMode,
    LifecycleMode,
)


def make_valid_env(**overrides) -> EnvironmentDefinition:
    defaults = dict(
        environment_id="env-001",
        provider=EnvironmentProvider.DOCKER,
        filesystem=FilesystemPolicy(
            workspace_root="/workspace",
            writable_paths=["/workspace/src"],
            read_only_paths=["/workspace/.venv"],
            blocked_paths=["/workspace/secrets"],
        ),
        network=NetworkPolicy(),
        resources=ResourceLimits(),
        secrets=SecretPolicy(),
        lifecycle=LifecyclePolicy(),
        audit=AuditPolicy(),
    )
    defaults.update(overrides)
    return EnvironmentDefinition(**defaults)


class TestFilesystemPolicy:
    def test_valid_filesystem(self):
        fs = FilesystemPolicy(
            workspace_root="/workspace",
            writable_paths=["/workspace/src"],
            read_only_paths=["/workspace/.venv"],
        )
        assert fs.workspace_root == "/workspace"

    def test_empty_root_raises(self):
        with pytest.raises(ValidationError) as exc:
            FilesystemPolicy(workspace_root="")
        assert "workspace_root must not be empty" in str(exc.value)

    def test_writable_read_only_overlap_raises(self):
        with pytest.raises(ValidationError) as exc:
            FilesystemPolicy(
                workspace_root="/ws",
                writable_paths=["/ws/src"],
                read_only_paths=["/ws/src"],
            )
        assert "writable_paths and read_only_paths overlap" in str(exc.value)

    def test_writable_blocked_overlap_raises(self):
        with pytest.raises(ValidationError) as exc:
            FilesystemPolicy(
                workspace_root="/ws",
                writable_paths=["/ws/src"],
                blocked_paths=["/ws/src"],
            )
        assert "writable_paths and blocked_paths overlap" in str(exc.value)

    def test_read_only_blocked_overlap_raises(self):
        with pytest.raises(ValidationError) as exc:
            FilesystemPolicy(
                workspace_root="/ws",
                read_only_paths=["/ws/config"],
                blocked_paths=["/ws/config"],
            )
        assert "read_only_paths and blocked_paths overlap" in str(exc.value)


class TestNetworkPolicy:
    def test_default_disabled(self):
        np = NetworkPolicy()
        assert np.mode == NetworkMode.DISABLED
        assert np.allowed_hosts == []

    def test_allowlist_requires_hosts(self):
        with pytest.raises(ValidationError) as exc:
            NetworkPolicy(mode=NetworkMode.ALLOWLIST)
        assert "ALLOWLIST mode requires at least one allowed_host" in str(exc.value)

    def test_allowlist_with_hosts(self):
        np = NetworkPolicy(mode=NetworkMode.ALLOWLIST, allowed_hosts=["pypi.org"])
        assert np.mode == NetworkMode.ALLOWLIST

    def test_disabled_forbids_hosts(self):
        with pytest.raises(ValidationError) as exc:
            NetworkPolicy(mode=NetworkMode.DISABLED, allowed_hosts=["pypi.org"])
        assert "DISABLED mode must not specify allowed_hosts" in str(exc.value)

    def test_full_network_allows_any_hosts(self):
        np = NetworkPolicy(mode=NetworkMode.FULL)
        assert np.mode == NetworkMode.FULL


class TestResourceLimits:
    def test_defaults(self):
        rl = ResourceLimits()
        assert rl.max_cpu_cores == 2.0
        assert rl.max_memory_mb == 2048

    def test_positive_limits(self):
        with pytest.raises(ValidationError):
            ResourceLimits(max_cpu_cores=0)
        with pytest.raises(ValidationError):
            ResourceLimits(max_memory_mb=-1)


class TestSecretPolicy:
    def test_default_none(self):
        sp = SecretPolicy()
        assert sp.access_mode == SecretAccessMode.NONE

    def test_explicit_with_names(self):
        sp = SecretPolicy(access_mode=SecretAccessMode.EXPLICIT, allowed_secret_names=["API_KEY"])
        assert sp.allowed_secret_names == ["API_KEY"]

    def test_none_forbids_names(self):
        with pytest.raises(ValidationError) as exc:
            SecretPolicy(access_mode=SecretAccessMode.NONE, allowed_secret_names=["API_KEY"])
        assert "NONE access mode must not specify allowed_secret_names" in str(exc.value)


class TestLifecyclePolicy:
    def test_default_ephemeral_with_ttl(self):
        lp = LifecyclePolicy()
        assert lp.mode == LifecycleMode.EPHEMERAL
        assert lp.ttl_seconds == 1800

    def test_persistent_no_ttl_restriction(self):
        lp = LifecyclePolicy(mode=LifecycleMode.PERSISTENT, ttl_seconds=3600)
        assert lp.mode == LifecycleMode.PERSISTENT

    def test_ephemeral_needs_positive_ttl(self):
        with pytest.raises(ValidationError) as exc:
            LifecyclePolicy(mode=LifecycleMode.EPHEMERAL, ttl_seconds=0)
        assert "ttl_seconds must be positive" in str(exc.value)

    def test_ephemeral_needs_positive_ttl_negative(self):
        with pytest.raises(ValidationError):
            LifecyclePolicy(mode=LifecycleMode.EPHEMERAL, ttl_seconds=-1)


class TestEnvironmentDefinition:
    def test_valid_docker_env(self):
        env = make_valid_env()
        assert env.environment_id == "env-001"
        assert env.provider == EnvironmentProvider.DOCKER
        assert env.network.mode == NetworkMode.DISABLED
        assert env.secrets.access_mode == SecretAccessMode.NONE
        assert env.lifecycle.mode == LifecycleMode.EPHEMERAL
        assert env.audit.log_tool_calls is True

    def test_valid_e2b_env(self):
        env = make_valid_env(
            environment_id="env-002",
            provider=EnvironmentProvider.E2B,
            network=NetworkPolicy(mode=NetworkMode.ALLOWLIST, allowed_hosts=["api.github.com"]),
            secrets=SecretPolicy(access_mode=SecretAccessMode.EXPLICIT, allowed_secret_names=["GH_TOKEN"]),
        )
        assert env.provider == EnvironmentProvider.E2B
        assert env.network.allowed_hosts == ["api.github.com"]
        assert env.secrets.allowed_secret_names == ["GH_TOKEN"]

    def test_valid_local_debug_env(self):
        env = make_valid_env(
            environment_id="env-debug",
            provider=EnvironmentProvider.LOCAL,
            lifecycle=LifecyclePolicy(mode=LifecycleMode.PERSISTENT),
        )
        assert env.provider == EnvironmentProvider.LOCAL
        assert env.lifecycle.mode == LifecycleMode.PERSISTENT

    def test_empty_id_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_valid_env(environment_id="")
        assert "environment_id must not be empty" in str(exc.value)

    def test_audit_defaults(self):
        env = make_valid_env()
        assert env.audit.capture_stdout_stderr is True
        assert env.audit.capture_fs_diff is True


class TestDefaults:
    def test_resource_defaults(self):
        rl = ResourceLimits()
        assert rl.max_cpu_cores == 2.0
        assert rl.max_memory_mb == 2048
        assert rl.max_disk_mb == 4096
        assert rl.max_runtime_seconds == 600
        assert rl.max_process_count == 20

    def test_lifecycle_defaults(self):
        lp = LifecyclePolicy()
        assert lp.mode == LifecycleMode.EPHEMERAL
        assert lp.ttl_seconds == 1800
        assert lp.preserve_on_failure is True

    def test_audit_defaults(self):
        ap = AuditPolicy()
        assert ap.log_tool_calls is True
        assert ap.log_resource_usage is True
        assert ap.capture_stdout_stderr is True
        assert ap.capture_fs_diff is True


class TestSerialization:
    def test_env_definition_serialize(self):
        env = make_valid_env()
        data = env.model_dump()
        assert data["environment_id"] == "env-001"
        assert data["provider"] == "docker"
        assert data["filesystem"]["workspace_root"] == "/workspace"
        assert data["network"]["mode"] == "disabled"
