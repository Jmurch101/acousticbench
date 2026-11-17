const state = {
  view: "overview",
  overview: null,
  datasets: [],
  models: [],
  runs: [],
  selectedRunId: null,
  selectedRun: null,
  comparison: null,
  busy: false,
};

const main = document.querySelector("#main");
const flash = document.querySelector("#flash");

document.body.addEventListener("click", (event) => {
  const nav = event.target.closest("nav [data-view]");
  if (nav) {
    show(nav.dataset.view);
    return;
  }
  const action = event.target.closest("[data-action]");
  if (!action || action.disabled) return;
  handleAction(action).catch((error) => setFlash(error.message, "error"));
});

document.body.addEventListener("submit", (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  if (!form.dataset.form) return;
  event.preventDefault();
  submitForm(form).catch((error) => setFlash(error.message, "error"));
});

document.body.addEventListener("change", (event) => {
  if (event.target.id === "model-id") syncModelFields();
  if (event.target.id === "eval-mode") syncEvalMode();
});

show("overview");

async function show(view) {
  state.view = view;
  document.querySelectorAll("nav [data-view]").forEach((button) => {
    button.setAttribute("aria-current", button.dataset.view === view ? "page" : "false");
  });
  try {
    if (view === "overview") state.overview = await api("/api/overview");
    if (view === "datasets" || view === "evaluate" || view === "compare") {
      state.datasets = await api("/api/datasets");
    }
    if (view === "evaluate" || view === "overview") state.models = await api("/api/models");
    if (view === "runs" || view === "compare" || view === "overview") {
      state.runs = await api("/api/runs");
    }
    if (view === "runs" && state.selectedRunId) {
      state.selectedRun = await api(`/api/runs/${state.selectedRunId}`);
    }
    render();
  } catch (error) {
    setFlash(error.message, "error");
  }
}

function render() {
  const views = {
    overview: renderOverview,
    datasets: renderDatasets,
    evaluate: renderEvaluate,
    runs: renderRuns,
    compare: renderCompare,
  };
  main.innerHTML = (views[state.view] || renderOverview)();
  if (state.view === "evaluate") {
    syncModelFields();
    syncEvalMode();
  }
}

function renderOverview() {
  const info = state.overview || {};
  const completed = state.runs.filter((run) => run.status === "completed").length;
  return `
    <section class="grid">
      <article class="card"><p class="muted">Datasets</p><p class="stat">${info.dataset_count ?? 0}</p></article>
      <article class="card"><p class="muted">Models</p><p class="stat">${info.model_count ?? 0}</p></article>
      <article class="card"><p class="muted">Runs</p><p class="stat">${info.run_count ?? 0}</p></article>
      <article class="card"><p class="muted">Completed</p><p class="stat">${completed}</p></article>
    </section>
    <section class="panel" style="margin-top:1rem">
      <h2>What this harness does</h2>
      <p>Register a simulated dataset and a real dataset, run the same acoustic classification model on each, then compare the scores. Every run stores the model, dataset, configuration, and item-level predictions.</p>
      <p class="muted">Task assumed for metrics: ${escapeHtml(info.task || "closed-set classification")}. ${escapeHtml(info.gap_definition || "")}.</p>
      <div class="row-actions">
        <button type="button" class="primary" data-view="evaluate" data-action="go">Start an evaluation</button>
        <button type="button" data-action="generate-examples">Generate example datasets</button>
        <a class="button-link" href="/api/export/runs.json">Export runs JSON</a>
      </div>
    </section>
    <section class="panel" style="margin-top:1rem">
      <h2>Built-in models</h2>
      ${modelTable(state.models)}
    </section>
  `;
}

