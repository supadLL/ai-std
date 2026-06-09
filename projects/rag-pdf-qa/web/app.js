const PREFERENCES_KEY = "ragPdfQaUiPreferences";
const AUTH_TOKEN_KEY = "ragPdfQaAccessToken";
const DEFAULT_BACKGROUND_COLOR = "#0f1213";

const state = {
  accessToken: localStorage.getItem(AUTH_TOKEN_KEY) || "",
  currentUser: null,
  knowledgeBases: [],
  activeKnowledgeBaseId: "",
  documents: [],
  indexJobs: [],
  indexJobPollingHandle: null,
  hadActiveIndexJobs: false,
  lastAnswer: null,
  messages: [],
  evaluation: null,
  evaluationRuns: [],
  askMode: "rag",
  selectedDocumentIds: new Set(),
  activeDocumentId: null,
  availableProviders: [],
  llmProfiles: [],
  activeProfileId: "",
  adminUsers: [],
  knowledgeBaseMembers: [],
  preferences: loadPreferences(),
};

const els = {
  uploadForm: document.querySelector("#uploadForm"),
  fileInput: document.querySelector("#fileInput"),
  filePicker: document.querySelector("#filePicker"),
  chooseFileButton: document.querySelector("#chooseFileButton"),
  fileNameDisplay: document.querySelector("#fileNameDisplay"),
  chunkSize: document.querySelector("#chunkSize"),
  overlap: document.querySelector("#overlap"),
  reindex: document.querySelector("#reindex"),
  documentList: document.querySelector("#documentList"),
  refreshDocuments: document.querySelector("#refreshDocuments"),
  documentNameFilter: document.querySelector("#documentNameFilter"),
  documentTypeFilter: document.querySelector("#documentTypeFilter"),
  selectedDocumentCount: document.querySelector("#selectedDocumentCount"),
  clearDocumentFilters: document.querySelector("#clearDocumentFilters"),
  batchDeleteDocuments: document.querySelector("#batchDeleteDocuments"),
  documentDetail: document.querySelector("#documentDetail"),
  indexJobList: document.querySelector("#indexJobList"),
  refreshIndexJobs: document.querySelector("#refreshIndexJobs"),
  askForm: document.querySelector("#askForm"),
  askModeButtons: Array.from(document.querySelectorAll("[data-ask-mode]")),
  questionInput: document.querySelector("#questionInput"),
  topK: document.querySelector("#topK"),
  scoreThreshold: document.querySelector("#scoreThreshold"),
  askDocumentFilter: document.querySelector("#askDocumentFilter"),
  answerOutput: document.querySelector("#answerOutput"),
  sourceList: document.querySelector("#sourceList"),
  debugGrid: document.querySelector("#debugGrid"),
  statusPill: document.querySelector("#statusPill"),
  evaluationForm: document.querySelector("#evaluationForm"),
  evaluationTopK: document.querySelector("#evaluationTopK"),
  evaluationThreshold: document.querySelector("#evaluationThreshold"),
  evaluationStatus: document.querySelector("#evaluationStatus"),
  evaluationSummary: document.querySelector("#evaluationSummary"),
  evaluationHistory: document.querySelector("#evaluationHistory"),
  evaluationCases: document.querySelector("#evaluationCases"),
  reloadEvaluation: document.querySelector("#reloadEvaluation"),
  reloadEvaluationRuns: document.querySelector("#reloadEvaluationRuns"),
  toast: document.querySelector("#toast"),
  tabButtons: Array.from(document.querySelectorAll(".tab-button")),
  tabPages: Array.from(document.querySelectorAll(".tab-page")),
  settingsForm: document.querySelector("#settingsForm"),
  profileTableBody: document.querySelector("#profileTableBody"),
  addProfileButton: document.querySelector("#addProfileButton"),
  profileModal: document.querySelector("#profileModal"),
  profileForm: document.querySelector("#profileForm"),
  profileModalTitle: document.querySelector("#profileModalTitle"),
  closeProfileModal: document.querySelector("#closeProfileModal"),
  cancelProfileModal: document.querySelector("#cancelProfileModal"),
  profileIdInput: document.querySelector("#profileIdInput"),
  profileNameInput: document.querySelector("#profileNameInput"),
  providerInput: document.querySelector("#providerInput"),
  baseUrlInput: document.querySelector("#baseUrlInput"),
  modelInput: document.querySelector("#modelInput"),
  apiKeyInput: document.querySelector("#apiKeyInput"),
  timeoutInput: document.querySelector("#timeoutInput"),
  clearApiKeyInput: document.querySelector("#clearApiKeyInput"),
  activateProfileInput: document.querySelector("#activateProfileInput"),
  systemPromptInput: document.querySelector("#systemPromptInput"),
  answerPromptInput: document.querySelector("#answerPromptInput"),
  modelOptions: document.querySelector("#modelOptions"),
  settingsStatus: document.querySelector("#settingsStatus"),
  reloadSettings: document.querySelector("#reloadSettings"),
  languageButtons: Array.from(document.querySelectorAll("[data-language]")),
  colorButtons: Array.from(document.querySelectorAll(".color-swatch[data-theme-color]")),
  customColorInput: document.querySelector("#customColorInput"),
  backgroundColorInput: document.querySelector("#backgroundColorInput"),
  resetBackgroundColor: document.querySelector("#resetBackgroundColor"),
  authPanel: document.querySelector("#authPanel"),
  appShell: document.querySelector("#appShell"),
  authForm: document.querySelector("#authForm"),
  authUsername: document.querySelector("#authUsername"),
  authPassword: document.querySelector("#authPassword"),
  registerUser: document.querySelector("#registerUser"),
  bootstrapAdmin: document.querySelector("#bootstrapAdmin"),
  logoutButton: document.querySelector("#logoutButton"),
  currentUserLabel: document.querySelector("#currentUserLabel"),
  knowledgeBaseSelect: document.querySelector("#knowledgeBaseSelect"),
  knowledgeBaseForm: document.querySelector("#knowledgeBaseForm"),
  knowledgeBaseNameInput: document.querySelector("#knowledgeBaseNameInput"),
  reloadTeamAccess: document.querySelector("#reloadTeamAccess"),
  adminUsersBlock: document.querySelector("#adminUsersBlock"),
  adminUserForm: document.querySelector("#adminUserForm"),
  adminUsernameInput: document.querySelector("#adminUsernameInput"),
  adminPasswordInput: document.querySelector("#adminPasswordInput"),
  adminUserList: document.querySelector("#adminUserList"),
  memberForm: document.querySelector("#memberForm"),
  memberUsernameInput: document.querySelector("#memberUsernameInput"),
  memberList: document.querySelector("#memberList"),
};

const THEME_COLORS = {
  teal: { accent: "#37d0b2", accent2: "#ffb86b" },
  blue: { accent: "#5aa7ff", accent2: "#8ee6ff" },
  violet: { accent: "#9b8cff", accent2: "#f0b3ff" },
  rose: { accent: "#ff7aa2", accent2: "#ffd166" },
};

