from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sqlite3
from typing import Any

from .models import ConfigCreate, ConfigVersion, ReleaseRecord, ValidationPolicy, ValidationResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, db_path: str):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    policy_json TEXT NOT NULL,
                    notes TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    issues_json TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL,
                    FOREIGN KEY(config_id) REFERENCES configs(id)
                );

                CREATE TABLE IF NOT EXISTS releases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER NOT NULL,
                    target_environment TEXT NOT NULL,
                    rollout_percent INTEGER NOT NULL,
                    change_ticket TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(config_id) REFERENCES configs(id)
                );
                """
            )

    def create_config(self, payload: ConfigCreate) -> ConfigVersion:
        now = _now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO configs (
                    service_name, environment, provider,
                    parameters_json, policy_json, notes,
                    status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.service_name,
                    payload.environment,
                    payload.provider,
                    json.dumps(payload.parameters),
                    payload.policy.model_dump_json(),
                    payload.notes,
                    "draft",
                    now,
                    now,
                ),
            )
            config_id = int(cursor.lastrowid)
        config = self.get_config(config_id)
        if config is None:
            raise RuntimeError("failed to create config")
        return config

    def list_configs(self) -> list[ConfigVersion]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM configs ORDER BY id DESC").fetchall()
        return [self._to_config(row) for row in rows]

    def get_config(self, config_id: int) -> ConfigVersion | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM configs WHERE id = ?", (config_id,)).fetchone()
        if row is None:
            return None
        return self._to_config(row)

    def update_status(self, config_id: int, status: str) -> None:
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                "UPDATE configs SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, config_id),
            )

    def save_validation(self, config_id: int, passed: bool, issues: list[str]) -> ValidationResult:
        evaluated_at = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO validations (config_id, passed, issues_json, evaluated_at)
                VALUES (?, ?, ?, ?)
                """,
                (config_id, 1 if passed else 0, json.dumps(issues), evaluated_at),
            )
        return ValidationResult(
            config_id=config_id,
            passed=passed,
            issues=issues,
            evaluated_at=evaluated_at,
        )

    def get_latest_validation(self, config_id: int) -> ValidationResult | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT config_id, passed, issues_json, evaluated_at
                FROM validations
                WHERE config_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (config_id,),
            ).fetchone()
        if row is None:
            return None
        return ValidationResult(
            config_id=int(row["config_id"]),
            passed=bool(row["passed"]),
            issues=self._load_json_list(row["issues_json"]),
            evaluated_at=str(row["evaluated_at"]),
        )

    def create_release(
        self,
        config_id: int,
        target_environment: str,
        rollout_percent: int,
        change_ticket: str,
        approved_by: str,
    ) -> ReleaseRecord:
        created_at = _now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO releases (
                    config_id, target_environment, rollout_percent,
                    change_ticket, approved_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (config_id, target_environment, rollout_percent, change_ticket, approved_by, created_at),
            )
            release_id = int(cursor.lastrowid)
        return ReleaseRecord(
            id=release_id,
            config_id=config_id,
            target_environment=target_environment,
            rollout_percent=rollout_percent,
            change_ticket=change_ticket,
            approved_by=approved_by,
            created_at=created_at,
        )

    def list_releases(self) -> list[ReleaseRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM releases ORDER BY id DESC").fetchall()

        output: list[ReleaseRecord] = []
        for row in rows:
            output.append(
                ReleaseRecord(
                    id=int(row["id"]),
                    config_id=int(row["config_id"]),
                    target_environment=str(row["target_environment"]),
                    rollout_percent=int(row["rollout_percent"]),
                    change_ticket=str(row["change_ticket"]),
                    approved_by=str(row["approved_by"]),
                    created_at=str(row["created_at"]),
                )
            )
        return output

    def _to_config(self, row: sqlite3.Row) -> ConfigVersion:
        policy_raw = json.loads(str(row["policy_json"]))
        return ConfigVersion(
            id=int(row["id"]),
            service_name=str(row["service_name"]),
            environment=str(row["environment"]),
            provider=str(row["provider"]),
            parameters=self._load_json_map(row["parameters_json"]),
            policy=ValidationPolicy(**policy_raw),
            notes=row["notes"],
            status=str(row["status"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _load_json_map(raw: Any) -> dict[str, Any]:
        data = json.loads(str(raw))
        if not isinstance(data, dict):
            raise ValueError("invalid parameters data")
        return data

    @staticmethod
    def _load_json_list(raw: Any) -> list[str]:
        data = json.loads(str(raw))
        if not isinstance(data, list):
            raise ValueError("invalid list data")
        return [str(item) for item in data]
