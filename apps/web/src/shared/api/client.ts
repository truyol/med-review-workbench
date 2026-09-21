export type ApiMeta = { request_id: string };
export type ApiResponse<T> = { data: T; meta: ApiMeta };

export type Project = { id: string; name: string; description?: string | null; created_at: string; updated_at: string };
export type Case = { id: string; project_id: string; case_code: string; title: string; clinical_context?: string | null; created_at: string; updated_at: string };
export type AssetKind = "dicom" | "image" | "stl";
export type AssetStatus = "pending" | "accepted" | "needs_changes" | "rejected";
export type Asset = { id: string; case_id: string; kind: AssetKind; status: AssetStatus; source_label: string; content_type?: string | null; size_bytes: number; sha256: string; preview_available: boolean; metadata_summary: Record<string, unknown>; ingest_warnings: string[]; tags: string[]; note?: string | null; created_at: string; updated_at: string };
export type Review = { id: string; asset_id: string; decision: "accept" | "needs_changes" | "reject"; note?: string | null; reviewer_name: string; created_at: string; updated_at: string };
export type Annotation = { id: string; asset_id: string; label: string; data: Record<string, number>; note?: string | null; created_at: string; updated_at: string };
export type ReviewBoard = { case: Case; assets: Array<{ asset: Asset; latest_review: Review | null }> };

export class ApiError extends Error {
  code: string;
  nextAction: string;
  requestId?: string;
  constructor(message: string, code = "REQUEST_FAILED", nextAction = "请稍后重试", requestId?: string) {
    super(message); this.name = "ApiError"; this.code = code; this.nextAction = nextAction; this.requestId = requestId;
  }
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { ...init, headers: { "X-Request-ID": crypto.randomUUID(), ...(init?.headers ?? {}) } });
  if (response.status === 204) {
    return undefined as T;
  }
  const body = (await response.json().catch(() => null)) as { data?: T; error?: { code?: string; message?: string; next_action?: string; request_id?: string } } | null;
  if (!response.ok || !body?.data) {
    const error = body?.error;
    throw new ApiError(error?.message ?? `请求失败（${response.status}）`, error?.code, error?.next_action, error?.request_id);
  }
  return body.data;
}

export const fetchHealth = () => api<{ status: "ok"; service: "medreview-api" }>("/health");
export const fetchProjects = () => api<Project[]>("/projects?limit=100");
export const createProject = (payload: { name: string; description?: string }) => api<Project>("/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const fetchCases = (projectId: string) => api<Case[]>(`/projects/${projectId}/cases?limit=100`);
export const createCase = (projectId: string, payload: { case_code: string; title: string }) => api<Case>(`/projects/${projectId}/cases`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const fetchReviewBoard = (caseId: string) => api<ReviewBoard>(`/cases/${caseId}/review-board`);
export const uploadAsset = (caseId: string, file: File) => { const form = new FormData(); form.append("file", file); return api<Asset>(`/cases/${caseId}/assets`, { method: "POST", body: form }); };
export const reviewAsset = (assetId: string, payload: { decision: Review["decision"]; note?: string; reviewer_name: string }) => api<Review>(`/assets/${assetId}/reviews`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const updateAsset = (assetId: string, payload: { tags?: string[]; note?: string | null }) => api<Asset>(`/assets/${assetId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const fetchAnnotations = (assetId: string) => api<Annotation[]>(`/assets/${assetId}/annotations`);
export const createAnnotation = (assetId: string, payload: { label: string; data: Record<string, number>; note?: string | null }) => api<Annotation>(`/assets/${assetId}/annotations`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
export const deleteAnnotation = (annotationId: string) => api<void>(`/annotations/${annotationId}`, { method: "DELETE" });
export const deleteAsset = (assetId: string) => api<void>(`/assets/${assetId}`, { method: "DELETE" });
export const assetPreviewUrl = (assetId: string) => `/api/v1/assets/${assetId}/preview`;
export const assetModelUrl = (assetId: string) => `/api/v1/assets/${assetId}/model`;