const translations = {
  zh: {
    "app.eyebrow": "Local RAG",
    "app.title": "本地知识库 RAG Agent",
    "app.documentTitle": "本地 RAG Agent | 知识库问答",
    "nav.aria": "主功能",
    "nav.import": "文件导入",
    "nav.importSub": "Import",
    "nav.ask": "知识问答",
    "nav.askSub": "Ask",
    "nav.evaluation": "检索评估",
    "nav.evaluationSub": "Eval",
    "nav.settings": "设置",
    "nav.settingsSub": "Settings",
    "nav.docs": "Swagger Docs",
    "kb.current": "Knowledge base",
    "kb.newPlaceholder": "New knowledge base",
    "kb.create": "Create knowledge base",
    "kb.created": "Knowledge base created",
    "jobs.eyebrow": "Jobs",
    "jobs.title": "Index jobs",
    "jobs.refresh": "Refresh index jobs",
    "jobs.empty": "No index jobs",
    "jobs.retry": "Retry",
    "jobs.created": "Index job queued",
    "import.eyebrow": "Import",
    "import.title": "文件导入",
    "import.refresh": "刷新文档列表",
    "import.chooseFile": "选择文件",
    "import.noFile": "未选择文件",
    "import.chunk": "分块大小 chunk",
    "import.overlap": "重叠长度 overlap",
    "import.reindex": "重新索引 reindex",
    "import.submit": "上传索引",
    "library.filenameFilter": "文件名",
    "library.typeFilter": "类型",
    "library.allTypes": "全部",
    "library.clearFilters": "清除筛选",
    "library.batchDelete": "批量删除",
    "library.detail": "详情",
    "library.reindex": "重新索引",
    "library.selected": "selected",
    "library.selectFirst": "请先勾选要删除的文档",
    "library.noMatch": "没有匹配文档",
    "library.confirmDelete": "确认删除选中的文档？",
    "library.deleted": "批量删除完成",
    "library.reindexed": "重建索引完成",
    "ask.eyebrow": "Retrieve",
    "ask.title": "知识问答",
    "ask.empty": "等待问题",
    "ask.placeholder": "输入问题",
    "ask.mode": "模式",
    "ask.ragMode": "RAG",
    "ask.agentMode": "Agent",
    "ask.topK": "检索数量 top_k",
    "ask.threshold": "分数阈值 threshold",
    "ask.document": "限定文档 document",
    "ask.allDocuments": "all",
    "ask.submit": "提问",
    "sources.eyebrow": "Sources",
    "sources.title": "检索来源",
    "evaluation.eyebrow": "Evaluation",
    "evaluation.title": "检索评估",
    "evaluation.topK": "检索数量 top_k",
    "evaluation.threshold": "分数阈值 threshold",
    "evaluation.run": "运行评估",
    "evaluation.reload": "读取最近结果",
    "evaluation.reloadHistory": "刷新历史",
    "evaluation.history": "评估历史",
    "evaluation.quality": "质量门禁",
    "evaluation.empty": "暂无评估结果",
    "evaluation.dataset": "数据集 dataset",
    "evaluation.cases": "用例 cases",
    "evaluation.hitRate": "命中率 hit_rate",
    "evaluation.pageHitRate": "页码命中 page_hit",
    "evaluation.keywordHitRate": "关键词命中 keyword_hit",
    "evaluation.lowScore": "低分结果 low_score",
    "evaluation.generatedAt": "生成时间 generated",
    "evaluation.caseHit": "hit",
    "evaluation.caseMiss": "miss",
    "settings.eyebrow": "Settings",
    "settings.title": "模型与提示词",
    "preferences.title": "界面偏好",
    "preferences.language": "语言",
    "preferences.color": "系统颜色",
    "preferences.background": "背景颜色",
    "preferences.customColor": "自定义颜色",
    "preferences.resetBackground": "恢复默认",
    "settings.profileEyebrow": "LLM Profiles",
    "settings.profileTitle": "模型 API 配置",
    "settings.addProfile": "+ 新增 API",
    "settings.profileProvider": "供应商 Provider",
    "settings.profileKey": "密钥 API Key",
    "settings.profileModel": "模型 Model",
    "settings.profileEnabled": "启用状态 Active",
    "settings.profileActions": "操作 Actions",
    "settings.profileModalEyebrow": "Model API",
    "settings.profileCreateTitle": "新增 API 配置",
    "settings.profileEditTitle": "编辑 API 配置",
    "settings.profileName": "名称",
    "settings.activateAfterSave": "保存后启用此配置",
    "settings.saveProfile": "保存配置",
    "settings.cancel": "取消",
    "settings.enabled": "启用中",
    "settings.enable": "启用",
    "settings.edit": "编辑",
    "settings.delete": "删除",
    "settings.noProfiles": "暂无模型配置",
    "settings.provider": "模型供应商 Provider",
    "settings.baseUrl": "接口地址 API Base URL",
    "settings.model": "模型名称 LLM Model",
    "settings.apiKey": "接口密钥 API Key",
    "settings.timeout": "超时时间 Timeout",
    "settings.clearApiKey": "清除本地运行时 API Key",
    "settings.systemPrompt": "RAG 系统提示词 RAG System Prompt",
    "settings.answerPrompt": "RAG 回答指令 RAG Answer Instructions",
    "settings.save": "保存设置",
    "settings.reload": "重新读取",
    "labels.chunk": "分块大小 chunk",
    "labels.overlap": "重叠长度 overlap",
    "labels.reindex": "重新索引 reindex",
    "labels.topK": "检索数量 top_k",
    "labels.threshold": "分数阈值 threshold",
    "labels.provider": "模型供应商 Provider",
    "labels.baseUrl": "接口地址 API Base URL",
    "labels.model": "模型名称 LLM Model",
    "labels.apiKey": "接口密钥 API Key",
    "labels.timeout": "超时时间 Timeout",
    "labels.systemPrompt": "RAG 系统提示词 RAG System Prompt",
    "labels.answerPrompt": "RAG 回答指令 RAG Answer Instructions",
    "settings.apiKeyPlaceholder": "留空则不修改已配置密钥",
    "documents.empty": "暂无文档",
    "documents.chunks": "分块 chunks",
    "documents.noHash": "no-hash",
    "sources.empty": "无 sources",
    "debug.retrieved": "检索数量 retrieved",
    "debug.sources": "来源 sources",
    "debug.model": "模型 model",
    "debug.tokens": "令牌 tokens",
    "debug.route": "路由 route",
    "debug.tools": "工具 tools",
    "debug.reason": "原因 reason",
    "debug.fallback": "兜底 fallback",
    "message.pendingMeta": "AI 正在解析检索结果",
    "message.pendingText": "整理答案中",
    "message.requestFailed": "请求失败",
    "toast.chooseFile": "请选择文件",
    "toast.indexDone": "索引完成",
    "toast.enterQuestion": "请输入问题",
    "toast.settingsSaved": "设置已保存",
    "toast.profileSaved": "模型配置已保存",
    "toast.profileActivated": "模型配置已启用",
    "toast.profileDeleted": "模型配置已删除",
    "toast.cannotDeleteActive": "启用中的配置不能删除",
    "toast.languageChanged": "语言已切换",
    "toast.feedbackSaved": "反馈已记录",
    "toast.colorChanged": "系统色已更新",
    "toast.backgroundChanged": "背景色已更新",
    "status.idle": "idle",
    "status.loading": "loading",
    "status.indexing": "indexing",
    "status.asking": "asking",
    "status.evaluating": "evaluating",
    "status.done": "done",
    "status.error": "error",
    "settingsStatus.loading": "loading",
    "settingsStatus.saving": "saving",
    "settingsStatus.error": "error",
    "settingsStatus.noKey": "no-key",
    "settingsStatus.key": "key",
    "auth.register": "Register",
    "team.eyebrow": "Team Access",
    "team.title": "Users and members",
    "team.reload": "Refresh access",
    "team.users": "Users",
    "team.members": "Knowledge base members",
    "team.usernamePlaceholder": "username",
    "team.passwordPlaceholder": "temporary password",
    "team.createUser": "Create",
    "team.addMember": "Add",
    "team.emptyUsers": "No users",
    "team.emptyMembers": "No members",
    "team.noKnowledgeBase": "Select a knowledge base first",
    "team.noPermission": "Owner or admin access required",
    "team.remove": "Remove",
    "team.createdUser": "User created",
    "team.addedMember": "Member added",
    "team.removedMember": "Member removed",
  },
  en: {
    "app.eyebrow": "Local RAG",
    "app.title": "Local Knowledge RAG Agent",
    "app.documentTitle": "Local RAG Agent | Knowledge QA",
    "nav.aria": "Main functions",
    "nav.import": "Import Files",
    "nav.importSub": "Import",
    "nav.ask": "Knowledge Q&A",
    "nav.askSub": "Ask",
    "nav.evaluation": "Evaluation",
    "nav.evaluationSub": "Eval",
    "nav.settings": "Settings",
    "nav.settingsSub": "Settings",
    "nav.docs": "Swagger Docs",
    "kb.current": "Knowledge base",
    "kb.newPlaceholder": "New knowledge base",
    "kb.create": "Create knowledge base",
    "kb.created": "Knowledge base created",
    "jobs.eyebrow": "Jobs",
    "jobs.title": "Index jobs",
    "jobs.refresh": "Refresh index jobs",
    "jobs.empty": "No index jobs",
    "jobs.retry": "Retry",
    "jobs.created": "Index job queued",
    "import.eyebrow": "Import",
    "import.title": "Import Files",
    "import.refresh": "Refresh documents",
    "import.chooseFile": "Choose File",
    "import.noFile": "No file selected",
    "import.chunk": "chunk",
    "import.overlap": "overlap",
    "import.reindex": "reindex",
    "import.submit": "Upload & Index",
    "library.filenameFilter": "Filename",
    "library.typeFilter": "Type",
    "library.allTypes": "All",
    "library.clearFilters": "Clear filters",
    "library.batchDelete": "Batch delete",
    "library.detail": "Details",
    "library.reindex": "Reindex",
    "library.selected": "selected",
    "library.selectFirst": "Select documents first",
    "library.noMatch": "No matching documents",
    "library.confirmDelete": "Delete selected documents?",
    "library.deleted": "Batch delete complete",
    "library.reindexed": "Reindex complete",
    "ask.eyebrow": "Retrieve",
    "ask.title": "Knowledge Q&A",
    "ask.empty": "Waiting for a question",
    "ask.placeholder": "Ask a question",
    "ask.mode": "Mode",
    "ask.ragMode": "RAG",
    "ask.agentMode": "Agent",
    "ask.topK": "top_k",
    "ask.threshold": "threshold",
    "ask.document": "document",
    "ask.allDocuments": "all",
    "ask.submit": "Ask",
    "sources.eyebrow": "Sources",
    "sources.title": "Retrieved Sources",
    "evaluation.eyebrow": "Evaluation",
    "evaluation.title": "Retrieval Evaluation",
    "evaluation.topK": "top_k",
    "evaluation.threshold": "threshold",
    "evaluation.run": "Run Evaluation",
    "evaluation.reload": "Load Latest",
    "evaluation.reloadHistory": "Refresh History",
    "evaluation.history": "Evaluation History",
    "evaluation.quality": "quality",
    "evaluation.empty": "No evaluation result",
    "evaluation.dataset": "Dataset",
    "evaluation.cases": "cases",
    "evaluation.hitRate": "hit_rate",
    "evaluation.pageHitRate": "page_hit",
    "evaluation.keywordHitRate": "keyword_hit",
    "evaluation.lowScore": "low_score",
    "evaluation.generatedAt": "generated",
    "evaluation.caseHit": "hit",
    "evaluation.caseMiss": "miss",
    "settings.eyebrow": "Settings",
    "settings.title": "Model & Prompts",
    "preferences.title": "Interface Preferences",
    "preferences.language": "Language",
    "preferences.color": "System Color",
    "preferences.background": "Background Color",
    "preferences.customColor": "Custom color",
    "preferences.resetBackground": "Reset",
    "settings.profileEyebrow": "LLM Profiles",
    "settings.profileTitle": "Model API Profiles",
    "settings.addProfile": "+ Add API",
    "settings.profileProvider": "Provider",
    "settings.profileKey": "API Key",
    "settings.profileModel": "Model",
    "settings.profileEnabled": "Active",
    "settings.profileActions": "Actions",
    "settings.profileModalEyebrow": "Model API",
    "settings.profileCreateTitle": "Add API Profile",
    "settings.profileEditTitle": "Edit API Profile",
    "settings.profileName": "Name",
    "settings.activateAfterSave": "Activate after saving",
    "settings.saveProfile": "Save Profile",
    "settings.cancel": "Cancel",
    "settings.enabled": "Active",
    "settings.enable": "Enable",
    "settings.edit": "Edit",
    "settings.delete": "Delete",
    "settings.noProfiles": "No model profiles",
    "settings.provider": "Provider",
    "settings.baseUrl": "API Base URL",
    "settings.model": "LLM Model",
    "settings.apiKey": "API Key",
    "settings.timeout": "Timeout",
    "settings.clearApiKey": "Clear local runtime API key",
    "settings.systemPrompt": "RAG System Prompt",
    "settings.answerPrompt": "RAG Answer Instructions",
    "settings.save": "Save Settings",
    "settings.reload": "Reload",
    "labels.chunk": "chunk",
    "labels.overlap": "overlap",
    "labels.reindex": "reindex",
    "labels.topK": "top_k",
    "labels.threshold": "threshold",
    "labels.provider": "Provider",
    "labels.baseUrl": "API Base URL",
    "labels.model": "LLM Model",
    "labels.apiKey": "API Key",
    "labels.timeout": "Timeout",
    "labels.systemPrompt": "RAG System Prompt",
    "labels.answerPrompt": "RAG Answer Instructions",
    "settings.apiKeyPlaceholder": "Leave blank to keep the configured key",
    "documents.empty": "No documents yet",
    "documents.chunks": "chunks",
    "documents.noHash": "no-hash",
    "sources.empty": "No sources",
    "debug.retrieved": "retrieved",
    "debug.sources": "sources",
    "debug.model": "model",
    "debug.tokens": "tokens",
    "debug.route": "route",
    "debug.tools": "tools",
    "debug.reason": "reason",
    "debug.fallback": "fallback",
    "message.pendingMeta": "AI is reading retrieved sources",
    "message.pendingText": "Composing answer",
    "message.requestFailed": "Request failed",
    "toast.chooseFile": "Choose a file first",
    "toast.indexDone": "Indexing complete",
    "toast.enterQuestion": "Enter a question",
    "toast.settingsSaved": "Settings saved",
    "toast.profileSaved": "Model profile saved",
    "toast.profileActivated": "Model profile activated",
    "toast.profileDeleted": "Model profile deleted",
    "toast.cannotDeleteActive": "Active profile cannot be deleted",
    "toast.languageChanged": "Language changed",
    "toast.feedbackSaved": "Feedback recorded",
    "toast.colorChanged": "System color updated",
    "toast.backgroundChanged": "Background color updated",
    "status.idle": "idle",
    "status.loading": "loading",
    "status.indexing": "indexing",
    "status.asking": "asking",
    "status.evaluating": "evaluating",
    "status.done": "done",
    "status.error": "error",
    "settingsStatus.loading": "loading",
    "settingsStatus.saving": "saving",
    "settingsStatus.error": "error",
    "settingsStatus.noKey": "no-key",
    "settingsStatus.key": "key",
    "auth.register": "Register",
    "team.eyebrow": "Team Access",
    "team.title": "Users and members",
    "team.reload": "Refresh access",
    "team.users": "Users",
    "team.members": "Knowledge base members",
    "team.usernamePlaceholder": "username",
    "team.passwordPlaceholder": "temporary password",
    "team.createUser": "Create",
    "team.addMember": "Add",
    "team.emptyUsers": "No users",
    "team.emptyMembers": "No members",
    "team.noKnowledgeBase": "Select a knowledge base first",
    "team.noPermission": "Owner or admin access required",
    "team.remove": "Remove",
    "team.createdUser": "User created",
    "team.addedMember": "Member added",
    "team.removedMember": "Member removed",
  },
};

