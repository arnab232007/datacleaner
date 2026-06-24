/**
 * DataCleaner — Frontend App Controller
 * Handles: file drag-drop, upload XHR, polling, charts, downloads.
 */
"use strict";

/* ── State ─────────────────────────────────────────── */
const state = {
  fileId:  null,
  jobId:   null,
  result:  null,
  pollTimer: null,
};

const API = "";   // same-origin; change to "http://localhost:5000" for dev

/* ── Init ──────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  AOS.init({ duration: 600, once: true });
  initParticles();
  initMinecraftBlocks();
  initDropZone();
  initButtons();
});

/* ── Particles ─────────────────────────────────────── */
function initParticles() {
  if (typeof particlesJS === "undefined") return;
  particlesJS("particles-js", {
    particles: {
      number: { value: 55, density: { enable: true, value_area: 800 } },
      color: { value: ["#5c7cff", "#9b6dff", "#00e5ff"] },
      shape: { type: "circle" },
      opacity: { value: 0.35, random: true },
      size: { value: 2.5, random: true },
      line_linked: { enable: true, distance: 130, color: "#5c7cff", opacity: 0.18, width: 1 },
      move: { enable: true, speed: 1.2, random: true, out_mode: "out" },
    },
    interactivity: {
      detect_on: "canvas",
      events: { onhover: { enable: true, mode: "repulse" } },
    },
    retina_detect: true,
  });
}

/* ── Minecraft blocks ──────────────────────────────── */
function initMinecraftBlocks() {
  const container = document.getElementById("mc-blocks");
  if (!container) return;
  const colors = ["rgba(92,124,255,.25)", "rgba(155,109,255,.2)", "rgba(0,229,255,.2)"];
  for (let i = 0; i < 12; i++) {
    const el = document.createElement("div");
    el.className = "mc-block";
    el.style.cssText = `
      left: ${Math.random() * 95}%;
      top:  ${Math.random() * 90}%;
      width: ${24 + Math.random() * 28}px;
      height: ${24 + Math.random() * 28}px;
      border-color: ${colors[i % colors.length]};
      animation-delay: ${(Math.random() * 6).toFixed(1)}s;
      animation-duration: ${6 + Math.random() * 6}s;
    `;
    container.appendChild(el);
  }
}

/* ── Drop Zone ─────────────────────────────────────── */
function initDropZone() {
  const zone  = document.getElementById("drop-zone");
  const input = document.getElementById("file-input");

  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => input.files[0] && handleFile(input.files[0]));

  zone.addEventListener("dragover",  e => { e.preventDefault(); zone.classList.add("drag-over"); });
  zone.addEventListener("dragleave", ()  => zone.classList.remove("drag-over"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  });
}

function handleFile(file) {
  const allowed = ["csv", "xls", "xlsx"];
  const ext = file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) return alert("Please upload a CSV, XLS, or XLSX file.");
  uploadFile(file);
}

/* ── Upload ────────────────────────────────────────── */
function uploadFile(file) {
  const progWrap = document.getElementById("upload-progress");
  const progBar  = document.getElementById("upload-bar");
  const progPct  = document.getElementById("upload-pct");
  progWrap.classList.remove("d-none");

  const fd = new FormData();
  fd.append("file", file);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", `${API}/api/upload`);

  xhr.upload.onprogress = e => {
    if (e.lengthComputable) {
      const pct = Math.round(e.loaded / e.total * 100);
      progBar.style.width = pct + "%";
      progPct.textContent  = pct + "%";
    }
  };

  xhr.onload = () => {
    const res = JSON.parse(xhr.responseText);
    if (!res.ok) return showError(res.error);
    state.fileId = res.file_id;
    showFileMeta(res);
    showConfigPanel();
    progWrap.classList.add("d-none");
  };

  xhr.onerror = () => showError("Upload failed. Is the backend running?");
  xhr.send(fd);
}

function showFileMeta(meta) {
  document.getElementById("meta-name").textContent =
    `${meta.filename}`;
  document.getElementById("meta-details").textContent =
    `${meta.size} · ${meta.rows.toLocaleString()} rows · ${meta.columns} columns`;
  document.getElementById("file-meta").classList.remove("d-none");
}

