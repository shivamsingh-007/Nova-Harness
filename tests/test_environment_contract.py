import pytest
from pydantic import ValidationError
from models.environment_contract import (
    EnvironmentType, ConfigScope, ConfigSourceType, SecretStorageType,
    ConfigKeyRef, SecretRef, RuntimeSettingRef, EnvironmentProfile,
    ConfigBundle, SecretsManifest, EnvironmentContractEnvelope,
)


def make_key(**overrides) -> ConfigKeyRef:
    defaults = dict(key="db_host", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR)
    defaults.update(overrides)
    return ConfigKeyRef(**defaults)


def make_secret(**overrides) -> SecretRef:
    defaults = dict(secret_id="sec-001", name="db_password", storage_type=SecretStorageType.ENV_VAR)
    defaults.update(overrides)
    return SecretRef(**defaults)


def make_setting(**overrides) -> RuntimeSettingRef:
    defaults = dict(setting_id="s-001", key_ref=make_key(), value_type="string")
    defaults.update(overrides)
    return RuntimeSettingRef(**defaults)


def make_profile(**overrides) -> EnvironmentProfile:
    defaults = dict(
        environment=EnvironmentType.LOCAL, profile_id="prof-local",
        name="Local Development",
    )
    defaults.update(overrides)
    return EnvironmentProfile(**defaults)


def make_bundle(**overrides) -> ConfigBundle:
    defaults = dict(bundle_id="bundle-001", profile=make_profile(), values={})
    defaults.update(overrides)
    return ConfigBundle(**defaults)


def make_manifest(**overrides) -> SecretsManifest:
    defaults = dict(manifest_id="manifest-001", profile_id="prof-local")
    defaults.update(overrides)
    return SecretsManifest(**defaults)


def make_envelope(**overrides) -> EnvironmentContractEnvelope:
    defaults = dict(envelope_id="env-001", bundle=make_bundle(), secrets_manifest=make_manifest())
    defaults.update(overrides)
    return EnvironmentContractEnvelope(**defaults)


class TestEnums:
    def test_environment_type_values(self):
        assert EnvironmentType.LOCAL.value == "local"
        assert EnvironmentType.DEV.value == "dev"
        assert EnvironmentType.TEST.value == "test"
        assert EnvironmentType.STAGING.value == "staging"
        assert EnvironmentType.PRODUCTION.value == "production"
        assert len(EnvironmentType) == 5

    def test_config_scope_values(self):
        assert ConfigScope.GLOBAL.value == "global"
        assert ConfigScope.PROJECT.value == "project"
        assert ConfigScope.RUN.value == "run"
        assert ConfigScope.TASK.value == "task"
        assert ConfigScope.AGENT.value == "agent"
        assert ConfigScope.TOOL.value == "tool"
        assert len(ConfigScope) == 6

    def test_config_source_type_values(self):
        assert ConfigSourceType.DEFAULT.value == "default"
        assert ConfigSourceType.ENV_VAR.value == "env_var"
        assert ConfigSourceType.FILE.value == "file"
        assert ConfigSourceType.SECRET.value == "secret"
        assert ConfigSourceType.CLI.value == "cli"
        assert ConfigSourceType.REMOTE.value == "remote"
        assert len(ConfigSourceType) == 6

    def test_secret_storage_type_values(self):
        assert SecretStorageType.ENV_VAR.value == "env_var"
        assert SecretStorageType.VAULT.value == "vault"
        assert SecretStorageType.SECRET_MANAGER.value == "secret_manager"
        assert SecretStorageType.KMS.value == "kms"
        assert SecretStorageType.FILE.value == "file"
        assert SecretStorageType.UNKNOWN.value == "unknown"
        assert len(SecretStorageType) == 6


class TestConfigKeyRef:
    def test_valid(self):
        k = make_key()
        assert k.key == "db_host"
        assert k.required is True

    def test_blank_key_raises(self):
        with pytest.raises(ValidationError):
            make_key(key="")

    def test_optional_key(self):
        k = make_key(required=False)
        assert k.required is False

    def test_with_description(self):
        k = make_key(description="Database hostname")
        assert k.description == "Database hostname"

    def test_all_scopes(self):
        for s in ConfigScope:
            k = make_key(scope=s)
            assert k.scope == s

    def test_all_sources(self):
        for s in ConfigSourceType:
            k = make_key(source=s)
            assert k.source == s