function setStatus(value) {
  els.statusPill.dataset.status = value;
  els.statusPill.textContent = t(`status.${value}`, value);
}

function setEvaluationStatus(value) {
  if (!els.evaluationStatus) {
    return;
  }
  els.evaluationStatus.dataset.status = value;
  els.evaluationStatus.textContent = t(`status.${value}`, value);
}

function setSettingsStatus(value, source = "") {
  els.settingsStatus.dataset.status = value;
  els.settingsStatus.dataset.source = source;
  if (value === "key") {
    els.settingsStatus.textContent = `${t("settingsStatus.key")}:${source}`;
  } else {
    els.settingsStatus.textContent = t(`settingsStatus.${value}`, value);
  }
}

function showToast(message, isError = false) {
  els.toast.textContent = message;
  els.toast.classList.toggle("danger", isError);
  els.toast.classList.add("show");
  window.setTimeout(() => els.toast.classList.remove("show"), 2600);
}

async function requestJson(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (state.accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${state.accessToken}`);
  }
  const response = await fetch(url, { ...options, headers });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    if (response.status === 401 && !url.startsWith("/auth/login")) {
      clearAuthState();
      showAuthPanel();
    }
    const detail = data?.detail || response.statusText;
    const error = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    error.status = response.status;
    throw error;
  }
  return data;
}

function setAuthState(authData) {
  state.accessToken = authData.access_token || "";
  state.currentUser = authData.user || null;
  localStorage.setItem(AUTH_TOKEN_KEY, state.accessToken);
  renderAuthState();
}

function clearAuthState() {
  state.accessToken = "";
  state.currentUser = null;
  state.knowledgeBases = [];
  state.activeKnowledgeBaseId = "";
  state.documents = [];
  state.indexJobs = [];
  state.hadActiveIndexJobs = false;
  state.adminUsers = [];
  state.knowledgeBaseMembers = [];
  stopIndexJobPolling();
  state.selectedDocumentIds.clear();
  state.activeDocumentId = null;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  renderAuthState();
  renderKnowledgeBases();
  renderIndexJobs();
  renderDocumentControls();
  renderDocuments();
  renderAdminUsers();
  renderKnowledgeBaseMembers();
}

function showAuthPanel() {
  els.authPanel.hidden = false;
  els.appShell.classList.add("auth-locked");
}

function hideAuthPanel() {
  els.authPanel.hidden = true;
  els.appShell.classList.remove("auth-locked");
}

function renderAuthState() {
  if (els.currentUserLabel) {
    els.currentUserLabel.textContent = state.currentUser
      ? `${state.currentUser.username} / ${state.currentUser.role}`
      : "guest";
  }
}

async function initializeAuthenticatedApp() {
  applyPreferences();
  switchTab("import");

  if (!state.accessToken) {
    showAuthPanel();
    return;
  }

  try {
    const data = await requestJson("/auth/me");
    state.currentUser = data.user;
    hideAuthPanel();
    renderAuthState();
    await loadKnowledgeBases();
    await Promise.all([loadDocuments(), loadIndexJobs(), loadSettings(), loadTeamAccess()]);
  } catch (error) {
    clearAuthState();
    showAuthPanel();
  }
}

async function submitAuth(event) {
  event.preventDefault();
  await authenticateWith("/auth/login");
}

async function bootstrapAdmin() {
  await authenticateWith("/auth/bootstrap-admin");
}

async function registerUser() {
  await authenticateWith("/auth/register");
}

async function authenticateWith(endpoint) {
  const payload = {
    username: els.authUsername.value.trim(),
    password: els.authPassword.value,
  };
  try {
    const data = await requestJson(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setAuthState(data);
    hideAuthPanel();
    showToast("Signed in");
    await loadKnowledgeBases();
    await Promise.all([loadDocuments(), loadIndexJobs(), loadSettings(), loadTeamAccess()]);
  } catch (error) {
    showToast(error.message, true);
  }
}

async function logout() {
  try {
    if (state.accessToken) {
      await requestJson("/auth/logout", { method: "POST" });
    }
  } catch {
    // Local logout still clears the client token.
  }
  clearAuthState();
  showAuthPanel();
  showToast("Signed out");
}

async function loadKnowledgeBases() {
  const data = await requestJson("/knowledge-bases");
  state.knowledgeBases = data.knowledge_bases || [];
  const fallbackId = data.default_knowledge_base_id || state.knowledgeBases[0]?.knowledge_base_id || "";
  if (!state.knowledgeBases.some((item) => item.knowledge_base_id === state.activeKnowledgeBaseId)) {
    state.activeKnowledgeBaseId = fallbackId;
  }
  renderKnowledgeBases();
}

function renderKnowledgeBases() {
  if (!els.knowledgeBaseSelect) {
    return;
  }
  els.knowledgeBaseSelect.innerHTML = state.knowledgeBases
    .map(
      (knowledgeBase) =>
        `<option value="${escapeHtml(knowledgeBase.knowledge_base_id)}">${escapeHtml(knowledgeBase.name)}</option>`,
    )
    .join("");
  els.knowledgeBaseSelect.value = state.activeKnowledgeBaseId;
}

function knowledgeBasePath(path) {
  if (!state.activeKnowledgeBaseId) {
    return path;
  }
  return `/knowledge-bases/${encodeURIComponent(state.activeKnowledgeBaseId)}${path}`;
}

async function changeKnowledgeBase() {
  state.activeKnowledgeBaseId = els.knowledgeBaseSelect.value || "";
  state.selectedDocumentIds.clear();
  state.activeDocumentId = null;
  state.evaluation = null;
  state.evaluationRuns = [];
  state.indexJobs = [];
  state.hadActiveIndexJobs = false;
  stopIndexJobPolling();
  renderDocumentDetail();
  renderIndexJobs();
  await Promise.all([loadDocuments(), loadIndexJobs(), loadTeamAccess()]);
}

async function createKnowledgeBase(event) {
  event.preventDefault();
  const name = els.knowledgeBaseNameInput.value.trim();
  if (!name) {
    return;
  }
  try {
    const knowledgeBase = await requestJson("/knowledge-bases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    state.activeKnowledgeBaseId = knowledgeBase.knowledge_base_id;
    els.knowledgeBaseNameInput.value = "";
    await loadKnowledgeBases();
    await Promise.all([loadDocuments(), loadIndexJobs(), loadTeamAccess()]);
    showToast(t("kb.created"));
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadDocuments() {
  setStatus("loading");
  const data = await requestJson(knowledgeBasePath("/documents"));
  state.documents = data.documents || [];
  state.selectedDocumentIds = new Set(
    [...state.selectedDocumentIds].filter((documentId) => state.documents.some((doc) => doc.document_id === documentId)),
  );
  if (state.activeDocumentId && !state.documents.some((doc) => doc.document_id === state.activeDocumentId)) {
    state.activeDocumentId = null;
  }
  renderDocumentControls();
  renderDocuments();
  setStatus("idle");
}

async function loadIndexJobs() {
  if (!els.indexJobList) {
    return;
  }
  const data = await requestJson(knowledgeBasePath("/documents/index-jobs"));
  state.indexJobs = data.jobs || [];
  renderIndexJobs();

  const hasActiveJobs = state.indexJobs.some((job) => ["queued", "running"].includes(job.status));
  if (state.hadActiveIndexJobs && !hasActiveJobs) {
    await loadDocuments();
  }
  state.hadActiveIndexJobs = hasActiveJobs;
  if (hasActiveJobs) {
    startIndexJobPolling();
  } else {
    stopIndexJobPolling();
  }
}

function renderIndexJobs() {
  if (!els.indexJobList) {
    return;
  }
  if (!state.indexJobs.length) {
    els.indexJobList.innerHTML = `<p class="empty-state">${t("jobs.empty")}</p>`;
    return;
  }

  els.indexJobList.innerHTML = state.indexJobs
    .map(
      (job) => `
        <article class="doc-card">
          <div class="doc-title">
            <span>${escapeHtml(job.filename)}</span>
            <span class="job-status ${escapeHtml(job.status)}">${escapeHtml(job.status)}</span>
          </div>
          <div class="meta">
            ${escapeHtml(job.job_id)} · attempts ${job.attempts} · ${escapeHtml(job.progress_message || job.status)}<br />
            chunks ${job.result?.chunk_count ?? "-"} · indexed ${job.result?.indexed_count ?? "-"} · ${escapeHtml(job.updated_at || job.created_at)}
          </div>
          ${job.error_message ? `<p class="preview danger-action">${escapeHtml(job.error_message)}</p>` : ""}
          ${job.status === "failed" ? `<div class="doc-actions"><button class="mini-button" type="button" data-retry-job="${escapeHtml(job.job_id)}">${t("jobs.retry")}</button></div>` : ""}
        </article>
      `,
    )
    .join("");
}

function startIndexJobPolling() {
  if (state.indexJobPollingHandle) {
    return;
  }
  state.indexJobPollingHandle = window.setInterval(() => {
    loadIndexJobs().catch((error) => {
      stopIndexJobPolling();
      showToast(error.message, true);
    });
  }, 2000);
}

function stopIndexJobPolling() {
  if (!state.indexJobPollingHandle) {
    return;
  }
  window.clearInterval(state.indexJobPollingHandle);
  state.indexJobPollingHandle = null;
}

async function loadSettings() {
  if (!els.settingsForm) {
    return;
  }

  setSettingsStatus("loading");
  const data = await requestJson("/settings");
  applySettingsData(data);
}

function activeKnowledgeBase() {
  return state.knowledgeBases.find((knowledgeBase) => knowledgeBase.knowledge_base_id === state.activeKnowledgeBaseId) || null;
}

function canManageActiveKnowledgeBase() {
  return state.currentUser?.role === "admin" || activeKnowledgeBase()?.role === "owner";
}

async function loadTeamAccess() {
  if (!els.memberList) {
    return;
  }

  const isAdmin = state.currentUser?.role === "admin";
  if (els.adminUsersBlock) {
    els.adminUsersBlock.hidden = !isAdmin;
  }

  if (!state.currentUser || !state.activeKnowledgeBaseId) {
    state.adminUsers = [];
    state.knowledgeBaseMembers = [];
    renderAdminUsers();
    renderKnowledgeBaseMembers(t("team.noKnowledgeBase"));
    return;
  }

  if (isAdmin) {
    try {
      const data = await requestJson("/admin/users");
      state.adminUsers = data.users || [];
    } catch (error) {
      state.adminUsers = [];
      if (error.status !== 403) {
        showToast(error.message, true);
      }
    }
  } else {
    state.adminUsers = [];
  }
  renderAdminUsers();

  if (!canManageActiveKnowledgeBase()) {
    state.knowledgeBaseMembers = [];
    renderKnowledgeBaseMembers(t("team.noPermission"));
    return;
  }

  try {
    const data = await requestJson(knowledgeBasePath("/members"));
    state.knowledgeBaseMembers = data.members || [];
    renderKnowledgeBaseMembers();
  } catch (error) {
    state.knowledgeBaseMembers = [];
    if (error.status === 403) {
      renderKnowledgeBaseMembers(t("team.noPermission"));
      return;
    }
    renderKnowledgeBaseMembers(error.message);
    showToast(error.message, true);
  }
}

function renderAdminUsers() {
  if (!els.adminUserList) {
    return;
  }
  if (!state.adminUsers.length) {
    els.adminUserList.innerHTML = `<p class="empty-state compact-empty">${t("team.emptyUsers")}</p>`;
    return;
  }
  els.adminUserList.innerHTML = state.adminUsers
    .map(
      (user) => `
        <div class="management-row">
          <div class="management-meta">
            <b>${escapeHtml(user.username)}</b>
            <span>${escapeHtml(user.user_id)} · ${escapeHtml(user.status)} · ${formatDateTime(user.created_at)}</span>
          </div>
          <span class="type-pill">${escapeHtml(user.role)}</span>
        </div>
      `,
    )
    .join("");
}

function renderKnowledgeBaseMembers(message = "") {
  if (!els.memberList) {
    return;
  }
  const canManage = Boolean(state.currentUser && state.activeKnowledgeBaseId && canManageActiveKnowledgeBase());
  if (els.memberForm) {
    els.memberForm.hidden = !canManage;
  }
  if (message) {
    els.memberList.innerHTML = `<p class="empty-state compact-empty">${escapeHtml(message)}</p>`;
    return;
  }
  if (!state.currentUser || !state.activeKnowledgeBaseId) {
    els.memberList.innerHTML = `<p class="empty-state compact-empty">${t("team.noKnowledgeBase")}</p>`;
    return;
  }
  if (!canManage && state.currentUser && state.activeKnowledgeBaseId) {
    els.memberList.innerHTML = `<p class="empty-state compact-empty">${t("team.noPermission")}</p>`;
    return;
  }
  if (!state.knowledgeBaseMembers.length) {
    els.memberList.innerHTML = `<p class="empty-state compact-empty">${t("team.emptyMembers")}</p>`;
    return;
  }

  const ownerCount = state.knowledgeBaseMembers.filter((member) => member.role === "owner").length;
  els.memberList.innerHTML = state.knowledgeBaseMembers
    .map((member) => {
      const isLastOwner = member.role === "owner" && ownerCount <= 1;
      const canRemove = canManage && !isLastOwner;
      return `
        <div class="management-row">
          <div class="management-meta">
            <b>${escapeHtml(member.username)}</b>
            <span>${escapeHtml(member.user_id)} · ${formatDateTime(member.created_at)}</span>
          </div>
          <div class="management-actions">
            <span class="type-pill">${escapeHtml(member.role)}</span>
            <button
              class="mini-button danger-button"
              type="button"
              data-member-remove="${escapeHtml(member.user_id)}"
              ${canRemove ? "" : "disabled"}
            >
              ${t("team.remove")}
            </button>
          </div>
        </div>
      `;
    })
    .join("");
}

async function createAdminUser(event) {
  event.preventDefault();
  const username = els.adminUsernameInput.value.trim();
  const password = els.adminPasswordInput.value;
  if (!username || !password) {
    return;
  }
  try {
    await requestJson("/admin/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    els.adminUsernameInput.value = "";
    els.adminPasswordInput.value = "";
    await loadTeamAccess();
    showToast(t("team.createdUser"));
  } catch (error) {
    showToast(error.message, true);
  }
}

async function addKnowledgeBaseMember(event) {
  event.preventDefault();
  const username = els.memberUsernameInput.value.trim();
  if (!username) {
    return;
  }
  try {
    await requestJson(knowledgeBasePath("/members"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });
    els.memberUsernameInput.value = "";
    await loadTeamAccess();
    showToast(t("team.addedMember"));
  } catch (error) {
    showToast(error.message, true);
  }
}

function handleMemberListClick(event) {
  const removeButton = event.target.closest("[data-member-remove]");
  if (!removeButton || removeButton.disabled) {
    return;
  }
  removeKnowledgeBaseMember(removeButton.dataset.memberRemove).catch((error) => showToast(error.message, true));
}

async function removeKnowledgeBaseMember(userId) {
  await requestJson(knowledgeBasePath(`/members/${encodeURIComponent(userId)}`), {
    method: "DELETE",
  });
  await loadTeamAccess();
  showToast(t("team.removedMember"));
}

function applySettingsData(data) {
  state.availableProviders = data.available_providers || [];
  state.llmProfiles = data.llm_profiles || [];
  state.activeProfileId = data.active_llm_profile_id || "";
  const provider = data.llm_provider || "deepseek";
  renderProviderOptions(provider);
  els.providerInput.value = provider;
  renderModelOptions();
  els.baseUrlInput.value = data.llm_base_url || data.deepseek_base_url || "";
  els.modelInput.value = data.llm_model || data.deepseek_model || "";
  els.profileNameInput.value = "";
  els.timeoutInput.value = data.request_timeout_seconds || 30;
  els.apiKeyInput.value = "";
  els.clearApiKeyInput.checked = false;
  els.activateProfileInput.checked = false;
  els.systemPromptInput.value = data.rag_system_prompt || "";
  els.answerPromptInput.value = data.rag_answer_instructions || "";
  renderProfileTable();
  setSettingsStatus(data.llm_api_key_configured ? "key" : "noKey", data.llm_api_key_source);
}

function renderProviderOptions(selectedProvider = "deepseek") {
  if (!els.providerInput) {
    return;
  }
  const providers = state.availableProviders.length
    ? state.availableProviders
    : [{ provider: selectedProvider, label: selectedProvider, default_base_url: "", default_models: [] }];
  els.providerInput.innerHTML = providers
    .map((provider) => {
      const value = escapeHtml(provider.provider);
      const label = escapeHtml(provider.label || provider.provider);
      return `<option value="${value}">${label}</option>`;
    })
    .join("");
}

function getSelectedProviderOption() {
  const selected = els.providerInput?.value || "deepseek";
  return state.availableProviders.find((provider) => provider.provider === selected) || null;
}

function renderModelOptions() {
  if (!els.modelOptions) {
    return;
  }
  const provider = getSelectedProviderOption();
  const models = provider?.default_models || [];
  els.modelOptions.innerHTML = models.map((model) => `<option value="${escapeHtml(model)}"></option>`).join("");
}

function applyProviderDefaults() {
  const provider = getSelectedProviderOption();
  renderModelOptions();
  if (!provider) {
    return;
  }
  if (provider.default_base_url) {
    els.baseUrlInput.value = provider.default_base_url;
  }
  if (provider.default_models?.length) {
    els.modelInput.value = provider.default_models[0];
  } else if (provider.provider === "custom_openai_compatible") {
    els.modelInput.value = "";
  }
}

function providerLabel(providerId) {
  const provider = state.availableProviders.find((item) => item.provider === providerId);
  return provider?.label || providerId;
}

function renderProfileTable() {
  if (!els.profileTableBody) {
    return;
  }
  if (!state.llmProfiles.length) {
    els.profileTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="profile-empty">${t("settings.noProfiles")}</td>
      </tr>
    `;
    return;
  }
  els.profileTableBody.innerHTML = state.llmProfiles
    .map((profile) => {
      const enabled = profile.enabled || profile.profile_id === state.activeProfileId;
      return `
        <tr class="${enabled ? "active-profile" : ""}">
          <td>
            <b>${escapeHtml(profile.name || providerLabel(profile.provider))}</b>
            <span>${escapeHtml(providerLabel(profile.provider))}</span>
          </td>
          <td>
            <span class="key-chip ${profile.api_key_configured ? "configured" : ""}">
              ${profile.api_key_configured ? escapeHtml(profile.api_key_label || "SK-********") : "none"}
            </span>
          </td>
          <td>
            <b>${escapeHtml(profile.model)}</b>
            <span>${escapeHtml(profile.base_url)}</span>
          </td>
          <td>
            ${
              enabled
                ? `<span class="active-chip">${t("settings.enabled")}</span>`
                : `<button class="mini-button" type="button" data-profile-activate="${escapeHtml(profile.profile_id)}">${t("settings.enable")}</button>`
            }
          </td>
          <td>
            <div class="profile-actions">
              <button class="mini-button" type="button" data-profile-edit="${escapeHtml(profile.profile_id)}">${t("settings.edit")}</button>
              <button class="mini-button danger-button" type="button" data-profile-delete="${escapeHtml(profile.profile_id)}" ${enabled ? "disabled" : ""}>${t("settings.delete")}</button>
            </div>
          </td>
        </tr>
      `;
    })
    .join("");
}