function showConfigPanel() {
  document.getElementById("config-panel").classList.remove("d-none");
  document.getElementById("config-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/* ── Buttons ───────────────────────────────────────── */
function initButtons() {
  document.getElementById("start-clean-btn").addEventListener("click", startCleaning);
  document.getElementById("dl-csv") .addEventListener("click", () => download("csv"));
  document.getElementById("dl-xlsx").addEventListener("click", () => download("xlsx"));
  document.getElementById("dl-pdf") .addEventListener("click", () => downloadReport("pdf"));
  document.getElementById("dl-html").addEventListener("click", () => downloadReport("html"));
  document.getElementById("reset-btn").addEventListener("click", resetAll);
}

/* ── Start cleaning ────────────────────────────────── */
function startCleaning() {
  if (!state.fileId) return;
  const cfg = {
    missing_num_strategy:   document.getElementById("cfg-missing-num").value,
    missing_cat_strategy:   "mode",
    missing_drop_threshold: parseFloat(document.getElementById("cfg-drop-thresh").value),
    outlier_method:         document.getElementById("cfg-outlier-method").value,
    outlier_action:         document.getElementById("cfg-outlier-action").value,
    clean_text:             document.getElementById("cfg-text").checked,
    standardize_dates:      document.getElementById("cfg-dates").checked,
    clean_col_names:        document.getElementById("cfg-colnames").checked,
  };

  fetch(`${API}/api/clean/${state.fileId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  })
    .then(r => r.json())
    .then(res => {
      if (!res.ok) return showError(res.error);
      state.jobId = res.job_id;
      showProcessingSection();
      startPolling();
    })
    .catch(() => showError("Failed to start cleaning job."));
}

/* ── Processing section ────────────────────────────── */
const STEPS = [
  "Loading file", "Cleaning column names", "Correcting data types",
  "Handling missing values", "Removing duplicates", "Detecting outliers",
  "Standardising text", "Standardising dates", "Writing output files",
  "Generating reports",
];

function showProcessingSection() {
  document.getElementById("upload-section").classList.add("d-none");
  const sec = document.getElementById("processing-section");
  sec.classList.remove("d-none");
  sec.scrollIntoView({ behavior: "smooth" });

  const tracker = document.getElementById("step-tracker");
  tracker.innerHTML = STEPS.map((s, i) => `
    <div class="step-item" id="step-${i}">
      <div class="step-dot"><i class="fa-solid fa-circle" style="font-size:.5rem"></i></div>
      <span>${s}</span>
    </div>`).join("");
}

function startPolling() {
  state.pollTimer = setInterval(pollStatus, 1200);
}

function pollStatus() {
  fetch(`${API}/api/status/${state.jobId}`)
    .then(r => r.json())
    .then(res => {
      if (!res.ok) return;
      updateProgress(res.step, res.progress);
      if (res.status === "done")  { clearInterval(state.pollTimer); fetchResult(); }
      if (res.status === "error") { clearInterval(state.pollTimer); showError(res.error); }
    });
}

function updateProgress(stepLabel, pct) {
  document.getElementById("current-step-label").textContent = stepLabel;
  document.getElementById("current-pct").textContent = pct + "%";
  document.getElementById("pipeline-bar").style.width = pct + "%";

  const idx = STEPS.findIndex(s => s.toLowerCase() === stepLabel.toLowerCase());
  STEPS.forEach((_, i) => {
    const el = document.getElementById("step-" + i);
    if (!el) return;
    el.classList.remove("active", "done");
    if (i < idx) el.classList.add("done");
    if (i === idx) el.classList.add("active");
    const dot = el.querySelector(".step-dot i");
    if (i < idx) dot.className = "fa-solid fa-check";
    if (i === idx) dot.className = "fa-solid fa-spinner fa-spin";
    if (i > idx) dot.className = "fa-solid fa-circle";
  });
}

/* ── Fetch result & render ─────────────────────────── */
function fetchResult() {
  fetch(`${API}/api/result/${state.jobId}`)
    .then(r => r.json())
    .then(res => {
      if (!res.ok) return showError(res.error);
      state.result = res.result;
      showResults(res.result);
    });
}

function showResults(r) {
  document.getElementById("processing-section").classList.add("d-none");
  const sec = document.getElementById("results-section");
  sec.classList.remove("d-none");
  sec.scrollIntoView({ behavior: "smooth" });

  // Stat cards
  const cards = [
    { num: r.original_rows.toLocaleString(), lbl: "Original rows",      color: "#5c7cff" },
    { num: r.cleaned_rows.toLocaleString(),  lbl: "Cleaned rows",       color: "#22d67a" },
    { num: r.removed_rows.toLocaleString(),  lbl: "Rows removed",       color: "#e05260" },
    { num: r.nulls_fixed.toLocaleString(),   lbl: "Nulls fixed",        color: "#00e5ff" },
    { num: r.duplicates_removed.toLocaleString(), lbl: "Dupes removed", color: "#f5a623" },
    { num: r.outliers_handled.toLocaleString(),   lbl: "Outliers handled", color: "#9b6dff" },
  ];
  document.getElementById("stat-cards").innerHTML = cards.map(c => `
    <div class="col-6 col-md-4 col-lg-2">
      <div class="stat-card">
        <div class="sc-num" style="color:${c.color}">${c.num}</div>
        <div class="sc-lbl">${c.lbl}</div>
      </div>
    </div>`).join("");

  // Audit log
  document.getElementById("audit-list").innerHTML =
    (r.audit_log || []).map(a => `<li>${a}</li>`).join("");

  // Charts
  renderCharts(r);
}

/* ── Charts ────────────────────────────────────────── */
function renderCharts(r) {
  // Bar: before vs after rows
  const ctx1 = document.getElementById("chart-rows").getContext("2d");
  new Chart(ctx1, {
    type: "bar",
    data: {
      labels: ["Original", "Cleaned"],
      datasets: [{ data: [r.original_rows, r.cleaned_rows],
        backgroundColor: ["rgba(92,124,255,.7)", "rgba(34,214,122,.7)"],
        borderColor: ["#5c7cff", "#22d67a"], borderWidth: 2, borderRadius: 8 }],
    },
    options: {
      responsive: true, plugins: { legend: { display: false } },
      scales: { y: { grid: { color: "rgba(255,255,255,.06)" },
                     ticks: { color: "#7a86b8" } },
                x: { grid: { display: false }, ticks: { color: "#7a86b8" } } },
    },
  });

  // Doughnut: breakdown
  const ctx2 = document.getElementById("chart-breakdown").getContext("2d");
  new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: ["Nulls fixed", "Dupes removed", "Outliers handled", "Clean rows"],
      datasets: [{ data: [r.nulls_fixed, r.duplicates_removed, r.outliers_handled, r.cleaned_rows],
        backgroundColor: ["rgba(0,229,255,.7)", "rgba(245,166,35,.7)",
                          "rgba(155,109,255,.7)", "rgba(34,214,122,.7)"],
        borderWidth: 0, hoverOffset: 6 }],
    },
    options: {
      responsive: true, cutout: "68%",
      plugins: { legend: { labels: { color: "#7a86b8", boxWidth: 12 } } },
    },
  });
}

/* ── Downloads ─────────────────────────────────────── */
function download(fmt) {
  window.location.href = `${API}/api/download/${state.jobId}/${fmt}`;
}
function downloadReport(fmt) {
  if (fmt === "html") {
    window.open(`${API}/api/report/${state.jobId}/html`, "_blank");
  } else {
    window.location.href = `${API}/api/report/${state.jobId}/pdf`;
  }
}

/* ── Reset ─────────────────────────────────────────── */
function resetAll() {
  state.fileId = state.jobId = state.result = null;
  clearInterval(state.pollTimer);
  document.getElementById("file-meta").classList.add("d-none");
  document.getElementById("config-panel").classList.add("d-none");
  document.getElementById("upload-progress").classList.add("d-none");
  document.getElementById("results-section").classList.add("d-none");
  document.getElementById("processing-section").classList.add("d-none");
  document.getElementById("upload-section").classList.remove("d-none");
  document.getElementById("file-input").value = "";
  document.getElementById("upload-section").scrollIntoView({ behavior: "smooth" });
}

/* ── Error helper ──────────────────────────────────── */
function showError(msg) {
  alert("Error: " + msg);
}