class TestSecretRef:
    def test_valid(self):
        s = make_secret()
        assert s.secret_id == "sec-001"
        assert s.name == "db_password"

    def test_blank_secret_id_raises(self):
        with pytest.raises(ValidationError):
            make_secret(secret_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_secret(name="")

    def test_with_source_hint(self):
        s = make_secret(source_hint="AWS_PROFILE")
        assert s.source_hint == "AWS_PROFILE"

    def test_optional_secret(self):
        s = make_secret(required=False)
        assert s.required is False

    def test_all_storage_types(self):
        for t in SecretStorageType:
            s = make_secret(storage_type=t)
            assert s.storage_type == t


class TestRuntimeSettingRef:
    def test_valid(self):
        s = make_setting()
        assert s.setting_id == "s-001"

    def test_blank_setting_id_raises(self):
        with pytest.raises(ValidationError):
            make_setting(setting_id="")

    def test_blank_value_type_raises(self):
        with pytest.raises(ValidationError):
            make_setting(value_type="")

    def test_with_default_value(self):
        s = make_setting(default_value="localhost")
        assert s.default_value == "localhost"

    def test_sensitive_true(self):
        s = make_setting(sensitive=True)
        assert s.sensitive is True

    def test_sensitive_with_default_value_raises(self):
        with pytest.raises(ValidationError, match="sensitive settings must not carry a default_value"):
            make_setting(sensitive=True, default_value="secret")

    def test_with_secret_ref(self):
        s = make_setting(secret_ref=make_secret())
        assert s.secret_ref.name == "db_password"

    def test_masked_repr_sensitive(self):
        s = make_setting(sensitive=True)
        masked = s.masked_repr()
        assert "sensitive=True" in masked
        assert "setting_id=s-001" in masked

    def test_masked_repr_non_sensitive(self):
        s = make_setting()
        masked = s.masked_repr()
        assert "sensitive=True" not in masked
        assert "s-001" in masked


class TestEnvironmentProfile:
    def test_valid(self):
        p = make_profile()
        assert p.profile_id == "prof-local"

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_profile(profile_id="")

    def test_blank_name_raises(self):
        with pytest.raises(ValidationError):
            make_profile(name="")

    def test_all_environment_types(self):
        for e in EnvironmentType:
            p = make_profile(environment=e)
            assert p.environment == e

    def test_with_config_keys(self):
        p = make_profile(config_keys=[make_key()])
        assert len(p.config_keys) == 1

    def test_with_secrets(self):
        p = make_profile(secrets=[make_secret()])
        assert len(p.secrets) == 1

    def test_with_runtime_settings(self):
        k = make_key()
        s = make_setting(key_ref=k)
        p = make_profile(config_keys=[k], runtime_settings=[s])
        assert len(p.runtime_settings) == 1

    def test_duplicate_config_key_raises(self):
        k = make_key()
        with pytest.raises(ValidationError, match="duplicate config key"):
            make_profile(config_keys=[k, k])

    def test_duplicate_secret_name_raises(self):
        s = make_secret()
        with pytest.raises(ValidationError, match="duplicate secret name"):
            make_profile(secrets=[s, s])

    def test_setting_references_undeclared_key_raises(self):
        other_key = make_key(key="other_key")
        with pytest.raises(ValidationError, match="references undeclared key"):
            make_profile(
                runtime_settings=[make_setting(key_ref=other_key)],
            )

    def test_description_optional(self):
        p = make_profile(description="Dev setup")
        assert p.description == "Dev setup"

    def test_empty_lists_default(self):
        p = make_profile()
        assert p.config_keys == []
        assert p.secrets == []
        assert p.runtime_settings == []


class TestConfigBundle:
    def test_valid(self):
        b = make_bundle()
        assert b.bundle_id == "bundle-001"

    def test_blank_bundle_id_raises(self):
        with pytest.raises(ValidationError):
            make_bundle(bundle_id="")

    def test_with_values(self):
        b = make_bundle(values={"db_host": "localhost"})
        assert b.values["db_host"] == "localhost"

    def test_required_key_missing_from_values_raises(self):
        k = make_key(key="api_key", required=True)
        p = make_profile(config_keys=[k])
        with pytest.raises(ValidationError, match="required config key missing"):
            make_bundle(profile=p, values={})

    def test_optional_key_missing_from_values_valid(self):
        k = make_key(key="log_level", required=False)
        p = make_profile(config_keys=[k])
        b = make_bundle(profile=p, values={})
        assert b.bundle_id == "bundle-001"

    def test_required_key_present_valid(self):
        k = make_key(key="api_key", required=True)
        p = make_profile(config_keys=[k])
        b = make_bundle(profile=p, values={"api_key": "abc123"})
        assert b.values["api_key"] == "abc123"

    def test_defaults_not_override_required_secret(self):
        secret_key = ConfigKeyRef(key="db_password", scope=ConfigScope.GLOBAL, source=ConfigSourceType.SECRET)
        sec = SecretRef(secret_id="sec-001", name="db_password", storage_type=SecretStorageType.ENV_VAR, required=True)
        # Setting has secret_ref but is NOT marked sensitive - this should be caught
        setting = RuntimeSettingRef(
            setting_id="s-001", key_ref=secret_key, value_type="string",
            secret_ref=sec, sensitive=False,
        )
        p = make_profile(config_keys=[secret_key], secrets=[sec], runtime_settings=[setting])
        with pytest.raises(ValidationError, match="must not silently override required secret"):
            make_bundle(profile=p, values={"db_password": "plaintext_default"})


class TestSecretsManifest:
    def test_valid(self):
        m = make_manifest()
        assert m.manifest_id == "manifest-001"

    def test_blank_manifest_id_raises(self):
        with pytest.raises(ValidationError):
            make_manifest(manifest_id="")

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValidationError):
            make_manifest(profile_id="")

    def test_with_secrets(self):
        m = make_manifest(secrets=[make_secret()])
        assert len(m.secrets) == 1

    def test_duplicate_secret_names_raises(self):
        s = make_secret()
        with pytest.raises(ValidationError, match="duplicate secret name in manifest"):
            make_manifest(secrets=[s, s])


class TestEnvironmentContractEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_manifest_profile_mismatch_raises(self):
        with pytest.raises(ValidationError, match="profile_id must match"):
            make_envelope(
                bundle=make_bundle(profile=make_profile(profile_id="prof-local")),
                secrets_manifest=make_manifest(profile_id="prof-prod"),
            )

    def test_manifest_profile_match_valid(self):
        e = make_envelope(
            bundle=make_bundle(profile=make_profile(profile_id="prof-dev")),
            secrets_manifest=make_manifest(profile_id="prof-dev"),
        )
        assert e.secrets_manifest.profile_id == "prof-dev"


class TestSerialization:
    def test_key_to_dict_and_back(self):
        k = make_key()
        data = k.model_dump()
        assert data["key"] == "db_host"
        restored = ConfigKeyRef(**data)
        assert restored.key == k.key

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        assert data["envelope_id"] == "env-001"
        restored = EnvironmentContractEnvelope(**data)
        assert restored.envelope_id == e.envelope_id


class TestIntegration:
    def test_local_development_profile(self):
        keys = [
            ConfigKeyRef(key="db_host", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR, required=True),
            ConfigKeyRef(key="log_level", scope=ConfigScope.GLOBAL, source=ConfigSourceType.DEFAULT, required=False),
        ]
        secrets = [
            SecretRef(secret_id="sec-001", name="db_password", storage_type=SecretStorageType.ENV_VAR, required=True),
            SecretRef(secret_id="sec-002", name="api_token", storage_type=SecretStorageType.FILE, required=False),
        ]
        settings = [
            RuntimeSettingRef(setting_id="s-001", key_ref=keys[0], value_type="string", sensitive=False),
            RuntimeSettingRef(setting_id="s-002", key_ref=keys[1], value_type="string", default_value="info", sensitive=False),
        ]
        profile = EnvironmentProfile(
            environment=EnvironmentType.LOCAL, profile_id="prof-local",
            name="Local Development", description="Local dev setup",
            config_keys=keys, secrets=secrets, runtime_settings=settings,
        )
        bundle = ConfigBundle(bundle_id="bundle-local", profile=profile, values={"db_host": "localhost"})
        manifest = SecretsManifest(manifest_id="manifest-local", profile_id="prof-local", secrets=secrets)
        env = EnvironmentContractEnvelope(envelope_id="env-local", bundle=bundle, secrets_manifest=manifest)
        assert env.bundle.profile.environment == EnvironmentType.LOCAL
        assert env.bundle.values["db_host"] == "localhost"
        assert len(env.secrets_manifest.secrets) == 2

    def test_production_profile_with_strict_requirements(self):
        keys = [
            ConfigKeyRef(key="db_host", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR, required=True),
            ConfigKeyRef(key="db_port", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR, required=True),
            ConfigKeyRef(key="api_endpoint", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR, required=True),
            ConfigKeyRef(key="log_level", scope=ConfigScope.GLOBAL, source=ConfigSourceType.DEFAULT, required=False),
        ]
        secrets = [
            SecretRef(secret_id="sec-001", name="db_password", storage_type=SecretStorageType.VAULT, required=True),
            SecretRef(secret_id="sec-002", name="api_key", storage_type=SecretStorageType.SECRET_MANAGER, required=True),
        ]
        profile = EnvironmentProfile(
            environment=EnvironmentType.PRODUCTION, profile_id="prof-prod",
            name="Production", config_keys=keys, secrets=secrets,
        )
        bundle = ConfigBundle(
            bundle_id="bundle-prod", profile=profile,
            values={"db_host": "prod-db.example.com", "db_port": "5432", "api_endpoint": "https://api.example.com"},
        )
        manifest = SecretsManifest(manifest_id="manifest-prod", profile_id="prof-prod", secrets=secrets)
        env = EnvironmentContractEnvelope(envelope_id="env-prod", bundle=bundle, secrets_manifest=manifest)
        assert env.bundle.profile.environment == EnvironmentType.PRODUCTION
        assert env.bundle.values["db_host"] == "prod-db.example.com"
        assert env.secrets_manifest.secrets[0].storage_type == SecretStorageType.VAULT

    def test_staging_profile_with_secret_references(self):
        keys = [
            ConfigKeyRef(key="api_endpoint", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR, required=True),
            ConfigKeyRef(key="log_level", scope=ConfigScope.GLOBAL, source=ConfigSourceType.DEFAULT, required=False),
        ]
        secrets = [
            SecretRef(secret_id="sec-001", name="staging_api_key", storage_type=SecretStorageType.ENV_VAR, required=True),
        ]
        profile = EnvironmentProfile(
            environment=EnvironmentType.STAGING, profile_id="prof-staging",
            name="Staging", config_keys=keys, secrets=secrets,
        )
        bundle = ConfigBundle(
            bundle_id="bundle-staging", profile=profile,
            values={"api_endpoint": "https://staging-api.example.com"},
        )
        manifest = SecretsManifest(manifest_id="manifest-staging", profile_id="prof-staging", secrets=secrets)
        env = EnvironmentContractEnvelope(envelope_id="env-staging", bundle=bundle, secrets_manifest=manifest)
        assert env.bundle.profile.environment == EnvironmentType.STAGING
        assert len(env.secrets_manifest.secrets) == 1

    def test_required_key_missing_raises_in_bundle(self):
        k = ConfigKeyRef(key="required_key", scope=ConfigScope.GLOBAL, source=ConfigSourceType.ENV_VAR, required=True)
        p = make_profile(config_keys=[k])
        with pytest.raises(ValidationError, match="required config key missing"):
            make_bundle(profile=p, values={})

    def test_duplicate_config_keys_in_profile_raises(self):
        k = make_key(key="dup")
        with pytest.raises(ValidationError, match="duplicate config key"):
            make_profile(config_keys=[k, make_key(key="dup")])
