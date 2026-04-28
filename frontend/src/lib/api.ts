export type ConfigStatus = "draft" | "validated" | "rejected" | "promoted";

export type ValidationPolicy = {
  required_keys: string[];
  forbidden_keys: string[];
  max_temperature: number;
  min_timeout_ms: number;
  max_timeout_ms: number;
};

export type ConfigVersion = {
  id: number;
  service_name: string;
  environment: "dev" | "staging" | "prod";
  provider: "openai" | "azure-openai" | "anthropic" | "ollama" | "custom";
  parameters: Record<string, unknown>;
  policy: ValidationPolicy;
  notes: string | null;
  status: ConfigStatus;
  created_at: string;
  updated_at: string;
};

export type ValidationResult = {
  config_id: number;
  passed: boolean;
  issues: string[];
  evaluated_at: string;
};

export type ReleaseRecord = {
  id: number;
  config_id: number;
  target_environment: "staging" | "production";
  rollout_percent: number;
  change_ticket: string;
  approved_by: string;
  created_at: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8040";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    ...init
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export function listConfigs(): Promise<ConfigVersion[]> {
  return request<ConfigVersion[]>("/api/v1/configs");
}

export function createConfig(payload: {
  service_name: string;
  environment: "dev" | "staging" | "prod";
  provider: "openai" | "azure-openai" | "anthropic" | "ollama" | "custom";
  parameters: Record<string, unknown>;
  policy: ValidationPolicy;
  notes?: string;
}): Promise<ConfigVersion> {
  return request<ConfigVersion>("/api/v1/configs", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function validateConfig(configId: number): Promise<ValidationResult> {
  return request<ValidationResult>(`/api/v1/configs/${configId}/validate`, {
    method: "POST"
  });
}

export function latestValidation(configId: number): Promise<ValidationResult | null> {
  return request<ValidationResult | null>(`/api/v1/configs/${configId}/validation`);
}

export function promoteConfig(
  configId: number,
  payload: {
    target_environment: "staging" | "production";
    rollout_percent: number;
    change_ticket: string;
    approved_by: string;
  }
): Promise<ReleaseRecord> {
  return request<ReleaseRecord>(`/api/v1/configs/${configId}/promote`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listReleases(): Promise<ReleaseRecord[]> {
  return request<ReleaseRecord[]>("/api/v1/releases");
}
