import { lazy, Suspense, useMemo, useState, type ReactNode } from "react";
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
  Popconfirm,
  Progress,
  Result,
  Select,
  Space,
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
  SwapOutlined,
} from "@ant-design/icons";
import zhCN from "antd/locale/zh_CN";

import {
  ApiError,
  assetPreviewUrl,
  createAnnotation,
  createCase,
  createProject,
  deleteAnnotation,
  deleteAsset,
  fetchAnnotations,
  fetchCases,
  fetchProjects,
  fetchReviewBoard,
  reviewAsset,
  updateAsset,
  uploadAsset,
  type Annotation,
  type Asset,
  type Review,
} from "../shared/api/client";
import { markerColor } from "../shared/markerColors";
import type { MarkerPoint } from "../features/viewer/StlViewer";

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
      message={apiError?.message ?? "页面加载失败"}
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
        <Tag className="env-tag">工程评审原型 · 不用于临床</Tag>
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

function CompareModal({
  open,
  onClose,
  images,
}: {
  open: boolean;
  onClose: () => void;
  images: Asset[];
}) {
  const [left, setLeft] = useState<string | undefined>();
  const [right, setRight] = useState<string | undefined>();
  const options = images.map((asset) => ({
    value: asset.id,
    label: `${asset.tags.length > 0 ? asset.tags.join("、") : asset.source_label} · ${asset.id.slice(0, 8)}`,
  }));
  const leftAsset = images.find((asset) => asset.id === left);
  const rightAsset = images.find((asset) => asset.id === right);

  return (
    <Modal title="图片并排比较" open={open} onCancel={onClose} footer={null} width={1000}>
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="选择左侧图片"
          aria-label="左侧图片"
          style={{ width: 320 }}
          options={options.filter((option) => option.value !== right)}
          value={leftAsset?.id}
          onChange={setLeft}
        />
        <Select
          placeholder="选择右侧图片"
          aria-label="右侧图片"
          style={{ width: 320 }}
          options={options.filter((option) => option.value !== left)}
          value={rightAsset?.id}
          onChange={setRight}
        />
      </Space>
      <div className="compare-grid">
        {leftAsset ? (
          <img src={assetPreviewUrl(leftAsset.id)} alt="左侧素材" />
        ) : (
          <Empty description="选择左侧图片" />
        )}
        {rightAsset ? (
          <img src={assetPreviewUrl(rightAsset.id)} alt="右侧素材" />
        ) : (
          <Empty description="选择右侧图片" />
        )}
      </div>
    </Modal>
  );
}

