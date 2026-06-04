const PREFERENCES_KEY = "ragPdfQaUiPreferences";
const DEFAULT_BACKGROUND_COLOR = "#0f1213";

const state = {
  documents: [],
  lastAnswer: null,
  messages: [],
  preferences: loadPreferences(),
};

const els = {
  uploadForm: document.querySelector("#uploadForm"),
  fileInput: document.querySelector("#fileInput"),
  chunkSize: document.querySelector("#chunkSize"),
  overlap: document.querySelector("#overlap"),
  reindex: document.querySelector("#reindex"),
  documentList: document.querySelector("#documentList"),
  refreshDocuments: document.querySelector("#refreshDocuments"),
  askForm: document.querySelector("#askForm"),
  questionInput: document.querySelector("#questionInput"),
  topK: document.querySelector("#topK"),
  scoreThreshold: document.querySelector("#scoreThreshold"),
  answerOutput: document.querySelector("#answerOutput"),
  sourceList: document.querySelector("#sourceList"),
  debugGrid: document.querySelector("#debugGrid"),
  statusPill: document.querySelector("#statusPill"),
  toast: document.querySelector("#toast"),
  tabButtons: Array.from(document.querySelectorAll(".tab-button")),
  tabPages: Array.from(document.querySelectorAll(".tab-page")),
  settingsForm: document.querySelector("#settingsForm"),
  baseUrlInput: document.querySelector("#baseUrlInput"),
  modelInput: document.querySelector("#modelInput"),
  apiKeyInput: document.querySelector("#apiKeyInput"),
  timeoutInput: document.querySelector("#timeoutInput"),
  clearApiKeyInput: document.querySelector("#clearApiKeyInput"),
  systemPromptInput: document.querySelector("#systemPromptInput"),
  answerPromptInput: document.querySelector("#answerPromptInput"),
  settingsStatus: document.querySelector("#settingsStatus"),
  reloadSettings: document.querySelector("#reloadSettings"),
  languageButtons: Array.from(document.querySelectorAll("[data-language]")),
  colorButtons: Array.from(document.querySelectorAll(".color-swatch[data-theme-color]")),
  customColorInput: document.querySelector("#customColorInput"),
  backgroundColorInput: document.querySelector("#backgroundColorInput"),
  resetBackgroundColor: document.querySelector("#resetBackgroundColor"),
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
    "nav.settings": "设置",
    "nav.settingsSub": "Settings",
    "nav.docs": "Swagger Docs",
    "import.eyebrow": "Import",
    "import.title": "文件导入",
    "import.refresh": "刷新文档列表",
    "import.chunk": "chunk",
    "import.overlap": "overlap",
    "import.reindex": "reindex",
    "import.submit": "上传索引",
    "ask.eyebrow": "Retrieve",
    "ask.title": "知识问答",
    "ask.empty": "等待问题",
    "ask.placeholder": "输入问题",
    "ask.topK": "top_k",
    "ask.threshold": "threshold",
    "ask.submit": "提问",
    "sources.eyebrow": "Sources",
    "sources.title": "检索来源",
    "settings.eyebrow": "Settings",
    "settings.title": "模型与提示词",
    "preferences.title": "界面偏好",
    "preferences.language": "语言",
    "preferences.color": "系统颜色",
    "preferences.background": "背景颜色",
    "preferences.customColor": "自定义颜色",
    "preferences.resetBackground": "恢复默认",
    "settings.baseUrl": "API Base URL",
    "settings.model": "LLM Model",
    "settings.apiKey": "API Key",
    "settings.timeout": "Timeout",
    "settings.clearApiKey": "清除本地运行时 API Key",
    "settings.systemPrompt": "RAG System Prompt",
    "settings.answerPrompt": "RAG Answer Instructions",
    "settings.save": "保存设置",
    "settings.reload": "重新读取",
    "labels.chunk": "chunk",
    "labels.overlap": "overlap",
    "labels.reindex": "reindex",
    "labels.topK": "top_k",
    "labels.threshold": "threshold",
    "labels.baseUrl": "API Base URL",
    "labels.model": "LLM Model",
    "labels.apiKey": "API Key",
    "labels.timeout": "Timeout",
    "labels.systemPrompt": "RAG System Prompt",
    "labels.answerPrompt": "RAG Answer Instructions",
    "settings.apiKeyPlaceholder": "留空则不修改已配置密钥",
    "documents.empty": "暂无文档",
    "documents.chunks": "chunks",
    "documents.noHash": "no-hash",
    "sources.empty": "无 sources",
    "debug.retrieved": "retrieved",
    "debug.sources": "sources",
    "debug.model": "model",
    "debug.tokens": "tokens",
    "message.pendingMeta": "AI 正在解析检索结果",
    "message.pendingText": "整理答案中",
    "message.requestFailed": "请求失败",
    "toast.chooseFile": "请选择文件",
    "toast.indexDone": "索引完成",
    "toast.enterQuestion": "请输入问题",
    "toast.settingsSaved": "设置已保存",
    "toast.languageChanged": "语言已切换",
    "toast.colorChanged": "系统色已更新",
    "toast.backgroundChanged": "背景色已更新",
    "status.idle": "idle",
    "status.loading": "loading",
    "status.indexing": "indexing",
    "status.asking": "asking",
    "status.done": "done",
    "status.error": "error",
    "settingsStatus.loading": "loading",
    "settingsStatus.saving": "saving",
    "settingsStatus.error": "error",
    "settingsStatus.noKey": "no-key",
    "settingsStatus.key": "key",
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
    "nav.settings": "Settings",
    "nav.settingsSub": "Settings",
    "nav.docs": "Swagger Docs",
    "import.eyebrow": "Import",
    "import.title": "Import Files",
    "import.refresh": "Refresh documents",
    "import.chunk": "chunk",
    "import.overlap": "overlap",
    "import.reindex": "reindex",
    "import.submit": "Upload & Index",
    "ask.eyebrow": "Retrieve",
    "ask.title": "Knowledge Q&A",
    "ask.empty": "Waiting for a question",
    "ask.placeholder": "Ask a question",
    "ask.topK": "top_k",
    "ask.threshold": "threshold",
    "ask.submit": "Ask",
    "sources.eyebrow": "Sources",
    "sources.title": "Retrieved Sources",
    "settings.eyebrow": "Settings",
    "settings.title": "Model & Prompts",
    "preferences.title": "Interface Preferences",
    "preferences.language": "Language",
    "preferences.color": "System Color",
    "preferences.background": "Background Color",
    "preferences.customColor": "Custom color",
    "preferences.resetBackground": "Reset",
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
    "message.pendingMeta": "AI is reading retrieved sources",
    "message.pendingText": "Composing answer",
    "message.requestFailed": "Request failed",
    "toast.chooseFile": "Choose a file first",
    "toast.indexDone": "Indexing complete",
    "toast.enterQuestion": "Enter a question",
    "toast.settingsSaved": "Settings saved",
    "toast.languageChanged": "Language changed",
    "toast.colorChanged": "System color updated",
    "toast.backgroundChanged": "Background color updated",
    "status.idle": "idle",
    "status.loading": "loading",
    "status.indexing": "indexing",
    "status.asking": "asking",
    "status.done": "done",
    "status.error": "error",
    "settingsStatus.loading": "loading",
    "settingsStatus.saving": "saving",
    "settingsStatus.error": "error",
    "settingsStatus.noKey": "no-key",
    "settingsStatus.key": "key",
  },
};

