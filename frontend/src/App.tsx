import { useEffect, useMemo, useState } from "react";

import { MetricTile } from "./components/MetricTile";
import { StatusBadge } from "./components/StatusBadge";
import {
  ConfigVersion,
  ReleaseRecord,
  ValidationPolicy,
  ValidationResult,
  createConfig,
  latestValidation,
  listConfigs,
  listReleases,
  promoteConfig,
  validateConfig
} from "./lib/api";

const defaultParameters = {
  model: "gpt-4o-mini",
  temperature: 0.4,
  timeout_ms: 1200,
  max_tokens: 1024
};

const defaultPolicy: ValidationPolicy = {
  required_keys: ["model", "temperature", "timeout_ms"],
  forbidden_keys: ["debug_mode"],
  max_temperature: 1.0,
  min_timeout_ms: 300,
  max_timeout_ms: 5000
};

export default function App() {
  const [configs, setConfigs] = useState<ConfigVersion[]>([]);
  const [releases, setReleases] = useState<ReleaseRecord[]>([]);
  const [selectedConfigId, setSelectedConfigId] = useState<number | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);

  const [serviceName, setServiceName] = useState("risk-router");
  const [environment, setEnvironment] = useState<"dev" | "staging" | "prod">("staging");
  const [provider, setProvider] = useState<"openai" | "azure-openai" | "anthropic" | "ollama" | "custom">(
    "openai"
  );
  const [parametersText, setParametersText] = useState(JSON.stringify(defaultParameters, null, 2));
  const [policyText, setPolicyText] = useState(JSON.stringify(defaultPolicy, null, 2));
  const [notes, setNotes] = useState("Initial safe rollout profile");

  const [targetEnvironment, setTargetEnvironment] = useState<"staging" | "production">("staging");
  const [rolloutPercent, setRolloutPercent] = useState(20);
  const [changeTicket, setChangeTicket] = useState("CHG-2001");
  const [approvedBy, setApprovedBy] = useState("platform-oncall");

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Ready");
  const [error, setError] = useState<string | null>(null);

  async function refreshData(): Promise<void> {
    const [configItems, releaseItems] = await Promise.all([listConfigs(), listReleases()]);
    setConfigs(configItems);
    setReleases(releaseItems);

    if (configItems.length === 0) {
      setSelectedConfigId(null);
      setValidation(null);
      return;
    }

    const newSelected = selectedConfigId ?? configItems[0].id;
    setSelectedConfigId(newSelected);
    const latest = await latestValidation(newSelected);
    setValidation(latest);
  }

  useEffect(() => {
    refreshData().catch((err: unknown) => {
      setError(err instanceof Error ? err.message : "Failed to load data");
    });
  }, []);

  const metrics = useMemo(() => {
    const validated = configs.filter((item) => item.status === "validated").length;
    const promoted = configs.filter((item) => item.status === "promoted").length;
    const rejected = configs.filter((item) => item.status === "rejected").length;
    return {
      total: configs.length,
      validated,
      promoted,
      rejected
    };
  }, [configs]);

  async function onCreateConfig() {
    setBusy(true);
    setError(null);

    try {
      const parameters = JSON.parse(parametersText) as Record<string, unknown>;
      const policy = JSON.parse(policyText) as ValidationPolicy;

      await createConfig({
        service_name: serviceName,
        environment,
        provider,
        parameters,
        policy,
        notes
      });
      setMessage("Configuration created");
      await refreshData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create configuration");
    } finally {
      setBusy(false);
    }
  }

  async function onValidateConfig() {
    if (selectedConfigId == null) {
      setError("Select a config first");
      return;
    }

    setBusy(true);
    setError(null);

    try {
      const result = await validateConfig(selectedConfigId);
      setValidation(result);
      setMessage(result.passed ? "Validation passed" : "Validation failed");
      await refreshData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to validate configuration");
    } finally {
      setBusy(false);
    }
  }

  async function onPromoteConfig() {
    if (selectedConfigId == null) {
      setError("Select a config first");
      return;
    }

    setBusy(true);
    setError(null);

    try {
      await promoteConfig(selectedConfigId, {
        target_environment: targetEnvironment,
        rollout_percent: rolloutPercent,
        change_ticket: changeTicket,
        approved_by: approvedBy
      });
      setMessage("Promotion created");
      await refreshData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to promote configuration");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <h1>config-forge</h1>
        <p>Version, validate, and promote model-serving configs with policy guardrails.</p>
      </header>

      <section className="metrics-grid" aria-label="Summary Metrics">
        <MetricTile title="Total Configs" value={String(metrics.total)} subtitle="Versioned entities tracked" />
        <MetricTile
          title="Validated"
          value={String(metrics.validated)}
          subtitle="Policy checks currently passing"
        />
        <MetricTile title="Promoted" value={String(metrics.promoted)} subtitle="Released through rollout gates" />
        <MetricTile title="Rejected" value={String(metrics.rejected)} subtitle="Requires remediation" />
      </section>

      <section className="panel" aria-label="Create Configuration">
        <h2>Create Configuration</h2>
        <div className="form-grid">
          <label>
            Service Name
            <input value={serviceName} onChange={(event) => setServiceName(event.target.value)} />
          </label>

          <label>
            Environment
            <select
              value={environment}
              onChange={(event) => setEnvironment(event.target.value as "dev" | "staging" | "prod")}
            >
              <option value="dev">dev</option>
              <option value="staging">staging</option>
              <option value="prod">prod</option>
            </select>
          </label>

          <label>
            Provider
            <select
              value={provider}
              onChange={(event) =>
                setProvider(event.target.value as "openai" | "azure-openai" | "anthropic" | "ollama" | "custom")
              }
            >
              <option value="openai">openai</option>
              <option value="azure-openai">azure-openai</option>
              <option value="anthropic">anthropic</option>
              <option value="ollama">ollama</option>
              <option value="custom">custom</option>
            </select>
          </label>

          <label>
            Notes
            <input value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>
        </div>

        <label>
          Parameters (JSON)
          <textarea
            value={parametersText}
            onChange={(event) => setParametersText(event.target.value)}
            rows={10}
          />
        </label>

        <label>
          Policy (JSON)
          <textarea value={policyText} onChange={(event) => setPolicyText(event.target.value)} rows={9} />
        </label>

        <button disabled={busy} onClick={onCreateConfig}>
          {busy ? "Working..." : "Create Config"}
        </button>
      </section>

      <section className="panel" aria-label="Validate and Promote">
        <h2>Validate and Promote</h2>

        <label>
          Select Config
          <select
            value={selectedConfigId ?? ""}
            onChange={(event) => setSelectedConfigId(Number(event.target.value))}
          >
            <option value="" disabled>
              Choose config
            </option>
            {configs.map((item) => (
              <option key={item.id} value={item.id}>
                #{item.id} {item.service_name} ({item.environment})
              </option>
            ))}
          </select>
        </label>

        <div className="button-row">
          <button disabled={busy || selectedConfigId == null} onClick={onValidateConfig}>
            Run Validation
          </button>
        </div>

        {validation && (
          <article className="validation-box">
            <h3>Latest Validation</h3>
            <p>
              Result: <strong>{validation.passed ? "PASS" : "FAIL"}</strong>
            </p>
            <p>Evaluated: {new Date(validation.evaluated_at).toLocaleString()}</p>
            {validation.issues.length > 0 ? (
              <ul>
                {validation.issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            ) : (
              <p>No issues detected.</p>
            )}
          </article>
        )}

        <div className="form-grid">
          <label>
            Target Environment
            <select
              value={targetEnvironment}
              onChange={(event) => setTargetEnvironment(event.target.value as "staging" | "production")}
            >
              <option value="staging">staging</option>
              <option value="production">production</option>
            </select>
          </label>
          <label>
            Rollout Percent
            <input
              type="number"
              min={1}
              max={100}
              value={rolloutPercent}
              onChange={(event) => setRolloutPercent(Number(event.target.value))}
            />
          </label>
          <label>
            Change Ticket
            <input value={changeTicket} onChange={(event) => setChangeTicket(event.target.value)} />
          </label>
          <label>
            Approved By
            <input value={approvedBy} onChange={(event) => setApprovedBy(event.target.value)} />
          </label>
        </div>

        <button disabled={busy || selectedConfigId == null} onClick={onPromoteConfig}>
          Promote Config
        </button>
      </section>

      <section className="panel" aria-label="Config Inventory">
        <h2>Config Inventory</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Service</th>
              <th>Environment</th>
              <th>Provider</th>
              <th>Status</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {configs.length === 0 ? (
              <tr>
                <td colSpan={6}>No configs yet.</td>
              </tr>
            ) : (
              configs.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.service_name}</td>
                  <td>{item.environment}</td>
                  <td>{item.provider}</td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{new Date(item.updated_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="panel" aria-label="Release History">
        <h2>Release History</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Config</th>
              <th>Target</th>
              <th>Rollout</th>
              <th>Ticket</th>
              <th>Approved By</th>
            </tr>
          </thead>
          <tbody>
            {releases.length === 0 ? (
              <tr>
                <td colSpan={6}>No releases yet.</td>
              </tr>
            ) : (
              releases.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.config_id}</td>
                  <td>{item.target_environment}</td>
                  <td>{item.rollout_percent}%</td>
                  <td>{item.change_ticket}</td>
                  <td>{item.approved_by}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <footer className="status-strip">
        <span>{message}</span>
        {error && <strong className="error-text">{error}</strong>}
      </footer>
    </main>
  );
}