function CasePage() {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [kindFilter, setKindFilter] = useState<string | undefined>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [tagFilter, setTagFilter] = useState<string | undefined>();
  const [compareOpen, setCompareOpen] = useState(false);
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

  const assets = useMemo(() => board.data?.assets ?? [], [board.data]);
  const allTags = useMemo(
    () => Array.from(new Set(assets.flatMap((item) => item.asset.tags))).sort(),
    [assets],
  );
  const visible = assets.filter(
    ({ asset }) =>
      (!kindFilter || asset.kind === kindFilter) &&
      (!statusFilter || asset.status === statusFilter) &&
      (!tagFilter || asset.tags.includes(tagFilter)),
  );
  const images = assets.map((item) => item.asset).filter((asset) => asset.kind === "image");
  const reviewed = assets.filter((item) => item.asset.status !== "pending").length;
  const percent = assets.length === 0 ? 0 : Math.round((reviewed / assets.length) * 100);

  return (
    <Page
      title={board.data?.case ? `${board.data.case.case_code} · ${board.data.case.title}` : "病例评审看板"}
      subtitle="先上传素材，再逐项确认状态与评审结论。"
      back={board.data?.case ? `/projects/${board.data.case.project_id}` : "/projects"}
      action={
        <Space>
          <Button
            icon={<SwapOutlined />}
            disabled={images.length < 2}
            onClick={() => setCompareOpen(true)}
          >
            图片比较
          </Button>
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
        </Space>
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
                <Progress percent={percent} strokeColor="#1668dc" />
                <Typography.Text type="secondary">状态由最新评审记录派生</Typography.Text>
              </div>
            </div>
          </Card>

          {assets.length === 0 ? (
            <Empty description="还没有素材，请上传 DICOM、图片或 STL" />
          ) : (
            <>
              <Space wrap className="board-filters">
                <Select
                  allowClear
                  placeholder="类型"
                  style={{ width: 140 }}
                  value={kindFilter}
                  onChange={setKindFilter}
                  options={[
                    { value: "dicom", label: "DICOM" },
                    { value: "image", label: "图片" },
                    { value: "stl", label: "3D 模型" },
                  ]}
                />
                <Select
                  allowClear
                  placeholder="状态"
                  style={{ width: 140 }}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  options={Object.entries(statusLabel).map(([value, label]) => ({ value, label }))}
                />
                <Select
                  allowClear
                  placeholder="标签"
                  style={{ width: 180 }}
                  value={tagFilter}
                  onChange={setTagFilter}
                  options={allTags.map((tag) => ({ value: tag, label: tag }))}
                />
              </Space>

              {visible.length === 0 ? (
                <Empty description="没有符合筛选条件的素材" />
              ) : (
                <div className="asset-grid">
                  {visible.map(({ asset, latest_review }) => (
                    <Card key={asset.id} hoverable className="asset-card">
                      <div className="asset-card-head">
                        <span className={`asset-icon ${asset.kind}`}>{kindIcon[asset.kind]}</span>
                        <div className="asset-card-title">
                          <div>{asset.source_label}</div>
                          <Typography.Text type="secondary">{kindLabel[asset.kind]}</Typography.Text>
                        </div>
                        <Tag color={statusColor[asset.status]}>{statusLabel[asset.status]}</Tag>
                      </div>
                      {asset.tags.length > 0 && (
                        <div className="asset-card-tags">
                          {asset.tags.map((tag) => (
                            <Tag key={tag} bordered={false}>
                              {tag}
                            </Tag>
                          ))}
                        </div>
                      )}
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
        </>
      )}
      <CompareModal open={compareOpen} onClose={() => setCompareOpen(false)} images={images} />
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
        <Alert type="warning" message="缺少病例上下文" description="请从病例评审看板进入素材详情。" />
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
  const navigate = useNavigate();
  const [imageFailed, setImageFailed] = useState(false);
  const [reviewForm] = Form.useForm<{ decision: Review["decision"]; note?: string; reviewer_name: string }>();
  const [organizeForm] = Form.useForm<{ tags: string[]; note?: string }>();
  const [markerForm] = Form.useForm<{ label: string }>();
  const [pendingMarker, setPendingMarker] = useState<MarkerPoint | null>(null);
  const [highlightMarkerId, setHighlightMarkerId] = useState<string | null>(null);
  const [messageApi, contextHolder] = message.useMessage();
  const { message: globalMessage } = AntApp.useApp();

  const annotations = useQuery({
    queryKey: ["annotations", asset.id],
    queryFn: () => fetchAnnotations(asset.id),
  });

  const reviewMutation = useMutation({
    mutationFn: (payload: { decision: Review["decision"]; note?: string; reviewer_name: string }) =>
      reviewAsset(asset.id, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["review-board", caseId] });
      messageApi.success("评审已保存");
      reviewForm.resetFields();
    },
  });
  const organizeMutation = useMutation({
    mutationFn: (payload: { tags?: string[]; note?: string | null }) => updateAsset(asset.id, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["review-board", caseId] });
      messageApi.success("标签与备注已保存");
    },
  });
  const addMarkerMutation = useMutation({
    mutationFn: (payload: { label: string; data: MarkerPoint }) =>
      createAnnotation(asset.id, { label: payload.label, data: payload.data }),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["annotations", asset.id] });
      messageApi.success("结构标记已保存");
      setPendingMarker(null);
      markerForm.resetFields();
    },
  });
  const deleteMarkerMutation = useMutation({
    mutationFn: (annotationId: string) => deleteAnnotation(annotationId),
    onSuccess: () => client.invalidateQueries({ queryKey: ["annotations", asset.id] }),
  });
  const deleteAssetMutation = useMutation({
    mutationFn: () => deleteAsset(asset.id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["review-board", caseId] });
      globalMessage.success("素材已删除");
      navigate(`/cases/${caseId}`);
    },
    onError: (error) => messageApi.error(error instanceof ApiError ? error.nextAction : "删除失败"),
  });

  const markers = annotations.data ?? [];

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
            <StlViewer
              assetId={asset.id}
              markers={markers}
              onPlaceMarker={(point) => setPendingMarker(point)}
              highlightId={highlightMarkerId}
            />
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
            message="图片预览不可用"
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
          <Alert key={warning} type="warning" showIcon message={warning} className="warning-item" />
        ))}
      </Card>

      <Card title="标签与备注" className="organize-card" variant="borderless">
        <Form
          form={organizeForm}
          layout="vertical"
          initialValues={{ tags: asset.tags, note: asset.note ?? undefined }}
          onFinish={(values) => organizeMutation.mutate({ tags: values.tags, note: values.note ?? null })}
        >
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入后回车，例如：瓣膜 / 待补图" tokenSeparators={[",", "，"]} />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} placeholder="素材整理说明，不填写患者信息" />
          </Form.Item>
          <Button htmlType="submit" loading={organizeMutation.isPending} block>
            保存标签与备注
          </Button>
        </Form>
      </Card>

      {asset.kind === "stl" && (
        <Card title="结构标记" className="marker-card" variant="borderless">
          <Typography.Paragraph type="secondary">
            在左侧模型上点击即可添加标记点。
          </Typography.Paragraph>
          {markers.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有标记点" />
          ) : (
            <div className="marker-list">
              {markers.map((marker: Annotation, index: number) => (
                <div
                  key={marker.id}
                  className="marker-item"
                  onMouseEnter={() => setHighlightMarkerId(marker.id)}
                  onMouseLeave={() => setHighlightMarkerId(null)}
                >
                  <span
                    className="marker-dot"
                    style={{ background: markerColor(index), boxShadow: `0 0 0 3px ${markerColor(index)}33` }}
                  />
                  <span className="marker-index">{index + 1}</span>
                  <span className="marker-label">{marker.label}</span>
                  <Button
                    size="small"
                    type="text"
                    danger
                    onClick={() => deleteMarkerMutation.mutate(marker.id)}
                  >
                    删除
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      <Card title="提交评审" className="review-card" variant="borderless">
        <Form
          form={reviewForm}
          layout="vertical"
          onFinish={(values) => reviewMutation.mutate(values)}
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
          <Button type="primary" htmlType="submit" loading={reviewMutation.isPending} block>
            保存评审
          </Button>
        </Form>
      </Card>

      <Card title="危险操作" className="review-card" variant="borderless">
        <Popconfirm
          title="确认删除该素材？"
          description="已评审的素材不能硬删除；删除后不可恢复。"
          okText="删除"
          okButtonProps={{ danger: true }}
          onConfirm={() => deleteAssetMutation.mutate()}
        >
          <Button danger block loading={deleteAssetMutation.isPending}>
            删除素材
          </Button>
        </Popconfirm>
      </Card>

      <Modal
        title="添加结构标记"
        open={pendingMarker !== null}
        onCancel={() => {
          setPendingMarker(null);
          markerForm.resetFields();
        }}
        onOk={() => markerForm.submit()}
        confirmLoading={addMarkerMutation.isPending}
        destroyOnHidden
      >
        <Form
          form={markerForm}
          layout="vertical"
          onFinish={(values) => {
            if (pendingMarker) {
              addMarkerMutation.mutate({ label: values.label, data: pendingMarker });
            }
          }}
        >
          <Form.Item name="label" label="结构名称" rules={[{ required: true }]}>
            <Input placeholder="例如：主动脉瓣环" />
          </Form.Item>
        </Form>
      </Modal>
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
