// Shakisha API client — all calls proxy through Next.js to FastAPI on :8000

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "API error");
  }
  return res.json();
}

// ── Types ──────────────────────────────────────────────────────────────────

export type QualityLevel = "good" | "warning" | "critical";

export interface StudyResource {
  type: string;
  url: string;
  title: string;
}

export interface Study {
  study_id: string;
  title: string;
  is_nisr: boolean;
  year: string;
  organization: string;
  abstract: string;
  url: string;
  get_microdata_url: string;
  geographic_coverage: string;
  geographic_unit: string;
  quality_level: QualityLevel;
  quality_flags: string[];
  missing_field_count: number;
  resource_count: number;
  resources: StudyResource[];
}

export interface SearchRequest {
  query?: string;
  domain?: string;
  year_min?: number | null;
  year_max?: number | null;
  organization?: string;
  district?: string;
  resource_type?: string;
  quality_filter?: string;
  sort_order?: string;
  use_ai?: boolean;
}

export interface SearchResponse {
  results: Study[];
  total: number;
  total_in_domain: number;
  ai_explanation: string;
}

export interface DomainConfig {
  name: string;
  emoji: string;
  description: string;
  status: string;
  advocacy_context: string;
  study_count: number;
}

export interface CatalogStats {
  study_count: number;
  resource_count: number;
  active_domains: number;
  ai_available: boolean;
  catalog_updated: string;
}

export interface QualityItem {
  study_id: string;
  title: string;
  missing_field_count: number;
  quality_level: QualityLevel;
  quality_flags: string[];
}

export interface Brief {
  policy_context: string;
  key_findings: string;
  data_gaps: string;
  recommended_action: string;
  citation: string;
}

export interface BriefResponse {
  brief: Brief;
  study: Study;
}

export interface LinkCheckResult {
  study_id: string;
  title: string;
  url: string;
  status: "available" | "error" | "unreachable" | "invalid";
  http_code: number | null;
}

export interface PipelineSource {
  key: string;
  name: string;
  badge: string;
  badge_type: "active" | "crawler" | "academic" | "planned";
  description: string;
  adapter: string | null;
  run_cmd: string | null;
  study_count: number;
  resource_count: number | null;
  last_ingested: string;
  active: boolean;
}

export interface RecentStudy {
  study_id: string;
  title: string;
  organization: string;
  year: string;
  source_adapter: string;
  ingested_at: string;
}

export interface PipelineStatus {
  sources: PipelineSource[];
  total_studies: number;
  total_resources: number;
  active_sources: number;
  new_today: number;
  recently_added: RecentStudy[];
}

export interface ProvinceData {
  key: string;
  name: string;
  specific_count: number;
  total_count: number;
  domain_counts: Record<string, number>;
}

export interface DistrictData {
  name: string;
  province: string;
  study_count: number;
}

export interface GeoResolution {
  sub_district: number;
  district: number;
  province: number;
  national: number;
  unspecified: number;
}

export interface GeographicData {
  provinces: ProvinceData[];
  districts: DistrictData[];
  national_count: number;
  national_domains: Record<string, number>;
  total_studies: number;
  geo_resolution: GeoResolution;
}

// ── API functions ──────────────────────────────────────────────────────────

export const api = {
  stats: () => get<CatalogStats>("/stats"),

  domains: () => get<Record<string, DomainConfig>>("/domains"),

  organizations: () =>
    get<{ organizations: string[] }>("/organizations").then(
      (r) => r.organizations
    ),

  resourceTypes: () =>
    get<{ resource_types: string[] }>("/resource-types").then(
      (r) => r.resource_types
    ),

  districts: () =>
    get<{ districts: string[] }>("/districts").then(
      (r) => r.districts
    ),

  search: (req: SearchRequest) => post<SearchResponse>("/search", req),

  study: (id: string) => get<Study>(`/studies/${id}`),

  quality: (domain = "all") =>
    get<{ items: QualityItem[]; catalog_updated: string }>(`/quality${domain !== "all" ? `?domain=${domain}` : ""}`),

  brief: (study_id: string) =>
    post<BriefResponse>("/brief", { study_id }),

  explain: (study_id: string, query: string) =>
    post<{ explanation: string }>("/explain", { study_id, query }),

  linkCheck: (study_ids: string[]) =>
    post<{ results: LinkCheckResult[] }>("/link-check", { study_ids }),

  pipeline: () => get<PipelineStatus>("/pipeline"),

  geographic: () => get<GeographicData>("/geographic"),
};
