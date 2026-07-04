import pytest
from pydantic import ValidationError
from models.production_config import (
    DeploymentEnvironment,
    SecretSource,
    SecretReference,
    ProviderConfig,
    RuntimeBudgetConfig,
    TracingConfig,
    SecurityConfig,
    AppConfig,
    ResolvedSecret,
    ResolvedRuntimeConfig,
    ConfigValidationResult,
)


def make_dev_config(**overrides) -> AppConfig:
    defaults = dict(
        environment=DeploymentEnvironment.DEVELOPMENT,
        app_name="harness-dev",
        provider=ProviderConfig(
            provider_name="openrouter",
            model_name="google/gemini-2.0-flash-001",
            api_key_secret=SecretReference(
                secret_name="openrouter_api_key",
                source=SecretSource.ENV,
                reference="OPENROUTER_API_KEY",
            ),
            timeout_seconds=60,
            max_retries=2,
        ),
        runtime_budget=RuntimeBudgetConfig(
            max_steps_per_run=12,
            max_tool_calls_per_run=8,
            max_runtime_seconds=120,
            max_cost_usd_per_run=1.0,
        ),
        tracing=TracingConfig(
            enabled=True,
            redact_sensitive_fields=True,
            store_prompt_bodies=False,
            store_tool_arguments=False,
        ),
        security=SecurityConfig(
            allowed_egress_hosts=["api.openai.com", "api.anthropic.com"],
            secrets_redaction_enabled=True,
            enforce_secret_scoping=True,
            require_approval_for_secret_access=True,
        ),
    )
    defaults.update(overrides)
    return AppConfig(**defaults)


class TestEnums:
    def test_deployment_environment_values(self):
        assert DeploymentEnvironment.DEVELOPMENT.value == "development"
        assert DeploymentEnvironment.STAGING.value == "staging"
        assert DeploymentEnvironment.PRODUCTION.value == "production"

    def test_secret_source_values(self):
        assert SecretSource.ENV.value == "env"
        assert SecretSource.FILE.value == "file"
        assert SecretSource.VAULT.value == "vault"


class TestSecretReference:
    def test_valid_environments(self):
        ref = SecretReference(
            secret_name="db_pass",
            source=SecretSource.ENV,
            reference="DATABASE_PASSWORD",
        )
        assert ref.secret_name == "db_pass"
        assert ref.required is True

    def test_empty_secret_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            SecretReference(secret_name="  ", source=SecretSource.ENV, reference="X")
        assert "secret_name must not be empty" in str(exc.value)

    def test_empty_reference_raises(self):
        with pytest.raises(ValidationError) as exc:
            SecretReference(secret_name="k", source=SecretSource.ENV, reference="  ")
        assert "reference must not be empty" in str(exc.value)

    def test_with_description(self):
        ref = SecretReference(
            secret_name="api_key",
            source=SecretSource.VAULT,
            reference="projects/p/secrets/k",
            description="OpenRouter API key from vault",
        )
        assert ref.description == "OpenRouter API key from vault"

    def test_not_required_and_env_only(self):
        ref = SecretReference(
            secret_name="optional_key",
            source=SecretSource.FILE,
            reference="/etc/secrets/key",
            required=False,
            allow_in_env_only=True,
        )
        assert ref.required is False
        assert ref.allow_in_env_only is True


class TestProviderConfig:
    def test_valid_config(self):
        cfg = ProviderConfig(
            provider_name="anthropic",
            model_name="claude-3-opus-20240229",
        )
        assert cfg.timeout_seconds == 60
        assert cfg.max_retries == 2
        assert cfg.enabled is True

    def test_with_api_base_and_secret(self):
        cfg = ProviderConfig(
            provider_name="openai",
            model_name="gpt-4",
            api_base="https://api.openai.com/v1",
            api_key_secret=SecretReference(
                secret_name="openai_key", source=SecretSource.ENV, reference="OPENAI_API_KEY"
            ),
        )
        assert cfg.api_base == "https://api.openai.com/v1"
        assert cfg.api_key_secret.secret_name == "openai_key"

    def test_empty_provider_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProviderConfig(provider_name="  ", model_name="gpt-4")
        assert "must not be empty" in str(exc.value)

    def test_empty_model_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProviderConfig(provider_name="openai", model_name="   ")
        assert "must not be empty" in str(exc.value)

    def test_timeout_too_low_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProviderConfig(provider_name="openai", model_name="gpt-4", timeout_seconds=0)
        assert "timeout_seconds must be at least 1" in str(exc.value)

    def test_retries_negative_raises(self):
        with pytest.raises(ValidationError) as exc:
            ProviderConfig(provider_name="openai", model_name="gpt-4", max_retries=-1)
        assert "max_retries must be non-negative" in str(exc.value)

    def test_disabled_provider(self):
        cfg = ProviderConfig(
            provider_name="openai", model_name="gpt-4", enabled=False
        )
        assert cfg.enabled is False