function openProfileModal(profile = null) {
  renderProviderOptions(profile?.provider || "deepseek");
  els.profileIdInput.value = profile?.profile_id || "";
  els.profileNameInput.value = profile?.name || "";
  els.providerInput.value = profile?.provider || "deepseek";
  renderModelOptions();
  if (profile) {
    els.baseUrlInput.value = profile.base_url || "";
    els.modelInput.value = profile.model || "";
  } else {
    applyProviderDefaults();
  }
  els.apiKeyInput.value = "";
  els.clearApiKeyInput.checked = false;
  els.activateProfileInput.checked = Boolean(profile?.enabled);
  els.profileModalTitle.textContent = t(profile ? "settings.profileEditTitle" : "settings.profileCreateTitle");
  els.profileModal.hidden = false;
  els.profileNameInput.focus();
}

function closeProfileModal() {
  els.profileModal.hidden = true;
  els.profileForm.reset();
  els.profileIdInput.value = "";
}

async function saveProfile(event) {
  event.preventDefault();
  const profileId = els.profileIdInput.value;
  const payload = {
    name: els.profileNameInput.value.trim(),
    provider: els.providerInput.value,
    base_url: els.baseUrlInput.value.trim(),
    model: els.modelInput.value.trim(),
    clear_api_key: els.clearApiKeyInput.checked,
    activate: els.activateProfileInput.checked,
  };
  const apiKey = els.apiKeyInput.value.trim();
  if (apiKey) {
    payload.api_key = apiKey;
  }

  try {
    const data = await requestJson(profileId ? `/settings/llm-profiles/${encodeURIComponent(profileId)}` : "/settings/llm-profiles", {
      method: profileId ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applySettingsData(data);
    closeProfileModal();
    showToast(t("toast.profileSaved"));
  } catch (error) {
    showToast(error.message, true);
  }
}

async function activateProfile(profileId) {
  try {
    const data = await requestJson(`/settings/llm-profiles/${encodeURIComponent(profileId)}/activate`, {
      method: "POST",
    });
    applySettingsData(data);
    showToast(t("toast.profileActivated"));
  } catch (error) {
    showToast(error.message, true);
  }
}

async function deleteProfile(profileId) {
  const profile = state.llmProfiles.find((item) => item.profile_id === profileId);
  if (profile?.enabled) {
    showToast(t("toast.cannotDeleteActive"), true);
    return;
  }
  if (!window.confirm(t("library.confirmDelete"))) {
    return;
  }
  try {
    const data = await requestJson(`/settings/llm-profiles/${encodeURIComponent(profileId)}`, {
      method: "DELETE",
    });
    applySettingsData(data);
    showToast(t("toast.profileDeleted"));
  } catch (error) {
    showToast(error.message, true);
  }
}

function handleProfileTableClick(event) {
  const editButton = event.target.closest("[data-profile-edit]");
  if (editButton) {
    const profile = state.llmProfiles.find((item) => item.profile_id === editButton.dataset.profileEdit);
    if (profile) {
      openProfileModal(profile);
    }
    return;
  }

  const activateButton = event.target.closest("[data-profile-activate]");
  if (activateButton) {
    activateProfile(activateButton.dataset.profileActivate);
    return;
  }

  const deleteButton = event.target.closest("[data-profile-delete]");
  if (deleteButton) {
    deleteProfile(deleteButton.dataset.profileDelete);
  }
}

function renderDocuments() {
  const documents = getFilteredDocuments();
  if (!state.documents.length) {
    els.documentList.innerHTML = `<p class="empty-state">${t("documents.empty")}</p>`;
    renderDocumentDetail();
    return;
  }

  if (!documents.length) {
    els.documentList.innerHTML = `<p class="empty-state">${t("library.noMatch")}</p>`;
    renderDocumentDetail();
    return;
  }

  els.documentList.innerHTML = documents
    .map(
      (doc) => `
        <article class="doc-item">
          <div class="doc-title">
            <label class="doc-select">
              <input type="checkbox" data-select-doc="${escapeHtml(doc.document_id)}" ${state.selectedDocumentIds.has(doc.document_id) ? "checked" : ""} />
              <span>${escapeHtml(doc.filename)}</span>
            </label>
            <span class="type-pill">${escapeHtml(doc.file_type)}</span>
          </div>
          <div class="meta">
            ${t("documents.chunks")} ${doc.chunk_count} · ${doc.content_hash_prefix || t("documents.noHash")} · ${escapeHtml(doc.indexed_at || doc.created_at)}<br />
            ${escapeHtml(doc.document_id)} · ${escapeHtml(doc.embedding_model)}
          </div>
          <div class="doc-actions">
            <button class="mini-button" type="button" data-doc-detail="${escapeHtml(doc.document_id)}">${t("library.detail")}</button>
            <button class="mini-button" type="button" data-doc-reindex="${escapeHtml(doc.document_id)}">${t("library.reindex")}</button>
            <input class="reindex-file" type="file" accept=".pdf,.md,.markdown,.txt,.docx,.csv,.xlsx" data-reindex-file="${escapeHtml(doc.document_id)}" hidden />
          </div>
        </article>
      `,
    )
    .join("");
  renderDocumentDetail();
  updateDocumentSelectionState();
}

function getFilteredDocuments() {
  const nameFilter = (els.documentNameFilter?.value || "").trim().toLowerCase();
  const typeFilter = els.documentTypeFilter?.value || "";
  return state.documents.filter((doc) => {
    const matchesName = !nameFilter || doc.filename.toLowerCase().includes(nameFilter);
    const matchesType = !typeFilter || doc.file_type === typeFilter;
    return matchesName && matchesType;
  });
}

function renderDocumentControls() {
  const fileTypes = [...new Set(state.documents.map((doc) => doc.file_type).filter(Boolean))].sort();
  const currentType = els.documentTypeFilter?.value || "";
  if (els.documentTypeFilter) {
    els.documentTypeFilter.innerHTML = [
      `<option value="">${t("library.allTypes")}</option>`,
      ...fileTypes.map((fileType) => `<option value="${escapeHtml(fileType)}">${escapeHtml(fileType)}</option>`),
    ].join("");
    els.documentTypeFilter.value = fileTypes.includes(currentType) ? currentType : "";
  }
  if (els.askDocumentFilter) {
    const currentDocumentId = els.askDocumentFilter.value || "";
    els.askDocumentFilter.innerHTML = [
      `<option value="">${t("ask.allDocuments")}</option>`,
      ...state.documents.map((doc) => `<option value="${escapeHtml(doc.document_id)}">${escapeHtml(doc.filename)}</option>`),
    ].join("");
    els.askDocumentFilter.value = state.documents.some((doc) => doc.document_id === currentDocumentId) ? currentDocumentId : "";
  }
  updateDocumentSelectionState();
}

function updateDocumentSelectionState() {
  if (els.selectedDocumentCount) {
    els.selectedDocumentCount.textContent = `${state.selectedDocumentIds.size} ${t("library.selected")}`;
  }
  if (els.batchDeleteDocuments) {
    els.batchDeleteDocuments.classList.toggle("is-idle", state.selectedDocumentIds.size === 0);
  }
}

function renderDocumentDetail() {
  if (!els.documentDetail) {
    return;
  }
  const doc = state.documents.find((item) => item.document_id === state.activeDocumentId);
  if (!doc) {
    els.documentDetail.classList.remove("active");
    els.documentDetail.innerHTML = "";
    return;
  }
  els.documentDetail.classList.add("active");
  els.documentDetail.innerHTML = `
    <b>${escapeHtml(doc.filename)}</b><br />
    document_id ${escapeHtml(doc.document_id)}<br />
    knowledge_base_id ${escapeHtml(doc.knowledge_base_id || "-")}<br />
    type ${escapeHtml(doc.file_type)} · chunks ${doc.chunk_count} · pages ${doc.page_count}<br />
    hash ${escapeHtml(doc.content_hash)}<br />
    created ${escapeHtml(doc.created_at)} · indexed ${escapeHtml(doc.indexed_at)}
  `;
}

async function uploadDocument(event) {
  event.preventDefault();
  const file = els.fileInput.files[0];
  if (!file) {
    showToast(t("toast.chooseFile"), true);
    return;
  }

  const form = new FormData();
  form.append("file", file);
  form.append("chunk_size", els.chunkSize.value || "800");
  form.append("overlap", els.overlap.value || "100");
  form.append("reindex", els.reindex.checked ? "true" : "false");

  setStatus("indexing");
  try {
    const data = await requestJson(knowledgeBasePath("/documents/index-jobs"), {
      method: "POST",
      body: form,
    });
<<<<<<< HEAD
    showToast(data.message || t("toast.indexDone"));
    els.fileInput.value = "";
    updateSelectedFileName();
    await loadDocuments();
=======
    showToast(t("jobs.created"));
    state.indexJobs = [data, ...state.indexJobs.filter((job) => job.job_id !== data.job_id)];
    state.hadActiveIndexJobs = true;
    renderIndexJobs();
    startIndexJobPolling();
    await loadIndexJobs();
>>>>>>> e0d56302c3febb53fc08d3d5219d1bc8e7a1149f
  } catch (error) {
    showToast(error.message, true);
    setStatus("error");
  }
}

function updateSelectedFileName() {
  if (!els.fileNameDisplay || !els.fileInput) {
    return;
  }
  const file = els.fileInput.files?.[0] || null;
  els.fileNameDisplay.textContent = file ? file.name : t("import.noFile");
  els.fileNameDisplay.classList.toggle("has-file", Boolean(file));
}

async function batchDeleteDocuments() {
  const documentIds = [...state.selectedDocumentIds];
  if (!documentIds.length) {
    showToast(t("library.selectFirst"), true);
    return;
  }
  if (!window.confirm(t("library.confirmDelete"))) {
    return;
  }

  setStatus("loading");
  try {
    await requestJson(knowledgeBasePath("/documents/batch"), {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: documentIds }),
    });
    state.selectedDocumentIds.clear();
    state.activeDocumentId = null;
    showToast(t("library.deleted"));
    await loadDocuments();
  } catch (error) {
    showToast(error.message, true);
    setStatus("error");
  }
}

