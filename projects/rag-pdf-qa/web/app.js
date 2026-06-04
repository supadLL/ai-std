const state = {
  documents: [],
  lastAnswer: null,
  messages: [],
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
};

function setStatus(value) {
  els.statusPill.textContent = value;
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

  els.settingsStatus.textContent = "loading";
  const data = await requestJson("/settings");
  els.baseUrlInput.value = data.deepseek_base_url || "";
  els.modelInput.value = data.deepseek_model || "";
  els.timeoutInput.value = data.request_timeout_seconds || 30;
  els.apiKeyInput.value = "";
  els.clearApiKeyInput.checked = false;
  els.systemPromptInput.value = data.rag_system_prompt || "";
  els.answerPromptInput.value = data.rag_answer_instructions || "";
  els.settingsStatus.textContent = data.api_key_configured ? `key:${data.api_key_source}` : "no-key";
}

function renderDocuments() {
  if (!state.documents.length) {
    els.documentList.innerHTML = `<p class="empty-state">暂无文档</p>`;
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
            chunks ${doc.chunk_count} · ${doc.content_hash_prefix || "no-hash"}<br />
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
    showToast("请选择文件", true);
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
    showToast(data.message || "索引完成");
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

  els.settingsStatus.textContent = "saving";
  try {
    const data = await requestJson("/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    els.apiKeyInput.value = "";
    els.clearApiKeyInput.checked = false;
    els.settingsStatus.textContent = data.api_key_configured ? `key:${data.api_key_source}` : "no-key";
    showToast("设置已保存");
  } catch (error) {
    els.settingsStatus.textContent = "error";
    showToast(error.message, true);
  }
}

async function askQuestion(event) {
  event.preventDefault();
  const question = els.questionInput.value.trim();
  if (!question) {
    showToast("请输入问题", true);
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
      meta: `${data.model || "model"} · sources ${data.source_count}`,
    });
    renderSources(data.sources || []);
    renderDebug(data);
    setStatus("done");
  } catch (error) {
    replacePendingMessage(pendingId, {
      role: "assistant",
      content: `请求失败：${error.message}`,
      error: true,
    });
    els.debugGrid.innerHTML = "";
    setStatus("error");
  }
}

function renderMessages() {
  if (!state.messages.length) {
    els.answerOutput.innerHTML = `<p class="empty-state">等待问题</p>`;
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
          <div class="bubble-meta">AI 正在解析检索结果</div>
          <span class="thinking">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            整理答案中
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
    els.sourceList.innerHTML = `<p class="empty-state">无 sources</p>`;
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
    <div class="debug-item"><span>retrieved</span><b>${data.retrieved_count}</b></div>
    <div class="debug-item"><span>sources</span><b>${data.source_count}</b></div>
    <div class="debug-item"><span>model</span><b>${escapeHtml(data.model || "-")}</b></div>
    <div class="debug-item"><span>tokens</span><b>${usage.total_tokens ?? "-"}</b></div>
  `;
}

function markdownLite(text) {
  const escaped = escapeHtml(text);
  return escaped
    .replace(/^答案：/gm, "<strong>答案：</strong>")
    .replace(/^依据：/gm, "<strong>依据：</strong>")
    .replace(/^资料不足之处：/gm, "<strong>资料不足之处：</strong>")
    .replace(/\n/g, "<br />");
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
    els.settingsStatus.textContent = "error";
  }
});

switchTab("import");

function insertTextareaNewline(textarea) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = textarea.value;
  textarea.value = `${value.slice(0, start)}\n${value.slice(end)}`;
  textarea.selectionStart = start + 1;
  textarea.selectionEnd = start + 1;
}