class TestRuntimeBudgetConfig:
    def test_defaults(self):
        budget = RuntimeBudgetConfig()
        assert budget.max_steps_per_run == 12
        assert budget.max_tool_calls_per_run == 8
        assert budget.max_runtime_seconds == 120
        assert budget.max_cost_usd_per_run == 1.0

    def test_zero_steps_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudgetConfig(max_steps_per_run=0)
        assert "must be at least 1" in str(exc.value)

    def test_zero_tool_calls_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudgetConfig(max_tool_calls_per_run=0)
        assert "must be at least 1" in str(exc.value)

    def test_zero_runtime_seconds_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudgetConfig(max_runtime_seconds=0)
        assert "max_runtime_seconds must be at least 1" in str(exc.value)

    def test_negative_cost_raises(self):
        with pytest.raises(ValidationError) as exc:
            RuntimeBudgetConfig(max_cost_usd_per_run=-0.5)
        assert "max_cost_usd_per_run must be non-negative" in str(exc.value)

    def test_zero_cost_is_valid(self):
        budget = RuntimeBudgetConfig(max_cost_usd_per_run=0.0)
        assert budget.max_cost_usd_per_run == 0.0

    def test_custom_budget(self):
        budget = RuntimeBudgetConfig(
            max_steps_per_run=50,
            max_tool_calls_per_run=30,
            max_runtime_seconds=300,
            max_cost_usd_per_run=5.0,
        )
        assert budget.max_steps_per_run == 50
        assert budget.max_tool_calls_per_run == 30


class TestTracingConfig:
    def test_defaults(self):
        tracing = TracingConfig()
        assert tracing.enabled is True
        assert tracing.redact_sensitive_fields is True
        assert tracing.store_prompt_bodies is False
        assert tracing.store_tool_arguments is False


class TestSecurityConfig:
    def test_defaults(self):
        sec = SecurityConfig()
        assert sec.allowed_egress_hosts == []
        assert sec.secrets_redaction_enabled is True
        assert sec.enforce_secret_scoping is True
        assert sec.require_approval_for_secret_access is True

    def test_with_egress_hosts(self):
        sec = SecurityConfig(
            allowed_egress_hosts=["api.openai.com", "api.anthropic.com"],
        )
        assert len(sec.allowed_egress_hosts) == 2

    def test_security_disabled(self):
        sec = SecurityConfig(
            secrets_redaction_enabled=False,
            enforce_secret_scoping=False,
            require_approval_for_secret_access=False,
        )
        assert sec.secrets_redaction_enabled is False


class TestAppConfig:
    def test_valid_dev_config(self):
        cfg = make_dev_config()
        assert cfg.environment == DeploymentEnvironment.DEVELOPMENT
        assert cfg.app_name == "harness-dev"
        assert cfg.provider.provider_name == "openrouter"

    def test_valid_staging_config(self):
        cfg = make_dev_config(environment=DeploymentEnvironment.STAGING, app_name="harness-staging")
        assert cfg.environment == DeploymentEnvironment.STAGING

    def test_valid_production_config(self):
        cfg = make_dev_config(
            environment=DeploymentEnvironment.PRODUCTION,
            app_name="harness-prod",
            tracing=TracingConfig(
                enabled=True,
                redact_sensitive_fields=True,
                store_prompt_bodies=False,
                store_tool_arguments=False,
            ),
            security=SecurityConfig(
                allowed_egress_hosts=["api.openai.com", "api.anthropic.com"],
                secrets_redaction_enabled=True,
                enforce_secret_scoping=True,
                require_approval_for_secret_access=True,
            ),
        )
        assert cfg.environment == DeploymentEnvironment.PRODUCTION

    def test_empty_app_name_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_dev_config(app_name="  ")
        assert "app_name must not be empty" in str(exc.value)

    def test_production_missing_secret_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_dev_config(
                environment=DeploymentEnvironment.PRODUCTION,
                app_name="harness-prod",
                provider=ProviderConfig(
                    provider_name="openrouter",
                    model_name="gpt-4",
                    api_key_secret=None,
                ),
            )
        assert "production provider must have an api_key_secret" in str(exc.value)

    def test_production_store_prompt_bodies_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_dev_config(
                environment=DeploymentEnvironment.PRODUCTION,
                app_name="harness-prod",
                tracing=TracingConfig(
                    enabled=True,
                    redact_sensitive_fields=True,
                    store_prompt_bodies=True,
                    store_tool_arguments=False,
                ),
            )
        assert "production must not store prompt bodies" in str(exc.value)

    def test_production_store_tool_arguments_raises(self):
        with pytest.raises(ValidationError) as exc:
            make_dev_config(
                environment=DeploymentEnvironment.PRODUCTION,
                app_name="harness-prod",
                tracing=TracingConfig(
                    enabled=True,
                    redact_sensitive_fields=True,
                    store_prompt_bodies=False,
                    store_tool_arguments=True,
                ),
            )
        assert "production must not store tool arguments" in str(exc.value)

    def test_development_can_store_prompt_bodies(self):
        cfg = make_dev_config(
            tracing=TracingConfig(
                enabled=True,
                redact_sensitive_fields=True,
                store_prompt_bodies=True,
                store_tool_arguments=True,
            ),
        )
        assert cfg.tracing.store_prompt_bodies is True
        assert cfg.tracing.store_tool_arguments is True