async function reindexDocument(documentId, file) {
  const form = new FormData();
  form.append("file", file);
  form.append("chunk_size", els.chunkSize.value || "800");
  form.append("overlap", els.overlap.value || "100");

  setStatus("indexing");
  try {
    await requestJson(knowledgeBasePath(`/documents/${encodeURIComponent(documentId)}/reindex`), {
      method: "POST",
      body: form,
    });
    showToast(t("library.reindexed"));
    await loadDocuments();
  } catch (error) {
    showToast(error.message, true);
    setStatus("error");
  }
}

function handleDocumentListClick(event) {
  const detailButton = event.target.closest("[data-doc-detail]");
  if (detailButton) {
    state.activeDocumentId = detailButton.dataset.docDetail;
    renderDocumentDetail();
    return;
  }

  const reindexButton = event.target.closest("[data-doc-reindex]");
  if (reindexButton) {
    const input = els.documentList.querySelector(`[data-reindex-file="${CSS.escape(reindexButton.dataset.docReindex)}"]`);
    input?.click();
  }
}

function handleDocumentListChange(event) {
  const selectInput = event.target.closest("[data-select-doc]");
  if (selectInput) {
    if (selectInput.checked) {
      state.selectedDocumentIds.add(selectInput.dataset.selectDoc);
    } else {
      state.selectedDocumentIds.delete(selectInput.dataset.selectDoc);
    }
    updateDocumentSelectionState();
    return;
  }

  const reindexInput = event.target.closest("[data-reindex-file]");
  if (reindexInput?.files?.[0]) {
    reindexDocument(reindexInput.dataset.reindexFile, reindexInput.files[0]);
    reindexInput.value = "";
  }
}

