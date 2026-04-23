let mediaRecorder = null;
let audioChunks = [];

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const textBtn = document.getElementById("textBtn");
const transcriptBox = document.getElementById("transcriptBox");
const outputBox = document.getElementById("outputBox");
const recordingStatus = document.getElementById("recordingStatus");
const manualText = document.getElementById("manualText");
const reportCards = document.getElementById("reportCards");
const summaryBanner = document.getElementById("summaryBanner");

const menuItems = document.querySelectorAll(".menu-item");
const views = document.querySelectorAll(".view");

function switchView(viewId) {
  views.forEach((view) => view.classList.remove("active-view"));
  menuItems.forEach((item) => item.classList.remove("active"));

  const selectedView = document.getElementById(viewId);
  const selectedButton = document.querySelector(`.menu-item[data-view="${viewId}"]`);

  if (selectedView) selectedView.classList.add("active-view");
  if (selectedButton) selectedButton.classList.add("active");
}

menuItems.forEach((item) => {
  item.addEventListener("click", () => {
    const viewId = item.getAttribute("data-view");
    switchView(viewId);
  });
});

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function safeValue(value, fallback = "Not detected") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function renderMutedValue(value, fallback = "Not detected") {
  const hasValue = value !== null && value !== undefined && value !== "";
  return `<div class="value ${hasValue ? "" : "muted"}">${escapeHtml(safeValue(value, fallback))}</div>`;
}

