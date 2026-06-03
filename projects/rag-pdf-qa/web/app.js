const state = {
  documents: [],
  lastAnswer: null,
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
  els.answerOutput.innerHTML = `<p class="empty-state">生成中</p>`;
  els.sourceList.innerHTML = "";
  try {
    const data = await requestJson("/rag/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.lastAnswer = data;
    renderAnswer(data);
    renderSources(data.sources || []);
    renderDebug(data);
    setStatus("done");
  } catch (error) {
    els.answerOutput.innerHTML = `<p class="danger">${escapeHtml(error.message)}</p>`;
    els.debugGrid.innerHTML = "";
    setStatus("error");
  }
}

function renderAnswer(data) {
  els.answerOutput.innerHTML = markdownLite(data.reply || "");
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
els.refreshDocuments.addEventListener("click", () => {
  loadDocuments().catch((error) => showToast(error.message, true));
});

loadDocuments().catch((error) => {
  showToast(error.message, true);
  setStatus("error");
});