async function retryIndexJob(jobId) {
  try {
    const job = await requestJson(knowledgeBasePath(`/documents/index-jobs/${encodeURIComponent(jobId)}/retry`), {
      method: "POST",
    });
    state.indexJobs = state.indexJobs.map((item) => (item.job_id === job.job_id ? job : item));
    state.hadActiveIndexJobs = true;
    renderIndexJobs();
    startIndexJobPolling();
    showToast(t("jobs.created"));
  } catch (error) {
    showToast(error.message, true);
  }
}

function handleIndexJobListClick(event) {
  const retryButton = event.target.closest("[data-retry-job]");
  if (retryButton) {
    retryIndexJob(retryButton.dataset.retryJob);
  }
}

async function saveSettings(event) {
  event.preventDefault();
  const payload = {
    request_timeout_seconds: Number(els.timeoutInput.value || 30),
    rag_system_prompt: els.systemPromptInput.value,
    rag_answer_instructions: els.answerPromptInput.value,
  };

  setSettingsStatus("saving");
  try {
    const data = await requestJson("/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    applySettingsData(data);
    showToast(t("toast.settingsSaved"));
  } catch (error) {
    setSettingsStatus("error");
    showToast(error.message, true);
  }
}

async function askQuestion(event) {
  event.preventDefault();
  const question = els.questionInput.value.trim();
  if (!question) {
    showToast(t("toast.enterQuestion"), true);
    return;
  }

  const payload = {
    question,
    limit: Number(els.topK.value || 5),
  };
  if (els.scoreThreshold.value !== "") {
    payload.score_threshold = Number(els.scoreThreshold.value);
  }
  if (els.askDocumentFilter.value) {
    payload.document_id = els.askDocumentFilter.value;
  }
  if (state.activeKnowledgeBaseId) {
    payload.knowledge_base_id = state.activeKnowledgeBaseId;
  }

  setStatus("asking");
  const pendingId = `pending-${Date.now()}`;
  state.messages.push({ role: "user", content: question });
  state.messages.push({ id: pendingId, role: "assistant", pending: true });
  renderMessages({ scroll: "bottom" });
  els.questionInput.value = "";
  els.sourceList.innerHTML = "";
  try {
    const endpoint = knowledgeBasePath(state.askMode === "agent" ? "/agent/ask" : "/rag/ask");
    const data = await requestJson(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.lastAnswer = data;
    const routeMeta = data.route ? `${t("debug.route")} ${data.route} · ` : "";
    replacePendingMessage(pendingId, {
      role: "assistant",
      content: data.reply || "",
      meta: `${routeMeta}${data.model || t("debug.model")} · ${t("debug.sources")} ${data.source_count}`,
<<<<<<< HEAD
      feedback: {
        question,
        answer: data.reply || "",
        rating: "",
        route: data.route || state.askMode,
        knowledge_base_id: data.knowledge_base_id || state.activeKnowledgeBaseId || "",
        source_count: data.source_count || 0,
      },
    });
=======
    }, { scroll: "latestAssistantTop" });
>>>>>>> 54150954f5ddeeac4a794980a0eaf0e85bed9248
    renderSources(data.sources || []);
    renderDebug(data);
    setStatus("done");
  } catch (error) {
    replacePendingMessage(pendingId, {
      role: "assistant",
      content: `${t("message.requestFailed")}：${error.message}`,
      error: true,
    }, { scroll: "latestAssistantTop" });
    els.debugGrid.innerHTML = "";
    setStatus("error");
  }
}

function renderMessages(options = {}) {
  if (!state.messages.length) {
    els.answerOutput.innerHTML = `<p class="empty-state">${t("ask.empty")}</p>`;
    return;
  }

<<<<<<< HEAD
  els.answerOutput.innerHTML = state.messages.map((message, index) => renderMessage(message, index)).join("");
  els.answerOutput.scrollTop = els.answerOutput.scrollHeight;
=======
  els.answerOutput.innerHTML = state.messages.map(renderMessage).join("");
  scrollAnswerOutput(options.scroll || "none");
>>>>>>> 54150954f5ddeeac4a794980a0eaf0e85bed9248
}

function renderMessage(message, index = 0) {
  const classes = ["chat-message", message.role];
  if (message.error) {
    classes.push("error");
  }

  if (message.pending) {
    return `
      <article class="${classes.join(" ")}">
        <div class="bubble">
          <div class="bubble-meta">${t("message.pendingMeta")}</div>
          <span class="thinking">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            ${t("message.pendingText")}
          </span>
        </div>
      </article>
    `;
  }

  const content = message.role === "assistant"
    ? markdownLite(message.content || "")
    : escapeHtml(message.content || "").replace(/\n/g, "<br />");
  const meta = message.meta ? `<div class="bubble-meta">${escapeHtml(message.meta)}</div>` : "";
  const feedbackActions = message.feedback
    ? `
      <div class="feedback-actions">
        <button class="icon-button" type="button" title="thumbs up" data-feedback-rating="up" data-message-index="${index}">${message.feedback.rating === "up" ? "ok" : "+"}</button>
        <button class="icon-button" type="button" title="thumbs down" data-feedback-rating="down" data-message-index="${index}">${message.feedback.rating === "down" ? "ok" : "-"}</button>
      </div>
    `
    : "";

  return `
    <article class="${classes.join(" ")}">
      <div class="bubble">
        ${meta}
        ${content}
        ${feedbackActions}
      </div>
    </article>
  `;
}

function replacePendingMessage(id, nextMessage, options = {}) {
  const index = state.messages.findIndex((message) => message.id === id);
  if (index >= 0) {
    state.messages[index] = nextMessage;
  } else {
    state.messages.push(nextMessage);
  }
  renderMessages(options);
}

function scrollAnswerOutput(mode) {
  if (mode === "bottom") {
    els.answerOutput.scrollTop = els.answerOutput.scrollHeight;
    return;
  }
  if (mode === "latestAssistantTop") {
    const latestAssistant = [...els.answerOutput.querySelectorAll(".chat-message.assistant")].at(-1);
    if (latestAssistant) {
      els.answerOutput.scrollTop = Math.max(0, latestAssistant.offsetTop - els.answerOutput.offsetTop);
    }
  }
}

