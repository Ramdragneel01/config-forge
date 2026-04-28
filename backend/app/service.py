from __future__ import annotations

from .models import PromotionRequest, ReleaseRecord, ValidationResult
from .store import Store


class ConfigService:
    def __init__(self, store: Store):
        self.store = store

    def create_config(self, payload):
        return self.store.create_config(payload)

    def list_configs(self):
        return self.store.list_configs()

    def get_latest_validation(self, config_id: int) -> ValidationResult | None:
        return self.store.get_latest_validation(config_id)

    def validate_config(self, config_id: int) -> ValidationResult:
        config = self.store.get_config(config_id)
        if config is None:
            raise ValueError("config not found")

        policy = config.policy
        params = config.parameters
        issues: list[str] = []

        for key in policy.required_keys:
            if key not in params:
                issues.append(f"Missing required key: {key}")

        for key in policy.forbidden_keys:
            if key in params:
                issues.append(f"Forbidden key present: {key}")

        temperature = params.get("temperature")
        if temperature is not None:
            if isinstance(temperature, (int, float)):
                if float(temperature) > policy.max_temperature:
                    issues.append(
                        f"temperature exceeds max_temperature ({temperature} > {policy.max_temperature})"
                    )
            else:
                issues.append("temperature must be numeric")

        timeout_ms = params.get("timeout_ms")
        if timeout_ms is not None:
            if isinstance(timeout_ms, (int, float)):
                timeout_value = int(timeout_ms)
                if timeout_value < policy.min_timeout_ms:
                    issues.append(
                        f"timeout_ms below minimum ({timeout_value} < {policy.min_timeout_ms})"
                    )
                if timeout_value > policy.max_timeout_ms:
                    issues.append(
                        f"timeout_ms above maximum ({timeout_value} > {policy.max_timeout_ms})"
                    )
            else:
                issues.append("timeout_ms must be numeric")

        if config.provider == "azure-openai" and "api_version" not in params:
            issues.append("azure-openai provider requires api_version")

        if config.environment == "prod" and params.get("mock_mode") is True:
            issues.append("prod configuration cannot enable mock_mode")

        max_tokens = params.get("max_tokens")
        if isinstance(max_tokens, (int, float)) and int(max_tokens) > 8192:
            issues.append("max_tokens exceeds 8192 safety ceiling")

        passed = not issues
        result = self.store.save_validation(config_id=config_id, passed=passed, issues=issues)
        self.store.update_status(config_id, "validated" if passed else "rejected")
        return result

    def promote_config(self, config_id: int, payload: PromotionRequest) -> ReleaseRecord:
        config = self.store.get_config(config_id)
        if config is None:
            raise ValueError("config not found")

        latest_validation = self.store.get_latest_validation(config_id)
        if latest_validation is None or not latest_validation.passed:
            raise PermissionError("config must pass validation before promotion")

        if payload.target_environment == "production" and payload.rollout_percent < 5:
            raise ValueError("production rollout_percent must be at least 5")

        release = self.store.create_release(
            config_id=config_id,
            target_environment=payload.target_environment,
            rollout_percent=payload.rollout_percent,
            change_ticket=payload.change_ticket,
            approved_by=payload.approved_by,
        )
        self.store.update_status(config_id, "promoted")
        return release

    def list_releases(self):
        return self.store.list_releases()
