import { lazy, Suspense, useState, type ReactNode } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  ConfigProvider,
  Descriptions,
  Empty,
  Form,
  Input,
  Layout,
  Modal,
  Progress,
  Result,
  Select,
  Spin,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  FileImageOutlined,
  InboxOutlined,
  MedicineBoxOutlined,
  PlusOutlined,
  SafetyCertificateOutlined,
  ScanOutlined,
} from "@ant-design/icons";
import zhCN from "antd/locale/zh_CN";

import {
  ApiError,
  assetPreviewUrl,
  createCase,
  createProject,
  fetchCases,
  fetchProjects,
  fetchReviewBoard,
  reviewAsset,
  uploadAsset,
  type Asset,
  type Review,
} from "../shared/api/client";

const StlViewer = lazy(() => import("../features/viewer/StlViewer"));

const { Header, Content } = Layout;

const statusLabel: Record<Asset["status"], string> = {
  pending: "待评审",
  accepted: "已通过",
  needs_changes: "需补充",
  rejected: "已拒绝",
};
const statusColor: Record<Asset["status"], string> = {
  pending: "gold",
  accepted: "green",
  needs_changes: "orange",
  rejected: "red",
};
const kindLabel: Record<Asset["kind"], string> = { dicom: "DICOM", image: "图片", stl: "3D 模型" };
const kindIcon: Record<Asset["kind"], ReactNode> = {
  dicom: <ScanOutlined />,
  image: <FileImageOutlined />,
  stl: <MedicineBoxOutlined />,
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  const apiError = error instanceof ApiError ? error : undefined;
  return (
    <Alert
      type="error"
      showIcon
      title={apiError?.message ?? "页面加载失败"}
      description={apiError?.nextAction ?? "请检查 API 服务后重试"}
      action={
        retry ? (
          <Button size="small" onClick={retry}>
            重试
          </Button>
        ) : undefined
      }
    />
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <Layout className="app-shell">
      <Header className="app-header">
        <Link to="/projects" className="brand">
          <span className="brand-mark">
            <SafetyCertificateOutlined />
          </span>
          <span className="brand-text">
            Med Review Workbench
            <em>结构性心脏病术前规划 · 素材评审闭环</em>
          </span>
        </Link>
        <Tag className="env-tag">
          工程评审原型 · 不用于临床
        </Tag>
      </Header>
      <Content className="app-content">{children}</Content>
      <footer className="app-footer">
        仅用于医学影像工程素材的整理与评审，不输出诊断、治疗建议或自动分割结论。
      </footer>
    </Layout>
  );
}

function Page({
  title,
  subtitle,
  action,
  back,
  children,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  back?: string;
  children: ReactNode;
}) {
  const navigate = useNavigate();
  return (
    <div className="page">
      <div className="page-heading">
        <div className="page-heading-main">
          {back && (
            <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate(back)}>
              返回
            </Button>
          )}
          <div>
            <Typography.Title level={2}>{title}</Typography.Title>
            {subtitle && <Typography.Paragraph type="secondary">{subtitle}</Typography.Paragraph>}
          </div>
        </div>
        {action && <div className="heading-action">{action}</div>}
      </div>
      {children}
    </div>
  );
}