async function handleAnswerFeedbackClick(event) {
  const button = event.target.closest("[data-feedback-rating]");
  if (!button) {
    return;
  }
  const message = state.messages[Number(button.dataset.messageIndex)];
  if (!message?.feedback) {
    return;
  }
  const feedback = message.feedback;
  const payload = {
    question: feedback.question,
    answer: feedback.answer,
    rating: button.dataset.feedbackRating,
    route: feedback.route,
    details: {
      source_count: feedback.source_count,
    },
  };
  if (feedback.knowledge_base_id) {
    payload.knowledge_base_id = feedback.knowledge_base_id;
  }
  try {
    await requestJson("/feedback/answers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    feedback.rating = payload.rating;
    renderMessages();
    showToast(t("toast.feedbackSaved"));
  } catch (error) {
    showToast(error.message, true);
  }
}

function switchTab(tabName) {
  els.tabButtons.forEach((button) => {
    const isActive = button.dataset.tab === tabName;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
  els.tabPages.forEach((page) => {
    const isActive = page.id === `tab-${tabName}`;
    page.classList.toggle("active", isActive);
    page.hidden = !isActive;
  });

  if (tabName === "evaluation" && !state.evaluation) {
    loadLatestEvaluation();
  }
  if (tabName === "evaluation" && !state.evaluationRuns.length) {
    loadEvaluationRuns();
  }
}

function renderSources(sources) {
  if (!sources.length) {
    els.sourceList.innerHTML = `<p class="empty-state">${t("sources.empty")}</p>`;
    return;
  }
  els.sourceList.innerHTML = sources
    .map(
      (source) => `
        <article class="source-item">
          <div class="source-title">
            <span>[Source ${source.source_id}] ${escapeHtml(source.filename)}</span>
            <span class="type-pill">${escapeHtml(source.file_type || "file")}</span>
          </div>
          <div class="meta">
            score ${Number(source.score).toFixed(4)} · page ${source.page_number} · chunk ${source.chunk_id}
          </div>
          <p class="preview">${escapeHtml(source.preview || "")}</p>
        </article>
      `,
    )
    .join("");
}

function renderDebug(data) {
  const usage = data.usage || {};
  const debugItems = [
    `<div class="debug-item"><span>${t("debug.retrieved")}</span><b>${data.retrieved_count}</b></div>`,
    `<div class="debug-item"><span>${t("debug.sources")}</span><b>${data.source_count}</b></div>`,
    `<div class="debug-item"><span>${t("debug.model")}</span><b>${escapeHtml(data.model || "-")}</b></div>`,
    `<div class="debug-item"><span>${t("debug.tokens")}</span><b>${usage.total_tokens ?? "-"}</b></div>`,
  ];

  if (data.route) {
    debugItems.push(`<div class="debug-item"><span>${t("debug.route")}</span><b>${escapeHtml(data.route)}</b></div>`);
  }
  if (data.tools_used?.length) {
    debugItems.push(`<div class="debug-item wide"><span>${t("debug.tools")}</span><b>${escapeHtml(data.tools_used.join(" · "))}</b></div>`);
  }
  if (data.route_reason) {
    debugItems.push(`<div class="debug-item wide"><span>${t("debug.reason")}</span><b>${escapeHtml(data.route_reason)}</b></div>`);
  }
  if (data.routing_debug?.fallback) {
    debugItems.push(`<div class="debug-item wide"><span>${t("debug.fallback")}</span><b>${escapeHtml(data.routing_debug.fallback)}</b></div>`);
  }

  els.debugGrid.innerHTML = debugItems.join("");
}

async function loadLatestEvaluation() {
  if (!els.evaluationSummary) {
    return;
  }
  setEvaluationStatus("loading");
  try {
    const data = await requestJson("/evaluation/latest");
    state.evaluation = data;
    renderEvaluation(data);
    setEvaluationStatus("done");
  } catch (error) {
    state.evaluation = null;
    renderEvaluation(null);
    setEvaluationStatus("idle");
  }
}

async function loadEvaluationRuns() {
  if (!els.evaluationHistory) {
    return;
  }
  const params = new URLSearchParams({ limit: "8" });
  if (state.activeKnowledgeBaseId) {
    params.set("knowledge_base_id", state.activeKnowledgeBaseId);
  }
  try {
    const data = await requestJson(`/evaluation/runs?${params.toString()}`);
    state.evaluationRuns = data.runs || [];
    renderEvaluationHistory();
  } catch (error) {
    state.evaluationRuns = [];
    renderEvaluationHistory();
  }
}

async function runEvaluation(event) {
  event.preventDefault();
  const payload = {
    limit: Number(els.evaluationTopK.value || 5),
  };
  if (els.evaluationThreshold.value !== "") {
    payload.score_threshold = Number(els.evaluationThreshold.value);
  }
  if (state.activeKnowledgeBaseId) {
    payload.knowledge_base_id = state.activeKnowledgeBaseId;
  }

  setEvaluationStatus("evaluating");
  try {
    const data = await requestJson("/evaluation/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.evaluation = data;
    renderEvaluation(data);
    loadEvaluationRuns();
    setEvaluationStatus("done");
  } catch (error) {
    setEvaluationStatus("error");
    showToast(error.message, true);
  }
}

function renderEvaluationHistory() {
  if (!els.evaluationHistory) {
    return;
  }
  const runs = state.evaluationRuns || [];
  if (!runs.length) {
    els.evaluationHistory.innerHTML = "";
    return;
  }
  els.evaluationHistory.innerHTML = `
    <div class="evaluation-history-head">
      <b>${t("evaluation.history")}</b>
    </div>
    <div class="evaluation-run-list">
      ${runs.map(renderEvaluationRun).join("")}
    </div>
  `;
}

function renderEvaluationRun(run) {
  return `
    <button class="evaluation-run" type="button" data-evaluation-run-id="${escapeHtml(run.run_id)}">
      <span>${formatDateTime(run.generated_at)}</span>
      <b>${formatRate(run.hit_rate)}</b>
      <small>top_k ${run.limit} · ${t("evaluation.quality")} ${escapeHtml(run.quality_status || "-")}</small>
    </button>
  `;
}

async function handleEvaluationHistoryClick(event) {
  const button = event.target.closest("[data-evaluation-run-id]");
  if (!button) {
    return;
  }
  setEvaluationStatus("loading");
  try {
    const data = await requestJson(`/evaluation/runs/${encodeURIComponent(button.dataset.evaluationRunId)}`);
    state.evaluation = data;
    renderEvaluation(data);
    setEvaluationStatus("done");
  } catch (error) {
    setEvaluationStatus("error");
    showToast(error.message, true);
  }
}

function renderEvaluation(data) {
  if (!data) {
    els.evaluationSummary.innerHTML = `<p class="empty-state">${t("evaluation.empty")}</p>`;
    els.evaluationCases.innerHTML = "";
    return;
  }

  els.evaluationSummary.innerHTML = `
    <div class="debug-grid evaluation-metrics">
      <div class="debug-item"><span>${t("evaluation.hitRate")}</span><b>${formatRate(data.hit_rate)}</b></div>
      <div class="debug-item"><span>${t("evaluation.pageHitRate")}</span><b>${formatRate(data.page_hit_rate)}</b></div>
      <div class="debug-item"><span>${t("evaluation.keywordHitRate")}</span><b>${formatRate(data.keyword_hit_rate)}</b></div>
      <div class="debug-item"><span>${t("evaluation.lowScore")}</span><b>${data.low_score_result_count}</b></div>
    </div>
    <div class="evaluation-meta">
      ${t("evaluation.dataset")} ${escapeHtml(data.dataset_name)} ·
      ${t("evaluation.cases")} ${data.scored_case_count}/${data.case_count} ·
      top_k ${data.limit} ·
      ${t("evaluation.quality")} ${escapeHtml(data.quality_gate?.status || "-")} ·
      ${t("evaluation.generatedAt")} ${formatDateTime(data.generated_at)}
    </div>
  `;

  els.evaluationCases.innerHTML = (data.cases || [])
    .map(renderEvaluationCase)
    .join("");
}

function renderEvaluationCase(item) {
  const statusText = item.hit ? t("evaluation.caseHit") : t("evaluation.caseMiss");
  const scores = (item.top_scores || []).map((score) => Number(score).toFixed(4)).join(", ");
  const sources = (item.top_sources || [])
    .slice(0, 3)
    .map((source) => `${escapeHtml(source.filename)} p${source.page_number} c${source.chunk_id} ${escapeHtml(source.extraction_method || "text")}`)
    .join("<br />");
  return `
    <article class="evaluation-case ${item.hit ? "hit" : "miss"}">
      <div class="evaluation-case-head">
        <span class="evaluation-question">${escapeHtml(item.case_id)} · ${escapeHtml(item.question)}</span>
        <span class="type-pill evaluation-result-pill">${statusText}</span>
      </div>
      <div class="meta evaluation-case-meta">
        pages ${escapeHtml((item.top_pages || []).join(", ") || "-")} · scores ${escapeHtml(scores || "-")}<br />
        keywords ${escapeHtml((item.matched_keywords || []).join(", ") || "-")}
      </div>
      ${sources ? `<p class="preview">${sources}</p>` : ""}
    </article>
  `;
}

function formatRate(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function loadPreferences() {
  try {
    return {
      language: "zh",
      themeColor: "teal",
      customColor: "#37d0b2",
      backgroundColor: DEFAULT_BACKGROUND_COLOR,
      ...JSON.parse(localStorage.getItem(PREFERENCES_KEY) || "{}"),
    };
  } catch {
    return {
      language: "zh",
      themeColor: "teal",
      customColor: "#37d0b2",
      backgroundColor: DEFAULT_BACKGROUND_COLOR,
    };
  }
}

function savePreferences() {
  localStorage.setItem(PREFERENCES_KEY, JSON.stringify(state.preferences));
}

function t(key, fallback = "") {
  return translations[state.preferences.language]?.[key] || translations.zh[key] || fallback || key;
}

function applyPreferences() {
  applyLanguage();
  applyTheme();
}

function applyLanguage() {
  document.documentElement.lang = state.preferences.language === "en" ? "en" : "zh-CN";
  document.title = t("app.documentTitle");
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n, element.textContent);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder, element.getAttribute("placeholder") || ""));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.setAttribute("title", t(element.dataset.i18nTitle, element.getAttribute("title") || ""));
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel, element.getAttribute("aria-label") || ""));
  });
  els.languageButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.language === state.preferences.language);
  });
  els.askModeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.askMode === state.askMode);
  });
  setStatus(els.statusPill.dataset.status || "idle");
  setSettingsStatus(els.settingsStatus.dataset.status || "noKey", els.settingsStatus.dataset.source || "");
  renderDocumentControls();
  renderDocuments();
  renderProfileTable();
  renderAdminUsers();
  renderKnowledgeBaseMembers();
  renderMessages();
  if (state.lastAnswer) {
    renderSources(state.lastAnswer.sources || []);
    renderDebug(state.lastAnswer);
  }
  if (state.evaluation) {
    renderEvaluation(state.evaluation);
  } else if (els.evaluationSummary) {
    renderEvaluation(null);
  }
