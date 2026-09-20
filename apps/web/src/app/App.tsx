import { useEffect, useState } from "react";
import { Alert, App as AntApp, Card, ConfigProvider, Space, Tag, Typography } from "antd";

import { fetchHealth, type HealthResponse } from "../shared/api/client";

const { Paragraph, Text, Title } = Typography;

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((result) => {
        if (!cancelled) {
          setHealth(result);
        }
      })
      .catch((unknownError: unknown) => {
        if (!cancelled) {
          setError(unknownError instanceof Error ? unknownError.message : "Health check failed");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <ConfigProvider
      theme={{
        token: {
          borderRadius: 6,
          colorPrimary: "#1668dc",
        },
      }}
    >
      <AntApp>
        <main style={{ maxWidth: 920, margin: "0 auto", padding: "40px 24px" }}>
          <Space orientation="vertical" size={20} style={{ width: "100%" }}>
            <section>
              <Tag color="blue">P3 Scaffold</Tag>
              <Title level={2}>Med Review Workbench</Title>
              <Paragraph>
                结构性心脏病术前规划素材评审工作台。当前只验证工程底座，不进入业务评审流程。
              </Paragraph>
            </section>

            <Card title="API health probe" variant="outlined">
              {health ? (
                <Space orientation="vertical" size={8}>
                  <Text>
                    Status: <Tag color="green">{health.data.status}</Tag>
                  </Text>
                  <Text>Service: {health.data.service}</Text>
                  <Text type="secondary">request_id: {health.meta.request_id}</Text>
                </Space>
              ) : error ? (
                <Alert
                  type="warning"
                  message="API health unavailable"
                  description={error}
                  showIcon
                />
              ) : (
                <Text type="secondary">Checking API health...</Text>
              )}
            </Card>
          </Space>
        </main>
      </AntApp>
    </ConfigProvider>
  );
}
