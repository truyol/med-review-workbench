import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

function renderApp(path = "/") {
  window.history.replaceState({}, "", path);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><App /></QueryClientProvider>);
}

describe("P5 workbench shell", () => {
  it("redirects to the project workspace", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({ data: [], meta: { request_id: "test" } }), { status: 200 }))));
    renderApp();
    expect(await screen.findByRole("heading", { name: "项目工作台" })).toBeInTheDocument();
    expect(screen.getByText(/素材评审闭环/)).toBeInTheDocument();
  });

  it("renders every review status from the backend board", async () => {
    const statuses = ["pending", "accepted", "needs_changes", "rejected"] as const;
    const labels = ["待评审", "已通过", "需补充", "已拒绝"];
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({
      data: {
        case: { id: "case-1", project_id: "project-1", case_code: "P8", title: "Status mapping", created_at: "2026-09-21T00:00:00Z", updated_at: "2026-09-21T00:00:00Z" },
        assets: statuses.map((status, index) => ({
          asset: { id: `asset-${index}`, case_id: "case-1", kind: "image", status, source_label: `Asset ${index}`, content_type: "image/png", size_bytes: 100, sha256: "a".repeat(64), preview_available: true, metadata_summary: {}, ingest_warnings: [], created_at: "2026-09-21T00:00:00Z", updated_at: "2026-09-21T00:00:00Z" },
          latest_review: null,
        })),
      },
      meta: { request_id: "status-test" },
    }), { status: 200 }))));

    renderApp("/cases/case-1");
    for (const label of labels) expect(await screen.findByText(label)).toBeInTheDocument();
  });

  it("renders the stable API next action for a recoverable failure", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify({
      error: {
        code: "SERVICE_UNAVAILABLE",
        message: "Projects are temporarily unavailable.",
        next_action: "Retry after checking API readiness.",
        request_id: "component-error",
      },
    }), { status: 503 }))));

    renderApp("/projects");
    expect(await screen.findByText("Projects are temporarily unavailable.")).toBeInTheDocument();
    expect(screen.getByText("Retry after checking API readiness.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /重\s*试/ })).toBeInTheDocument();
  });
});