function renderDatasets() {
  return `
    <div class="split">
      <section class="panel">
        <h2>Registered datasets</h2>
        ${datasetTable(state.datasets)}
      </section>
      <section class="stack">
        <form class="panel form-grid" data-form="dataset">
          <h2>Add a dataset</h2>
          <label>Name <input name="name" required placeholder="Room A recordings"></label>
          <label>Domain
            <select name="domain" required>
              <option value="simulated">simulated</option>
              <option value="real">real</option>
            </select>
          </label>
          <label>Layout
            <select name="layout">
              <option value="class_folders">class folders (root/label/*.wav)</option>
              <option value="csv">manifest.csv</option>
            </select>
          </label>
          <label>Folder path <input name="root_path" required placeholder="C:\\recordings\\room-a"></label>
          <label>Description <textarea name="description" placeholder="Where the audio came from and who labeled it"></textarea></label>
          <button class="primary" type="submit">Register dataset</button>
        </form>
        <section class="panel">
          <h2>Try the workflow</h2>
          <p class="muted">Generates two labeled synthetic datasets: clean signals in the simulated domain, and a degraded stand-in registered as real. Both are examples, not recordings.</p>
          <button type="button" data-action="generate-examples">Generate example datasets</button>
        </section>
      </section>
    </div>
  `;
}

function renderEvaluate() {
  return `
    <div class="split">
      <form class="panel form-grid" data-form="evaluate" id="eval-form">
        <h2>Run an evaluation</h2>
        <label>Model
          <select name="model_id" id="model-id" required>${modelOptions(state.models)}</select>
        </label>
        <p class="muted" id="model-help"></p>
        <label id="constant-label-field">Constant label <input name="constant_label" value="tone"></label>
        <label>Mode
          <select name="mode" id="eval-mode">
            <option value="paired">Paired sim-to-real</option>
            <option value="single">Single dataset</option>
          </select>
        </label>
        <label id="single-dataset">Dataset
          <select name="dataset_id">${datasetOptions(state.datasets)}</select>
        </label>
        <label id="sim-dataset">Simulated dataset
          <select name="sim_dataset_id">${datasetOptions(state.datasets, "simulated")}</select>
        </label>
        <label id="real-dataset">Real dataset
          <select name="real_dataset_id">${datasetOptions(state.datasets, "real")}</select>
        </label>
        <label>Target sample rate <input name="sample_rate" type="number" min="8000" max="48000" value="16000"></label>
        <label>Split
          <select name="split">
            <option value="all">all files</option>
            <option value="train">train</option>
            <option value="val">val</option>
            <option value="test">test</option>
          </select>
        </label>
        <label>Max items (optional) <input name="max_items" type="number" min="1" placeholder="blank uses every match"></label>
        <label>Max seconds per file <input name="max_seconds" type="number" min="0.1" max="120" step="0.1" value="30"></label>
        <label>Notes <textarea name="notes" placeholder="What question this run answers"></textarea></label>
        <label>Extra model params JSON <textarea name="model_params" placeholder="{}"></textarea></label>
        <button class="primary" type="submit" ${state.busy ? "disabled" : ""}>Start evaluation</button>
      </form>
      <section class="stack">
        <section class="panel">
          <h2>Models</h2>
          ${modelTable(state.models)}
        </section>
        <form class="panel form-grid" data-form="model">
          <h2>Register a local model</h2>
          <p class="muted">This imports Python on this machine. Use a class that subclasses AcousticModel. See examples/custom_model_template.py.</p>
          <label>Id <input name="id" required placeholder="my-classifier"></label>
          <label>Name <input name="name" required placeholder="My classifier"></label>
          <label>Python path <input name="qualified_name" required placeholder="user_models.my_model:MyModel"></label>
          <label>Description <textarea name="description"></textarea></label>
          <label>Params JSON <textarea name="params" placeholder="{}"></textarea></label>
          <button type="submit">Register model</button>
        </form>
      </section>
    </div>
  `;
}

function renderRuns() {
  const detail = state.selectedRun ? runDetail(state.selectedRun) : `<p class="muted">Select a run to see metrics, the confusion matrix, and export links.</p>`;
  return `
    <section class="panel">
      <div class="row-actions">
        <h2 style="margin-right:auto">Evaluation runs</h2>
        <a class="button-link" href="/api/export/runs.json">Export JSON</a>
      </div>
      ${runTable(state.runs)}
    </section>
    <section class="panel" style="margin-top:1rem" id="run-detail">${detail}</section>
  `;
}