function setStatus(value) {
  els.statusPill.dataset.status = value;
  els.statusPill.textContent = t(`status.${value}`, value);
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
  const response = await fetch(url, options);
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function loadDocuments() {
  setStatus("loading");
  const data = await requestJson("/documents");
  state.documents = data.documents || [];
  renderDocuments();
  setStatus("idle");
}

async function loadSettings() {
  if (!els.settingsForm) {
    return;
  }

  setSettingsStatus("loading");
  const data = await requestJson("/settings");
  els.baseUrlInput.value = data.deepseek_base_url || "";
  els.modelInput.value = data.deepseek_model || "";
  els.timeoutInput.value = data.request_timeout_seconds || 30;
  els.apiKeyInput.value = "";
  els.clearApiKeyInput.checked = false;
  els.systemPromptInput.value = data.rag_system_prompt || "";
  els.answerPromptInput.value = data.rag_answer_instructions || "";
  setSettingsStatus(data.api_key_configured ? "key" : "noKey", data.api_key_source);
}

function renderDocuments() {
  if (!state.documents.length) {
    els.documentList.innerHTML = `<p class="empty-state">${t("documents.empty")}</p>`;
    return;
  }

  els.documentList.innerHTML = state.documents
    .map(
      (doc) => `
        <article class="doc-item">
          <div class="doc-title">
            <span>${escapeHtml(doc.filename)}</span>
            <span class="type-pill">${escapeHtml(doc.file_type)}</span>
          </div>
          <div class="meta">
            ${t("documents.chunks")} ${doc.chunk_count} · ${doc.content_hash_prefix || t("documents.noHash")}<br />
            ${escapeHtml(doc.embedding_model)}
          </div>
        </article>
      `,
    )
    .join("");
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
    const data = await requestJson("/documents/index", {
      method: "POST",
      body: form,
    });
    showToast(data.message || t("toast.indexDone"));
    await loadDocuments();
  } catch (error) {
    showToast(error.message, true);
    setStatus("error");
  }
}

