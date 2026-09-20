export type HealthResponse = {
  data: {
    status: "ok";
    service: "medreview-api";
  };
  meta: {
    request_id: string;
  };
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/v1/health", {
    headers: {
      "X-Request-ID": crypto.randomUUID(),
    },
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}