function renderCompare() {
  const completed = state.runs.filter((run) => run.status === "completed");
  const simDefault = completed.find((run) => run.dataset_domain === "simulated");
  const realDefault = completed.find((run) => run.dataset_domain === "real");
  return `
    <section class="panel">
      <h2>Simulated versus real</h2>
      <p class="muted">Gap = real − simulated. Files are not paired item by item. The comparison is of aggregate scores.</p>
      <form class="form-grid" data-form="compare" style="max-width:40rem">
        <label>Simulated run
          <select name="sim_run_id" required>${runOptions(completed, simDefault && simDefault.id)}</select>
        </label>
        <label>Real run
          <select name="real_run_id" required>${runOptions(completed, realDefault && realDefault.id)}</select>
        </label>
        <button class="primary" type="submit">Compare</button>
      </form>
      <div id="comparison">${state.comparison ? comparisonView(state.comparison) : ""}</div>
    </section>
  `;
}

function datasetTable(datasets) {
  if (!datasets.length) return `<p class="muted">No datasets yet.</p>`;
  const rows = datasets.map((dataset) => {
    const inventory = dataset.inventory;
    const count = inventory ? inventory.n_items : "unavailable";
    const labels = inventory ? Object.entries(inventory.label_counts).map(([label, n]) => `${label} ${n}`).join(", ") : dataset.inventory_error || "";
    return `<tr>
      <td>${escapeHtml(dataset.name)}<div class="muted">${escapeHtml(dataset.id)}</div></td>
      <td>${badges(dataset)}</td>
      <td class="num">${escapeHtml(count)}</td>
      <td>${escapeHtml(labels)}</td>
      <td><button type="button" class="danger" data-action="delete-dataset" data-id="${escapeHtml(dataset.id)}">Remove</button></td>
    </tr>`;
  }).join("");
  return `<table><thead><tr><th>Dataset</th><th>Domain</th><th class="num">Items</th><th>Labels</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
}

function modelTable(models) {
  if (!models.length) return `<p class="muted">No models.</p>`;
  const rows = models.map((model) => `<tr>
    <td>${escapeHtml(model.name)}<div class="muted">${escapeHtml(model.id)}</div></td>
    <td>${escapeHtml(model.source)}</td>
    <td>${escapeHtml(model.description)}</td>
    <td>${model.deletable ? `<button type="button" class="danger" data-action="delete-model" data-id="${escapeHtml(model.id)}">Remove</button>` : ""}</td>
  </tr>`).join("");
  return `<table><thead><tr><th>Model</th><th>Source</th><th>Description</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
}