function ProjectsPage() {
  const navigate = useNavigate();
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<{ name: string; description?: string }>();
  const query = useQuery({ queryKey: ["projects"], queryFn: fetchProjects });
  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      client.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
      form.resetFields();
      navigate(`/projects/${project.id}`);
    },
  });

  return (
    <Page
      title="项目工作台"
      subtitle="从项目进入病例，再完成素材上传、预览与评审。"
      action={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          新建项目
        </Button>
      }
    >
      {query.isPending ? (
        <div className="state-block">
          <Spin />
        </div>
      ) : query.isError ? (
        <ErrorNotice error={query.error} retry={() => query.refetch()} />
      ) : query.data.length === 0 ? (
        <Empty description="还没有项目，从一个演示项目开始" />
      ) : (
        <div className="project-grid">
          {query.data.map((item) => (
            <Card
              key={item.id}
              hoverable
              className="project-card"
              onClick={() => navigate(`/projects/${item.id}`)}
            >
              <div className="project-card-title">{item.name}</div>
              <div className="project-card-desc">{item.description || "未填写项目说明"}</div>
              <div className="project-card-foot">创建于 {new Date(item.created_at).toLocaleDateString()}</div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        title="新建项目"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={mutation.isPending}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={(values) => mutation.mutate(values)}>
          <Form.Item name="name" label="项目名称" rules={[{ required: true }]}>
            <Input placeholder="TAVR 术前素材评审" />
          </Form.Item>
          <Form.Item name="description" label="项目说明">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Page>
  );
}

function ProjectPage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm<{ case_code: string; title: string }>();
  const projects = useQuery({ queryKey: ["projects"], queryFn: fetchProjects });
  const cases = useQuery({
    queryKey: ["cases", projectId],
    queryFn: () => fetchCases(projectId),
    enabled: Boolean(projectId),
  });
  const project = projects.data?.find((item) => item.id === projectId);
  const mutation = useMutation({
    mutationFn: (payload: { case_code: string; title: string }) => createCase(projectId, payload),
    onSuccess: (item) => {
      client.invalidateQueries({ queryKey: ["cases", projectId] });
      setOpen(false);
      form.resetFields();
      navigate(`/cases/${item.id}`);
    },
  });

  return (
    <Page
      title={project?.name ?? "项目病例"}
      subtitle={project?.description ?? "选择病例进入素材评审看板。"}
      back="/projects"
      action={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          新建病例
        </Button>
      }
    >
      {cases.isPending ? (
        <div className="state-block">
          <Spin />
        </div>
      ) : cases.isError ? (
        <ErrorNotice error={cases.error} retry={() => cases.refetch()} />
      ) : cases.data.length === 0 ? (
        <Empty description="还没有病例，请创建一个演示病例" />
      ) : (
        <div className="case-grid">
          {cases.data.map((item) => (
            <Card
              key={item.id}
              hoverable
              className="case-card"
              onClick={() => navigate(`/cases/${item.id}`)}
            >
              <Tag color="blue">{item.case_code}</Tag>
              <div className="case-card-title">{item.title}</div>
              <div className="case-card-desc">
                {item.clinical_context || "未填写临床上下文（仅用于素材组织）"}
              </div>
              <Button type="link" className="case-card-action">
                进入评审
              </Button>
            </Card>
          ))}
        </div>
      )}

      <Modal
        title="新建病例"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={mutation.isPending}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={(values) => mutation.mutate(values)}>
          <Form.Item name="case_code" label="病例编号" rules={[{ required: true }]}>
            <Input placeholder="DEMO-TAVR-001" />
          </Form.Item>
          <Form.Item name="title" label="病例标题" rules={[{ required: true }]}>
            <Input placeholder="术前素材评审" />
          </Form.Item>
        </Form>
      </Modal>
    </Page>
  );
}

function CasePage() {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const board = useQuery({
    queryKey: ["review-board", caseId],
    queryFn: () => fetchReviewBoard(caseId),
    enabled: Boolean(caseId),
  });
  const upload = useMutation({
    mutationFn: (file: File) => uploadAsset(caseId, file),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["review-board", caseId] });
      messageApi.success("素材已上传并完成基础校验");
    },
    onError: (error) =>
      messageApi.error(error instanceof ApiError ? error.nextAction : "上传失败"),
  });

  const assets = board.data?.assets ?? [];
  const reviewed = assets.filter((item) => item.asset.status !== "pending").length;
  const percent = assets.length === 0 ? 0 : Math.round((reviewed / assets.length) * 100);

  return (
    <Page
      title={board.data?.case ? `${board.data.case.case_code} · ${board.data.case.title}` : "病例评审看板"}
      subtitle="先上传素材，再逐项确认状态与评审结论。"
      back={board.data?.case ? `/projects/${board.data.case.project_id}` : "/projects"}
      action={
        <Upload
          showUploadList={false}
          beforeUpload={(file) => {
            upload.mutate(file);
            return false;
          }}
          accept=".dcm,.dicom,.stl,.png,.jpg,.jpeg"
        >
          <Button type="primary" icon={<InboxOutlined />} loading={upload.isPending}>
            上传素材
          </Button>
        </Upload>
      }
    >
      {contextHolder}
      {board.isPending ? (
        <div className="state-block">
          <Spin />
        </div>
      ) : board.isError ? (
        <ErrorNotice error={board.error} retry={() => board.refetch()} />
      ) : (
        <>
          <Card className="board-summary" variant="borderless">
            <div className="board-summary-row">
              <div>
                <div className="board-summary-value">{assets.length}</div>
                <div className="board-summary-label">素材总数</div>
              </div>
              <div>
                <div className="board-summary-value">{reviewed}</div>
                <div className="board-summary-label">已评审</div>
              </div>
              <div className="board-summary-progress">
                <Progress percent={percent} strokeColor="#1677ff" />
                <Typography.Text type="secondary">状态由最新评审记录派生</Typography.Text>
              </div>
            </div>
          </Card>

          {assets.length === 0 ? (
            <Empty description="还没有素材，请上传 DICOM、图片或 STL" />
          ) : (
            <div className="asset-grid">
              {assets.map(({ asset, latest_review }) => (
                <Card key={asset.id} hoverable className="asset-card">
                  <div className="asset-card-head">
                    <span className={`asset-icon ${asset.kind}`}>{kindIcon[asset.kind]}</span>
                    <div className="asset-card-title">
                      <div>{asset.source_label}</div>
                      <Typography.Text type="secondary">{kindLabel[asset.kind]}</Typography.Text>
                    </div>
                    <Tag color={statusColor[asset.status]}>{statusLabel[asset.status]}</Tag>
                  </div>
                  <Descriptions column={1} size="small" className="asset-card-meta">
                    <Descriptions.Item label="大小">{formatBytes(asset.size_bytes)}</Descriptions.Item>
                    <Descriptions.Item label="哈希">{asset.sha256.slice(0, 12)}…</Descriptions.Item>
                    <Descriptions.Item label="最近评审">
                      {latest_review ? latest_review.reviewer_name : "暂无"}
                    </Descriptions.Item>
                  </Descriptions>
                  <Button
                    type="primary"
                    ghost
                    block
                    onClick={() => navigate(`/assets/${asset.id}?caseId=${caseId}`)}
                  >
                    查看
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </Page>
  );
}

function AssetPage() {
  const { assetId = "" } = useParams();
  const [params] = useSearchParams();
  const caseId = params.get("caseId") ?? "";
  const board = useQuery({
    queryKey: ["review-board", caseId],
    queryFn: () => fetchReviewBoard(caseId),
    enabled: Boolean(caseId),
  });
  const item = board.data?.assets.find(({ asset }) => asset.id === assetId)?.asset;

  if (!caseId) {
    return (
      <Page title="素材详情" back="/projects">
        <Alert type="warning" title="缺少病例上下文" description="请从病例评审看板进入素材详情。" />
      </Page>
    );
  }
  if (board.isPending) {
    return (
      <Page title="素材详情" back={`/cases/${caseId}`}>
        <div className="state-block">
          <Spin />
        </div>
      </Page>
    );
  }
  if (board.isError) {
    return (
      <Page title="素材详情" back={`/cases/${caseId}`}>
        <ErrorNotice error={board.error} />
      </Page>
    );
  }
  if (!item) {
    return (
      <Page title="素材详情" back={`/cases/${caseId}`}>
        <Result status="warning" title="素材不存在或已被移除" />
      </Page>
    );
  }
  return (
    <Page
      title={item.source_label}
      subtitle={`${board.data?.case.case_code} · 只展示服务端允许的元数据`}
      back={`/cases/${caseId}`}
    >
      <AssetDetail asset={item} caseId={caseId} />
    </Page>
  );
}

function AssetDetail({ asset, caseId }: { asset: Asset; caseId: string }) {
  const client = useQueryClient();
  const [imageFailed, setImageFailed] = useState(false);
  const [form] = Form.useForm<{ decision: Review["decision"]; note?: string; reviewer_name: string }>();
  const [messageApi, contextHolder] = message.useMessage();
  const mutation = useMutation({
    mutationFn: (payload: { decision: Review["decision"]; note?: string; reviewer_name: string }) =>
      reviewAsset(asset.id, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["review-board", caseId] });
      messageApi.success("评审已保存");
      form.resetFields();
    },
  });

  return (
    <div className="asset-detail">
      {contextHolder}
      <Card title="预览" className="preview-card" variant="borderless">
        {asset.kind === "stl" ? (
          <Suspense
            fallback={
              <div className="state-block">
                <Spin tip="正在加载 3D 查看器" />
              </div>
            }
          >
            <StlViewer assetId={asset.id} />
          </Suspense>
        ) : asset.preview_available && !imageFailed ? (
          <img
            className="asset-preview"
            src={assetPreviewUrl(asset.id)}
            alt="素材预览"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <Alert
            type="warning"
            showIcon
            title="图片预览不可用"
            description="请重试，或改看右侧的元数据信息。"
            action={
              <Button size="small" onClick={() => setImageFailed(false)}>
                重试
              </Button>
            }
          />
        )}
      </Card>

      <Card title="白名单元数据" className="metadata-card" variant="borderless">
        {Object.keys(asset.metadata_summary).length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无可展示元数据" />
        ) : (
          <Descriptions column={1} size="small">
            {Object.entries(asset.metadata_summary).map(([key, value]) => (
              <Descriptions.Item key={key} label={key}>
                {String(value)}
              </Descriptions.Item>
            ))}
          </Descriptions>
        )}
        {asset.ingest_warnings.map((warning) => (
          <Alert key={warning} type="warning" showIcon title={warning} className="warning-item" />
        ))}
      </Card>

      <Card title="提交评审" className="review-card" variant="borderless">
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => mutation.mutate(values)}
          initialValues={{ reviewer_name: "interview-reviewer" }}
        >
          <Form.Item name="decision" label="结论" rules={[{ required: true }]}>
            <Select
              placeholder="请选择评审结论"
              options={[
                { value: "accept", label: "通过" },
                { value: "needs_changes", label: "需补充" },
                { value: "reject", label: "拒绝" },
              ]}
            />
          </Form.Item>
          <Form.Item name="note" label="说明">
            <Input.TextArea rows={3} placeholder="记录可验证的素材问题，不填写患者信息" />
          </Form.Item>
          <Form.Item name="reviewer_name" label="评审人" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={mutation.isPending} block>
            保存评审
          </Button>
        </Form>
      </Card>
    </div>
  );
}

export function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      button={{ autoInsertSpace: false }}
      theme={{
        token: {
          borderRadius: 10,
          colorPrimary: "#1668dc",
          colorBgLayout: "#f2f5fa",
          fontSize: 14,
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <Shell>
            <Routes>
              <Route path="/" element={<Navigate to="/projects" replace />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/projects/:projectId" element={<ProjectPage />} />
              <Route path="/cases/:caseId" element={<CasePage />} />
              <Route path="/assets/:assetId" element={<AssetPage />} />
            </Routes>
          </Shell>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}