class TestResolvedSecret:
    def test_valid_resolved(self):
        secret = ResolvedSecret(
            secret_name="openrouter_key",
            resolved_from=SecretSource.ENV,
            value_present=True,
            redacted_preview="sk-or-v1-********...",
        )
        assert secret.secret_name == "openrouter_key"
        assert secret.value_present is True

    def test_short_redacted_preview_raises(self):
        with pytest.raises(ValidationError) as exc:
            ResolvedSecret(
                secret_name="k",
                resolved_from=SecretSource.ENV,
                value_present=True,
                redacted_preview="abc",
            )
        assert "redacted_preview must be at least 10 characters" in str(exc.value)

    def test_no_value_resolved(self):
        secret = ResolvedSecret(
            secret_name="optional_key",
            resolved_from=SecretSource.FILE,
            value_present=False,
            redacted_preview="not-found...",
        )
        assert secret.value_present is False


class TestResolvedRuntimeConfig:
    def test_with_secrets(self):
        app_cfg = make_dev_config()
        secrets = [
            ResolvedSecret(
                secret_name="openrouter_key",
                resolved_from=SecretSource.ENV,
                value_present=True,
                redacted_preview="sk-or-********...",
            ),
        ]
        runtime = ResolvedRuntimeConfig(app_config=app_cfg, resolved_secrets=secrets)
        assert runtime.app_config.app_name == "harness-dev"
        assert len(runtime.resolved_secrets) == 1

    def test_without_secrets(self):
        app_cfg = make_dev_config()
        runtime = ResolvedRuntimeConfig(app_config=app_cfg)
        assert runtime.resolved_secrets == []


class TestConfigValidationResult:
    def test_valid(self):
        result = ConfigValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_with_errors(self):
        result = ConfigValidationResult(
            valid=False,
            errors=["production provider must have an api_key_secret"],
        )
        assert result.valid is False
        assert len(result.errors) == 1

    def test_with_warnings(self):
        result = ConfigValidationResult(
            valid=True,
            warnings=["no egress hosts configured in production"],
        )
        assert result.valid is True
        assert len(result.warnings) == 1


class TestModelDumpDoesNotExposeSecrets:
    def test_provider_config_dump_no_secret_value(self):
        cfg = make_dev_config()
        dumped = cfg.model_dump()
        api_key_secret = dumped["provider"]["api_key_secret"]
        assert api_key_secret["secret_name"] == "openrouter_api_key"
        assert api_key_secret["source"] == "env"
        assert "value" not in api_key_secret
        assert "secret_value" not in api_key_secret

    def test_resolved_secret_dump_redacted_only(self):
        secret = ResolvedSecret(
            secret_name="api_key",
            resolved_from=SecretSource.ENV,
            value_present=True,
            redacted_preview="sk-********...",
        )
        dumped = secret.model_dump()
        assert dumped["redacted_preview"] == "sk-********..."
        assert dumped["value_present"] is True
        assert "value" not in dumped
        assert "raw_value" not in dumped


class TestSerialization:
    def test_app_config_to_json(self):
        cfg = make_dev_config()
        json_str = cfg.model_dump_json()
        assert "harness-dev" in json_str
        assert "openrouter" in json_str
        assert "sk-or" not in json_str

    def test_resolved_config_roundtrip(self):
        app_cfg = make_dev_config()
        runtime = ResolvedRuntimeConfig(app_config=app_cfg)
        dumped = runtime.model_dump()
        assert dumped["app_config"]["app_name"] == "harness-dev"