function renderTagList(items, emptyText = "No items detected") {
  if (!Array.isArray(items) || items.length === 0) {
    return `<div class="value muted">${escapeHtml(emptyText)}</div>`;
  }

  return `
    <div class="tag-list">
      ${items.map((item) => `<span class="report-tag">${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderSimpleList(items, emptyText = "No items detected") {
  if (!Array.isArray(items) || items.length === 0) {
    return `<div class="value muted">${escapeHtml(emptyText)}</div>`;
  }

  return `
    <ul class="list">
      ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderVitals(vitals = {}) {
  return `
    <div class="vitals-grid">
      <div class="vital-item">
        <span class="vital-label">Blood Pressure</span>
        <div class="vital-value">${escapeHtml(safeValue(vitals.blood_pressure))}</div>
      </div>
      <div class="vital-item">
        <span class="vital-label">Heart Rate</span>
        <div class="vital-value">${escapeHtml(safeValue(vitals.heart_rate))}</div>
      </div>
      <div class="vital-item">
        <span class="vital-label">Temperature</span>
        <div class="vital-value">${escapeHtml(safeValue(vitals.temperature))}</div>
      </div>
      <div class="vital-item">
        <span class="vital-label">SpO2</span>
        <div class="vital-value">${escapeHtml(safeValue(vitals.spo2))}</div>
      </div>
    </div>
  `;
}

function renderValidationBanner(warnings = [], missing = []) {
  if ((!warnings || warnings.length === 0) && (!missing || missing.length === 0)) {
    summaryBanner.classList.add("hidden");
    summaryBanner.innerHTML = "";
    return;
  }

  summaryBanner.classList.remove("hidden");
  summaryBanner.innerHTML = `
    <div class="banner-title">Validation Summary</div>
    ${warnings.length ? `
      <div class="banner-block">
        <span class="banner-label">Warnings</span>
        <div class="tag-list">
          ${warnings.map((item) => `<span class="report-tag warning-tag">${escapeHtml(item)}</span>`).join("")}
        </div>
      </div>
    ` : ""}
    ${missing.length ? `
      <div class="banner-block">
        <span class="banner-label">Missing Mandatory Fields</span>
        <div class="tag-list">
          ${missing.map((item) => `<span class="report-tag missing-tag">${escapeHtml(item)}</span>`).join("")}
        </div>
      </div>
    ` : ""}
  `;
}

function renderStructuredCards(result) {
  const clinical = result?.clinical || {};
  const quality = result?.quality || {};
  const meta = result?.meta || {};

  const warnings = Array.isArray(quality.warnings) ? quality.warnings : [];
  const missing = Array.isArray(quality.missing_mandatory_fields)
    ? quality.missing_mandatory_fields
    : [];

  renderValidationBanner(warnings, missing);

  reportCards.innerHTML = `
    <div class="report-grid">
      <div class="info-card span-2 hero-info-card">
        <span class="label">Reason for Visit</span>
        ${renderMutedValue(clinical.reason_for_visit)}
      </div>

      <div class="info-card">
        <span class="label">Visit Date / Time</span>
        ${renderMutedValue(meta.visit_datetime)}
      </div>

      <div class="info-card">
        <span class="label">Follow-up</span>
        ${renderMutedValue(clinical.follow_up)}
      </div>

      <div class="info-card span-2">
        <span class="label">Anamnesis Brief</span>
        ${renderMutedValue(clinical.anamnesis_brief)}
      </div>

      <div class="info-card span-2">
        <span class="label">Vitals</span>
        ${renderVitals(clinical.vitals || {})}
      </div>

      <div class="info-card">
        <span class="label">Interventions</span>
        ${renderTagList(clinical.interventions, "No interventions detected")}
      </div>

      <div class="info-card">
        <span class="label">Critical Issues</span>
        ${renderTagList(clinical.critical_issues, "No critical issues detected")}
      </div>

      <div class="info-card span-2">
        <span class="label">Quality Checks</span>
        ${
          warnings.length === 0 && missing.length === 0
            ? `<div class="value">No validation issues detected.</div>`
            : `
              <div class="quality-section">
                <div class="quality-group">
                  <div class="quality-title">Warnings</div>
                  ${renderSimpleList(warnings, "No warnings")}
                </div>
                <div class="quality-group">
                  <div class="quality-title">Missing Mandatory Fields</div>
                  ${renderSimpleList(missing, "No missing fields")}
                </div>
              </div>
            `
        }
      </div>
    </div>
  `;
}

function setLoadingState(message) {
  transcriptBox.textContent = message;

  reportCards.innerHTML = `
    <div class="report-grid">
      <div class="info-card span-2 loading-card">
        <span class="label">Processing</span>
        <div class="value">${escapeHtml(message)}</div>
      </div>
    </div>
  `;

  outputBox.textContent = "";
  summaryBanner.classList.add("hidden");
  summaryBanner.innerHTML = "";
}

function renderErrorState(message) {
  reportCards.innerHTML = `
    <div class="report-grid">
      <div class="info-card span-2">
        <span class="label">Error</span>
        <div class="value">${escapeHtml(message)}</div>
      </div>
    </div>
  `;

  outputBox.textContent = "";
}

function showReportView() {
  switchView("reportView");
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data);
    };

    mediaRecorder.start();
    recordingStatus.textContent = "Recording...";
    startBtn.disabled = true;
    stopBtn.disabled = false;
  } catch (error) {
    recordingStatus.textContent = "Microphone access failed.";
    console.error(error);
  }
}

async function stopRecording() {
  if (!mediaRecorder) return;

  mediaRecorder.stop();

  mediaRecorder.onstop = async () => {
    recordingStatus.textContent = "Uploading audio...";
    startBtn.disabled = false;
    stopBtn.disabled = true;

    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", blob, "recording.webm");

    transcriptBox.textContent = "Audio received. Starting transcription...";
    setLoadingState("Transcribing audio and extracting structured data...");
    showReportView();

    try {
      const response = await fetch("/process_audio", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (data.error) {
        transcriptBox.textContent = data.error;
        renderErrorState(data.error);
        recordingStatus.textContent = "Error";
        return;
      }

      transcriptBox.textContent = data.transcript || "No transcript returned.";
      outputBox.textContent = JSON.stringify(data.result, null, 2);
      renderStructuredCards(data.result || {});
      recordingStatus.textContent = "Done";
    } catch (error) {
      transcriptBox.textContent = "Audio processing failed.";
      renderErrorState("Audio processing failed.");
      outputBox.textContent = "";
      recordingStatus.textContent = "Error";
      console.error(error);
    }
  };
}

async function processText() {
  const text = manualText.value.trim();

  if (!text) {
    transcriptBox.textContent = "Please enter some text first.";
    return;
  }

  transcriptBox.textContent = "Text received. Starting extraction...";
  setLoadingState("Processing typed note...");
  showReportView();

  try {
    const response = await fetch("/process_text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    const data = await response.json();

    if (data.error) {
      transcriptBox.textContent = data.error;
      renderErrorState(data.error);
      return;
    }

    transcriptBox.textContent = data.transcript || text;
    outputBox.textContent = JSON.stringify(data.result, null, 2);
    renderStructuredCards(data.result || {});
  } catch (error) {
    transcriptBox.textContent = "Text processing failed.";
    renderErrorState("Text processing failed.");
    outputBox.textContent = "";
    console.error(error);
  }
}

if (startBtn) startBtn.addEventListener("click", startRecording);
if (stopBtn) stopBtn.addEventListener("click", stopRecording);
if (textBtn) textBtn.addEventListener("click", processText);