function runTable(runs) {
  if (!runs.length) return `<p class="muted">No runs yet. Start one from Evaluate.</p>`;
  const rows = runs.map((run) => {
    const summary = run.summary || {};
    return `<tr class="clickable" data-action="open-run" data-id="${escapeHtml(run.id)}">
      <td>${escapeHtml(run.created_at || "")}<div class="muted">${escapeHtml(run.id)}</div></td>
      <td>${escapeHtml(run.model_name)}</td>
      <td>${escapeHtml(run.dataset_name)}</td>
      <td><span class="badge ${escapeHtml(run.dataset_domain)}">${escapeHtml(run.dataset_domain)}</span></td>
      <td><span class="badge ${escapeHtml(run.status)}">${escapeHtml(run.status)}</span></td>
      <td class="num">${fmt(summary.accuracy)}</td>
      <td class="num">${fmt(summary.macro_f1)}</td>
    </tr>`;
  }).join("");
  return `<table><thead><tr><th>Created</th><th>Model</th><th>Dataset</th><th>Domain</th><th>Status</th><th class="num">Accuracy</th><th class="num">Macro F1</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function runDetail(run) {
  const summary = run.summary || {};
  const flags = (run.config && run.config.dataset_flags) || {};
  const caveat = flags.is_example || flags.synthetic || flags.synthetic_stand_in
    ? `<p class="caveat">Example or synthetic audio. These scores demonstrate the harness. They are not experimental results.</p>`
    : "";
  const error = run.error ? `<p class="caveat">${escapeHtml(run.error)}</p>` : "";
  return `
    ${caveat}
    ${error}
    <h2>${escapeHtml(run.model_name)} on ${escapeHtml(run.dataset_name)}</h2>
    <p class="muted">Run ${escapeHtml(run.id)} · ${escapeHtml(run.status)} · ${escapeHtml(run.notes || "No notes")}</p>
    <div class="grid">
      ${stat("Accuracy", fmt(summary.accuracy))}
      ${stat("Macro F1", fmt(summary.macro_f1))}
      ${stat("Weighted F1", fmt(summary.weighted_f1))}
      ${stat("Items", summary.n_evaluated != null ? `${summary.n_evaluated}/${summary.n_items}` : "—")}
      ${stat("Mean latency", summary.mean_latency_ms != null ? `${fmt(summary.mean_latency_ms)} ms` : "—")}
      ${stat("Calibration error", fmt(summary.ece))}
    </div>
    <h3>Per class</h3>
    ${perClassTable(summary.per_class)}
    <h3>Confusion matrix</h3>
    <p class="muted">Rows are true labels. Columns are predictions.</p>
    ${matrixTable(summary.confusion_matrix)}
    <div class="row-actions">
      <a class="button-link" href="/api/runs/${encodeURIComponent(run.id)}/report.html" target="_blank" rel="noreferrer">View report</a>
      <a class="button-link" href="/api/runs/${encodeURIComponent(run.id)}/report.md">Download Markdown</a>
      <a class="button-link" href="/api/runs/${encodeURIComponent(run.id)}/predictions.csv">Download predictions</a>
    </div>
  `;
}

function comparisonView(comparison) {
  const warnings = (comparison.warnings || []).map((warning) => `<li>${escapeHtml(warning)}</li>`).join("");
  const metrics = (comparison.metrics || []).map((metric) => `<tr>
    <td>${escapeHtml(metric.label)}</td>
    <td class="num">${fmt(metric.simulated)}</td>
    <td class="num">${fmt(metric.real)}</td>
    <td class="num ${gapClass(metric)}">${fmt(metric.gap)}</td>
  </tr>`).join("");
  const classes = (comparison.per_class_f1 || []).map((row) => `<tr>
    <td>${escapeHtml(row.label)}</td>
    <td class="num">${fmt(row.simulated_f1)}</td>
    <td class="num">${fmt(row.real_f1)}</td>
    <td class="num">${fmt(row.gap)}</td>
    <td class="num">${escapeHtml(row.simulated_support)}</td>
    <td class="num">${escapeHtml(row.real_support)}</td>
  </tr>`).join("");
  const sim = comparison.sim_run_id;
  const real = comparison.real_run_id;
  return `
    <h3>Result</h3>
    ${warnings ? `<ul>${warnings}</ul>` : ""}
    <p class="muted">Green means the real run is better on that metric. Rust means it is worse. Latency and calibration error are costs.</p>
    <table>
      <thead><tr><th>Metric</th><th class="num">Simulated</th><th class="num">Real</th><th class="num">Gap</th></tr></thead>
      <tbody>${metrics}</tbody>
    </table>
    <h3>Per-class F1</h3>
    <table>
      <thead><tr><th>Class</th><th class="num">Simulated</th><th class="num">Real</th><th class="num">Gap</th><th class="num">Sim n</th><th class="num">Real n</th></tr></thead>
      <tbody>${classes || `<tr><td colspan="6">No shared labels.</td></tr>`}</tbody>
    </table>
    <div class="row-actions">
      <a class="button-link" href="/api/compare/report.html?sim=${encodeURIComponent(sim)}&real=${encodeURIComponent(real)}" target="_blank" rel="noreferrer">View report</a>
      <a class="button-link" href="/api/compare/report.md?sim=${encodeURIComponent(sim)}&real=${encodeURIComponent(real)}">Download Markdown</a>
    </div>
  `;
}

function perClassTable(perClass) {
  const entries = Object.entries(perClass || {});
  if (!entries.length) return `<p class="muted">No per-class scores.</p>`;
  const rows = entries.map(([label, stats]) => `<tr>
    <td>${escapeHtml(label)}</td>
    <td class="num">${fmt(stats.precision)}</td>
    <td class="num">${fmt(stats.recall)}</td>
    <td class="num">${fmt(stats.f1)}</td>
    <td class="num">${escapeHtml(stats.support)}</td>
  </tr>`).join("");
  return `<table><thead><tr><th>Class</th><th class="num">Precision</th><th class="num">Recall</th><th class="num">F1</th><th class="num">Support</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function matrixTable(matrix) {
  if (!matrix || !matrix.labels || !matrix.labels.length) return `<p class="muted">No confusion matrix.</p>`;
  const max = Math.max(1, ...matrix.counts.flat());
  const head = matrix.labels.map((label) => `<th class="num">${escapeHtml(label)}</th>`).join("");
  const body = matrix.labels.map((label, rowIndex) => {
    const cells = matrix.counts[rowIndex].map((count) => {
      const alpha = 0.08 + 0.45 * (count / max);
      return `<td class="num" style="background: rgba(35, 78, 155, ${alpha.toFixed(3)})">${count}</td>`;
    }).join("");
    return `<tr><th class="label">${escapeHtml(label)}</th>${cells}</tr>`;
  }).join("");
  return `<div class="matrix"><table><thead><tr><th class="label">True \\ predicted</th>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

async function handleAction(action) {
  const name = action.dataset.action;
  if (name === "go") {
    show(action.dataset.view);
    return;
  }
  if (name === "generate-examples") {
    setFlash("Generating synthetic example audio...", "info");
    await api("/api/examples/generate", { method: "POST" });
    setFlash("Example datasets are ready. They are synthetic, not study recordings.", "ok");
    await show(state.view);
    return;
  }
  if (name === "delete-dataset") {
    if (!confirm("Remove this dataset from AcoustiBench? Audio files are left on disk.")) return;
    await api(`/api/datasets/${encodeURIComponent(action.dataset.id)}`, { method: "DELETE" });
    setFlash("Dataset removed from the registry.", "ok");
    await show("datasets");
    return;
  }
  if (name === "delete-model") {
    if (!confirm("Remove this registered model? The Python file is left in place.")) return;
    await api(`/api/models/${encodeURIComponent(action.dataset.id)}`, { method: "DELETE" });
    setFlash("Model removed.", "ok");
    await show("evaluate");
    return;
  }
  if (name === "open-run") {
    state.selectedRunId = action.dataset.id;
    state.selectedRun = await api(`/api/runs/${state.selectedRunId}`);
    render();
    document.querySelector("#run-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

async function submitForm(form) {
  if (form.dataset.form === "dataset") {
    const body = Object.fromEntries(new FormData(form).entries());
    await api("/api/datasets", { method: "POST", body: JSON.stringify(body) });
    setFlash("Dataset registered.", "ok");
    form.reset();
    await show("datasets");
    return;
  }
  if (form.dataset.form === "model") {
    const body = Object.fromEntries(new FormData(form).entries());
    body.params = parseJsonObject(body.params, "Model params");
    await api("/api/models", { method: "POST", body: JSON.stringify(body) });
    setFlash("Model registered. It will run as local Python when you evaluate.", "ok");
    form.reset();
    await show("evaluate");
    return;
  }
  if (form.dataset.form === "evaluate") {
    await startEvaluation(form);
    return;
  }
  if (form.dataset.form === "compare") {
    const body = Object.fromEntries(new FormData(form).entries());
    state.comparison = await api("/api/compare", { method: "POST", body: JSON.stringify(body) });
    setFlash("Comparison ready. Read the warnings before using it in a presentation.", "ok");
    render();
  }
}

async function startEvaluation(form) {
  const values = Object.fromEntries(new FormData(form).entries());
  const modelParams = parseJsonObject(values.model_params, "Model params");
  if (values.model_id === "constant-label" && values.constant_label) {
    modelParams.label = values.constant_label;
  }
  const payload = {
    model_id: values.model_id,
    sample_rate: Number(values.sample_rate),
    split: values.split,
    max_items: values.max_items ? Number(values.max_items) : null,
    max_seconds: values.max_seconds ? Number(values.max_seconds) : null,
    notes: values.notes,
    model_params: modelParams,
  };
  state.busy = true;
  render();
  try {
    if (values.mode === "paired") {
      payload.sim_dataset_id = values.sim_dataset_id;
      payload.real_dataset_id = values.real_dataset_id;
      setFlash("Running the model on both datasets...", "info");
      const started = await api("/api/evaluations/paired", { method: "POST", body: JSON.stringify(payload) });
      const simulated = await pollRun(started.simulated.id);
      const real = await pollRun(started.real.id);
      if (simulated.status !== "completed" || real.status !== "completed") {
        throw new Error(simulated.error || real.error || "One of the paired runs failed.");
      }
      state.comparison = await api("/api/compare", {
        method: "POST",
        body: JSON.stringify({ sim_run_id: simulated.id, real_run_id: real.id }),
      });
      setFlash("Paired evaluation finished.", "ok");
      await show("compare");
      return;
    }
    payload.dataset_id = values.dataset_id;
    setFlash("Evaluation running...", "info");
    const started = await api("/api/evaluations", { method: "POST", body: JSON.stringify(payload) });
    const finished = await pollRun(started.id);
    if (finished.status !== "completed") throw new Error(finished.error || "Evaluation failed.");
    state.selectedRunId = finished.id;
    state.selectedRun = finished;
    setFlash("Evaluation finished.", "ok");
    state.busy = false;
    await show("runs");
  } catch (error) {
    state.busy = false;
    if (state.view === "evaluate") render();
    throw error;
  }
}

async function pollRun(id) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const run = await api(`/api/runs/${id}`);
    if (run.status === "completed" || run.status === "failed") return run;
    await delay(500);
  }
  throw new Error("The run is still going. Check the Runs page in a moment.");
}

function syncModelFields() {
  const select = document.querySelector("#model-id");
  const help = document.querySelector("#model-help");
  const constant = document.querySelector("#constant-label-field");
  if (!select || !help || !constant) return;
  const model = state.models.find((item) => item.id === select.value);
  help.textContent = model ? model.description : "";
  constant.hidden = select.value !== "constant-label";
}

function syncEvalMode() {
  const mode = document.querySelector("#eval-mode")?.value || "paired";
  const single = document.querySelector("#single-dataset");
  const sim = document.querySelector("#sim-dataset");
  const real = document.querySelector("#real-dataset");
  if (!single || !sim || !real) return;
  single.hidden = mode !== "single";
  sim.hidden = mode !== "paired";
  real.hidden = mode !== "paired";
}

function datasetOptions(datasets, preferredDomain) {
  if (!datasets.length) return `<option value="">Generate or add a dataset first</option>`;
  const ordered = [...datasets].sort((a, b) => {
    if (a.domain === preferredDomain && b.domain !== preferredDomain) return -1;
    if (b.domain === preferredDomain && a.domain !== preferredDomain) return 1;
    return a.name.localeCompare(b.name);
  });
  return ordered.map((dataset) => {
    const marks = dataset.is_example ? " example" : "";
    return `<option value="${escapeHtml(dataset.id)}">${escapeHtml(dataset.name)} · ${escapeHtml(dataset.domain)}${marks}</option>`;
  }).join("");
}

function modelOptions(models) {
  if (!models.length) return `<option value="">No models</option>`;
  return models.map((model) => `<option value="${escapeHtml(model.id)}">${escapeHtml(model.name)}</option>`).join("");
}

function runOptions(runs, selected) {
  if (!runs.length) return `<option value="">No completed runs</option>`;
  return runs.map((run) => {
    const summary = run.summary || {};
    const selectedAttr = run.id === selected ? "selected" : "";
    return `<option value="${escapeHtml(run.id)}" ${selectedAttr}>${escapeHtml(run.dataset_domain)} · ${escapeHtml(run.model_name)} · acc ${fmt(summary.accuracy)} · ${escapeHtml(run.id)}</option>`;
  }).join("");
}

function badges(dataset) {
  const parts = [`<span class="badge ${escapeHtml(dataset.domain)}">${escapeHtml(dataset.domain)}</span>`];
  if (dataset.is_example) parts.push(`<span class="badge example">example</span>`);
  if (dataset.synthetic_stand_in) parts.push(`<span class="badge example">synthetic stand-in</span>`);
  return parts.join(" ");
}

function stat(label, value) {
  return `<article class="card"><p class="muted">${escapeHtml(label)}</p><p class="stat">${escapeHtml(value)}</p></article>`;
}

function gapClass(metric) {
  if (typeof metric.gap !== "number" || metric.gap === 0) return "";
  const realIsBetter = metric.better === "higher" ? metric.gap > 0 : metric.gap < 0;
  return realIsBetter ? "gap-better" : "gap-worse";
}

function fmt(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(3);
}

function parseJsonObject(text, label) {
  const raw = (text || "").trim();
  if (!raw) return {};
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_error) {
    throw new Error(`${label} must be a JSON object.`);
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} must be a JSON object.`);
  }
  return parsed;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data && data.detail ? data.detail : response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

function setFlash(message, kind) {
  flash.textContent = message;
  flash.className = `flash ${kind || "info"}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