async function saveSettings(event) {
  event.preventDefault();
  const payload = {
    deepseek_base_url: els.baseUrlInput.value.trim(),
    deepseek_model: els.modelInput.value.trim(),
    request_timeout_seconds: Number(els.timeoutInput.value || 30),
    clear_api_key: els.clearApiKeyInput.checked,
    rag_system_prompt: els.systemPromptInput.value,
    rag_answer_instructions: els.answerPromptInput.value,
  };
  const apiKey = els.apiKeyInput.value.trim();
  if (apiKey) {
    payload.deepseek_api_key = apiKey;
  }

  setSettingsStatus("saving");
  try {
    const data = await requestJson("/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    els.apiKeyInput.value = "";
    els.clearApiKeyInput.checked = false;
    setSettingsStatus(data.api_key_configured ? "key" : "noKey", data.api_key_source);
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

  setStatus("asking");
  const pendingId = `pending-${Date.now()}`;
  state.messages.push({ role: "user", content: question });
  state.messages.push({ id: pendingId, role: "assistant", pending: true });
  renderMessages();
  els.questionInput.value = "";
  els.sourceList.innerHTML = "";
  try {
    const data = await requestJson("/rag/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.lastAnswer = data;
    replacePendingMessage(pendingId, {
      role: "assistant",
      content: data.reply || "",
      meta: `${data.model || t("debug.model")} · ${t("debug.sources")} ${data.source_count}`,
    });
    renderSources(data.sources || []);
    renderDebug(data);
    setStatus("done");
  } catch (error) {
    replacePendingMessage(pendingId, {
      role: "assistant",
      content: `${t("message.requestFailed")}：${error.message}`,
      error: true,
    });
    els.debugGrid.innerHTML = "";
    setStatus("error");
  }
}

function renderMessages() {
  if (!state.messages.length) {
    els.answerOutput.innerHTML = `<p class="empty-state">${t("ask.empty")}</p>`;
    return;
  }

  els.answerOutput.innerHTML = state.messages.map(renderMessage).join("");
  els.answerOutput.scrollTop = els.answerOutput.scrollHeight;
}

function renderMessage(message) {
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

  return `
    <article class="${classes.join(" ")}">
      <div class="bubble">
        ${meta}
        ${content}
      </div>
    </article>
  `;
}

function replacePendingMessage(id, nextMessage) {
  const index = state.messages.findIndex((message) => message.id === id);
  if (index >= 0) {
    state.messages[index] = nextMessage;
  } else {
    state.messages.push(nextMessage);
  }
  renderMessages();
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
  els.debugGrid.innerHTML = `
    <div class="debug-item"><span>${t("debug.retrieved")}</span><b>${data.retrieved_count}</b></div>
    <div class="debug-item"><span>${t("debug.sources")}</span><b>${data.source_count}</b></div>
    <div class="debug-item"><span>${t("debug.model")}</span><b>${escapeHtml(data.model || "-")}</b></div>
    <div class="debug-item"><span>${t("debug.tokens")}</span><b>${usage.total_tokens ?? "-"}</b></div>
  `;
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
  setStatus(els.statusPill.dataset.status || "idle");
  setSettingsStatus(els.settingsStatus.dataset.status || "noKey", els.settingsStatus.dataset.source || "");
  renderDocuments();
  renderMessages();
  if (state.lastAnswer) {
    renderSources(state.lastAnswer.sources || []);
    renderDebug(state.lastAnswer);
  }
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
  root.style.setProperty("--bg", state.preferences.backgroundColor || DEFAULT_BACKGROUND_COLOR);
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
els.askForm.addEventListener("submit", askQuestion);
els.settingsForm.addEventListener("submit", saveSettings);
els.reloadSettings.addEventListener("click", () => {
  loadSettings().catch((error) => showToast(error.message, true));
});
els.languageButtons.forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.language));
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

loadDocuments().catch((error) => {
  showToast(error.message, true);
  setStatus("error");
});
loadSettings().catch((error) => {
  showToast(error.message, true);
  if (els.settingsStatus) {
    setSettingsStatus("error");
  }
});

applyPreferences();
switchTab("import");

function insertTextareaNewline(textarea) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = textarea.value;
  textarea.value = `${value.slice(0, start)}\n${value.slice(end)}`;
  textarea.selectionStart = start + 1;
  textarea.selectionEnd = start + 1;
}