<<<<<<< HEAD
  renderEvaluationHistory();
=======
  updateSelectedFileName();
>>>>>>> 54150954f5ddeeac4a794980a0eaf0e85bed9248
}

function applyTheme() {
  const selected = state.preferences.themeColor;
  const palette = selected === "custom"
    ? {
        accent: state.preferences.customColor || "#37d0b2",
        accent2: "#ffb86b",
      }
    : THEME_COLORS[selected] || THEME_COLORS.teal;
  const root = document.documentElement;
  const backgroundColor = state.preferences.backgroundColor || DEFAULT_BACKGROUND_COLOR;
  const backgroundRgb = hexToRgbList(backgroundColor);
  root.style.setProperty("--bg", backgroundColor);
  root.style.setProperty("--panel", `rgba(${backgroundRgb}, 0.78)`);
  root.style.setProperty("--panel-strong", `rgba(${backgroundRgb}, 0.9)`);
  root.style.setProperty("--surface", `rgba(${backgroundRgb}, 0.42)`);
  root.style.setProperty("--surface-strong", `rgba(${backgroundRgb}, 0.58)`);
  root.style.setProperty("--field", `rgba(${backgroundRgb}, 0.62)`);
  root.style.setProperty("--field-strong", `rgba(${backgroundRgb}, 0.78)`);
  root.style.setProperty("--accent", palette.accent);
  root.style.setProperty("--accent-2", palette.accent2);
  root.style.setProperty("--accent-rgb", hexToRgbList(palette.accent));
  root.style.setProperty("--accent-2-rgb", hexToRgbList(palette.accent2));
  els.colorButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.themeColor === selected);
  });
  if (els.customColorInput) {
    els.customColorInput.value = state.preferences.customColor || "#37d0b2";
  }
  if (els.backgroundColorInput) {
    els.backgroundColorInput.value = state.preferences.backgroundColor || DEFAULT_BACKGROUND_COLOR;
  }
}

function setLanguage(language) {
  state.preferences.language = language;
  savePreferences();
  applyLanguage();
  showToast(t("toast.languageChanged"));
}

function setAskMode(mode) {
  state.askMode = mode === "agent" ? "agent" : "rag";
  els.askModeButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.askMode === state.askMode);
  });
}

function setThemeColor(themeColor, customColor = null) {
  state.preferences.themeColor = themeColor;
  if (customColor) {
    state.preferences.customColor = customColor;
  }
  savePreferences();
  applyTheme();
  showToast(t("toast.colorChanged"));
}

function setBackgroundColor(backgroundColor) {
  state.preferences.backgroundColor = backgroundColor || DEFAULT_BACKGROUND_COLOR;
  savePreferences();
  applyTheme();
  showToast(t("toast.backgroundChanged"));
}

function resetBackgroundColor() {
  setBackgroundColor(DEFAULT_BACKGROUND_COLOR);
}

function hexToRgbList(hex) {
  const normalized = hex.replace("#", "");
  const full = normalized.length === 3
    ? normalized.split("").map((char) => `${char}${char}`).join("")
    : normalized;
  const value = Number.parseInt(full, 16);
  const red = (value >> 16) & 255;
  const green = (value >> 8) & 255;
  const blue = value & 255;
  return `${red}, ${green}, ${blue}`;
}

function markdownLite(text) {
  const lines = String(text || "").replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let codeLines = [];
  let inCodeBlock = false;

  lines.forEach((line) => {
    const fence = line.trim().match(/^```[A-Za-z0-9_-]*\s*$/);
    if (fence) {
      if (inCodeBlock) {
        html.push(renderCodeBlock(codeLines.join("\n")));
        codeLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
        codeLines = [];
      }
      return;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      return;
    }

    html.push(renderMarkdownLine(line));
  });

  if (inCodeBlock) {
    html.push(renderCodeBlock(codeLines.join("\n")));
  }

  return `<div class="md-answer">${html.join("")}</div>`;
}

function renderMarkdownLine(line) {
  const trimmed = line.trim();
  if (!trimmed) {
    return `<div class="md-spacer"></div>`;
  }

  const ordered = trimmed.match(/^(\d+)\.\s+(.+)$/);
  if (ordered) {
    return `
      <div class="md-line md-list-line">
        <span class="md-marker">${ordered[1]}.</span>
        <span>${renderInlineMarkdown(ordered[2])}</span>
      </div>
    `;
  }

  const unordered = trimmed.match(/^[-*]\s+(.+)$/);
  if (unordered) {
    return `
      <div class="md-line md-list-line">
        <span class="md-marker">-</span>
        <span>${renderInlineMarkdown(unordered[1])}</span>
      </div>
    `;
  }

  if (/^(答案|依据|资料不足之处)[:：]/.test(trimmed)) {
    const [title, ...rest] = trimmed.split(/[:：]/);
    const suffix = rest.join("：").trim();
    return `
      <div class="md-section-title">${escapeHtml(title)}：</div>
      ${suffix ? `<p class="md-paragraph">${renderInlineMarkdown(suffix)}</p>` : ""}
    `;
  }

  const heading = trimmed.match(/^#{1,6}\s+(.+)$/);
  if (heading) {
    return `<div class="md-section-title">${renderInlineMarkdown(heading[1])}</div>`;
  }

  return `<p class="md-paragraph">${renderInlineMarkdown(trimmed)}</p>`;
}

function renderInlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
}

function renderCodeBlock(code) {
  const content = code.trimEnd();
  if (!content) {
    return "";
  }
  return `<pre class="md-code"><code>${escapeHtml(content)}</code></pre>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

els.uploadForm.addEventListener("submit", uploadDocument);
els.chooseFileButton.addEventListener("click", () => els.fileInput.click());
els.fileNameDisplay.addEventListener("click", () => els.fileInput.click());
els.fileInput.addEventListener("change", updateSelectedFileName);
els.documentNameFilter.addEventListener("input", renderDocuments);
els.documentTypeFilter.addEventListener("change", renderDocuments);
els.clearDocumentFilters.addEventListener("click", () => {
  els.documentNameFilter.value = "";
  els.documentTypeFilter.value = "";
  renderDocuments();
});
els.batchDeleteDocuments.addEventListener("click", batchDeleteDocuments);
els.knowledgeBaseSelect.addEventListener("change", () => {
  changeKnowledgeBase().catch((error) => showToast(error.message, true));
});
els.knowledgeBaseForm.addEventListener("submit", createKnowledgeBase);
els.refreshIndexJobs.addEventListener("click", () => {
  loadIndexJobs().catch((error) => showToast(error.message, true));
});
els.indexJobList.addEventListener("click", handleIndexJobListClick);
els.documentList.addEventListener("click", handleDocumentListClick);
els.documentList.addEventListener("change", handleDocumentListChange);
els.askForm.addEventListener("submit", askQuestion);
els.answerOutput.addEventListener("click", handleAnswerFeedbackClick);
els.settingsForm.addEventListener("submit", saveSettings);
els.profileForm.addEventListener("submit", saveProfile);
els.profileTableBody.addEventListener("click", handleProfileTableClick);
els.addProfileButton.addEventListener("click", () => openProfileModal());
els.closeProfileModal.addEventListener("click", closeProfileModal);
els.cancelProfileModal.addEventListener("click", closeProfileModal);
els.profileModal.addEventListener("click", (event) => {
  if (event.target === els.profileModal) {
    closeProfileModal();
  }
});
els.providerInput.addEventListener("change", applyProviderDefaults);
els.evaluationForm.addEventListener("submit", runEvaluation);
els.reloadEvaluation.addEventListener("click", () => {
  loadLatestEvaluation().catch((error) => showToast(error.message, true));
});
els.reloadEvaluationRuns.addEventListener("click", () => {
  loadEvaluationRuns().catch((error) => showToast(error.message, true));
});
els.evaluationHistory.addEventListener("click", handleEvaluationHistoryClick);
els.reloadSettings.addEventListener("click", () => {
  loadSettings().catch((error) => showToast(error.message, true));
});
els.reloadTeamAccess.addEventListener("click", () => {
  loadTeamAccess().catch((error) => showToast(error.message, true));
});
els.adminUserForm.addEventListener("submit", createAdminUser);
els.memberForm.addEventListener("submit", addKnowledgeBaseMember);
els.memberList.addEventListener("click", handleMemberListClick);
els.languageButtons.forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.language));
});
els.askModeButtons.forEach((button) => {
  button.addEventListener("click", () => setAskMode(button.dataset.askMode));
});
els.colorButtons.forEach((button) => {
  button.addEventListener("click", () => setThemeColor(button.dataset.themeColor));
});
els.customColorInput.addEventListener("input", (event) => {
  setThemeColor("custom", event.target.value);
});
els.backgroundColorInput.addEventListener("input", (event) => {
  setBackgroundColor(event.target.value);
});
els.resetBackgroundColor.addEventListener("click", resetBackgroundColor);
els.tabButtons.forEach((button) => {
  button.addEventListener("click", () => switchTab(button.dataset.tab));
});
els.questionInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") {
    return;
  }

  if (event.ctrlKey) {
    event.preventDefault();
    insertTextareaNewline(els.questionInput);
    return;
  }

  event.preventDefault();
  els.askForm.requestSubmit();
});
els.refreshDocuments.addEventListener("click", () => {
  loadDocuments().catch((error) => showToast(error.message, true));
});
els.authForm.addEventListener("submit", submitAuth);
els.registerUser.addEventListener("click", () => {
  registerUser().catch((error) => showToast(error.message, true));
});
els.bootstrapAdmin.addEventListener("click", () => {
  bootstrapAdmin().catch((error) => showToast(error.message, true));
});
els.logoutButton.addEventListener("click", () => {
  logout().catch((error) => showToast(error.message, true));
});

initializeAuthenticatedApp();

function insertTextareaNewline(textarea) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = textarea.value;
  textarea.value = `${value.slice(0, start)}\n${value.slice(end)}`;
  textarea.selectionStart = start + 1;
  textarea.selectionEnd = start + 1;
}
