(() => {
  const fallbackData = {
    system: {
      status: "healthy",
      uptime: "4d 6h",
      version: "0.8.1",
      api_url: "http://localhost:8000",
      mode: "pilot"
    },
    metrics: {
      models_loaded: 7,
      total_extractions: 48210,
      avg_processing_time: "1.8s",
      errors: 3,
      cache_size: "1.4GB",
      request_rate: "42/min",
      requests_today: 12840,
      avg_latency_ms: 84,
      queue_depth: 17,
      active_connectors: 6,
      pipelines_running: 3
    },
    capabilities: [
      "routing",
      "entities",
      "concepts",
      "multilingual",
      "streaming",
      "batch",
      "governance"
    ],
    models: [
      { name: "Atlas-7B", type: "semantic", status: "ok", version: "v2.1", size: "7B" },
      { name: "Delta-2", type: "multilingual", status: "warming", version: "v1.4", size: "2B" },
      { name: "VectorGuard", type: "safety", status: "ok", version: "v3.0", size: "6B" },
      { name: "SignalNet", type: "stream", status: "ok", version: "v1.9", size: "1.3B" }
    ],
    endpoints: [
      { method: "POST", path: "/v1/extract", status: "ok", latency: "84ms" },
      { method: "POST", path: "/v1/batch", status: "queued", latency: "220ms" },
      { method: "GET", path: "/v1/health", status: "ok", latency: "24ms" },
      { method: "POST", path: "/v1/stream", status: "warming", latency: "140ms" }
    ],
    connections: [
      { name: "SEO Tool", type: "python_module", status: "linked", latency_ms: 84 },
      { name: "CMS Sync", type: "api", status: "linked", latency_ms: 126 },
      { name: "Keyword Lab", type: "internal", status: "warming", latency_ms: 210 },
      { name: "Vector DB", type: "storage", status: "linked", latency_ms: 32 },
      { name: "Analytics", type: "external", status: "queued", latency_ms: 0 },
      { name: "Audit Bot", type: "agent", status: "linked", latency_ms: 64 }
    ],
    pipelines: [
      { name: "Content Enrichment", mode: "api", state: "running", throughput: "2.1k docs/day" },
      { name: "Site Crawl", mode: "batch", state: "paused", throughput: "0.9k urls/day" },
      { name: "Brand Index", mode: "module", state: "running", throughput: "620 docs/day" }
    ],
    runs: [
      { id: "run_4021", status: "ok", duration: "4m 12s", summary: "12 docs processed" },
      { id: "run_4020", status: "warn", duration: "5m 03s", summary: "cache miss spike" },
      { id: "run_4019", status: "ok", duration: "3m 58s", summary: "9 docs processed" }
    ],
    activity: [
      { time: "2m ago", text: "SEO Tool requested semantic ranker", status: "linked" },
      { time: "12m ago", text: "CMS Sync pushed 142 documents", status: "ok" },
      { time: "34m ago", text: "New connector approved: Audit Bot", status: "ok" },
      { time: "1h ago", text: "Pipeline Site Crawl paused (quota)", status: "paused" }
    ],
    languages: ["en", "sv", "de", "fr", "es", "pt"],
    samples: [
      {
        title: "Release note",
        text: "SIE-X 0.9 adds streaming extraction and multilingual keyword tagging for European markets."
      },
      {
        title: "Customer brief",
        text: "Acme Retail wants daily product feeds, entity linking, and compliance flags for regulated markets."
      },
      {
        title: "Incident summary",
        text: "Cache latency spiked after Atlas-7B reload; batch queue depth doubled in 12 minutes."
      }
    ],
    flight_actions: [
      {
        name: "Warm models",
        tag: "core",
        status: "ok",
        description: "Prime Atlas + VectorGuard to reduce cold starts.",
        eta: "3-5 min",
        owner: "siex-core"
      },
      {
        name: "Sync knowledge vault",
        tag: "kb",
        status: "running",
        description: "Pull latest Claude + Maps indexes for fusion.",
        eta: "8 min",
        owner: "siex-kb"
      },
      {
        name: "Flush cache",
        tag: "ops",
        status: "queued",
        description: "Clear stale embeddings and refresh route cache.",
        eta: "1 min",
        owner: "siex-ops"
      },
      {
        name: "Run smoke checks",
        tag: "qa",
        status: "paused",
        description: "Validate API health and tool surfaces.",
        eta: "6 min",
        owner: "siex-qa"
      }
    ],
    alerts: [
      {
        title: "Queue pressure",
        tone: "warn",
        summary: "Batch queue above target, consider a warmup run.",
        eta: "15m",
        impact: "medium"
      },
      {
        title: "Cache warmed",
        tone: "ok",
        summary: "Atlas-7B vectors refreshed, latency stabilized.",
        eta: "now",
        impact: "low"
      },
      {
        title: "Connector drift",
        tone: "warn",
        summary: "CMS Sync latency trending above 150ms.",
        eta: "30m",
        impact: "medium"
      }
    ],
    focus: [
      {
        title: "Re-index Claude vault",
        owner: "kb",
        eta: "today",
        status: "active"
      },
      {
        title: "Route planner sync",
        owner: "geo",
        eta: "2h",
        status: "planned"
      },
      {
        title: "SIE-X API hardening",
        owner: "core",
        eta: "tomorrow",
        status: "planned"
      }
    ]
  };

  const STOPWORDS = new Set([
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "he", "her", "his", "in", "is", "it", "its", "of",
    "on", "or", "our", "she", "that", "the", "their", "they", "this", "to",
    "was", "we", "were", "will", "with", "you", "your", "but", "not", "into",
    "over", "after", "before", "about", "than", "then", "also", "can", "could",
    "should", "would", "may", "might", "if", "when", "where", "who", "what"
  ]);

  const state = {
    data: fallbackData,
    totalExtractions: Number(fallbackData.metrics.total_extractions) || 0
  };

  const statusDotMap = {
    ok: "ok",
    healthy: "ok",
    online: "ok",
    warn: "warn",
    warning: "warn",
    degraded: "warn"
  };

  let drawerRefs = null;

  function normalizeData(raw) {
    const data = raw || {};
    return {
      ...fallbackData,
      ...data,
      system: { ...fallbackData.system, ...(data.system || {}) },
      metrics: { ...fallbackData.metrics, ...(data.metrics || {}) },
      capabilities: Array.isArray(data.capabilities) ? data.capabilities : fallbackData.capabilities,
      models: Array.isArray(data.models) ? data.models : fallbackData.models,
      endpoints: Array.isArray(data.endpoints) ? data.endpoints : fallbackData.endpoints,
      connections: Array.isArray(data.connections) ? data.connections : fallbackData.connections,
      pipelines: Array.isArray(data.pipelines) ? data.pipelines : fallbackData.pipelines,
      runs: Array.isArray(data.runs) ? data.runs : fallbackData.runs,
      activity: Array.isArray(data.activity) ? data.activity : fallbackData.activity,
      languages: Array.isArray(data.languages) ? data.languages : fallbackData.languages,
      samples: Array.isArray(data.samples) ? data.samples : fallbackData.samples,
      flight_actions: Array.isArray(data.flight_actions) ? data.flight_actions : fallbackData.flight_actions,
      alerts: Array.isArray(data.alerts) ? data.alerts : fallbackData.alerts,
      focus: Array.isArray(data.focus) ? data.focus : fallbackData.focus
    };
  }

  async function loadData() {
    try {
      const response = await fetch("data/mock.json", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Mock data fetch failed");
      }
      const raw = await response.json();
      return normalizeData(raw);
    } catch (error) {
      return normalizeData(fallbackData);
    }
  }

  function formatValue(value) {
    if (value === null || value === undefined || value === "") {
      return "--";
    }
    if (typeof value === "number") {
      return value.toLocaleString();
    }
    return String(value);
  }

  function formatTimeStamp(date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function setStat(key, value) {
    document.querySelectorAll(`[data-stat="${key}"]`).forEach((node) => {
      node.textContent = formatValue(value);
    });
  }

  function setMeter(key, value) {
    const width = clampNumber(Number(value), 0, 100);
    document.querySelectorAll(`[data-meter="${key}"]`).forEach((node) => {
      node.style.width = `${width}%`;
    });
  }

  function setCommandError(message) {
    document.querySelectorAll('[data-stat="command_error"]').forEach((node) => {
      node.textContent = message || "";
    });
  }

  function formatMs(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) {
      return "--";
    }
    return `${Math.round(numeric)}ms`;
  }

  function calculateHealthScore(metrics) {
    const errors = Number(metrics.errors) || 0;
    const latency = Number(metrics.avg_latency_ms) || 0;
    const queue = Number(metrics.queue_depth) || 0;

    const errorPenalty = Math.min(errors * 4, 20);
    const latencyPenalty = Math.min(latency / 8, 20);
    const queuePenalty = Math.min(queue, 15);
    const rawScore = 100 - errorPenalty - latencyPenalty - queuePenalty;
    const score = Math.round(clampNumber(rawScore, 55, 100));

    let stateLabel = "stable";
    if (score >= 90) {
      stateLabel = "clear";
    } else if (score >= 75) {
      stateLabel = "watch";
    } else {
      stateLabel = "risk";
    }

    return { score, stateLabel };
  }

  function getDrawerRefs() {
    return {
      root: document.querySelector("[data-drawer]"),
      overlay: document.querySelector("[data-drawer-overlay]"),
      title: document.querySelector("[data-drawer-title]"),
      type: document.querySelector("[data-drawer-type]"),
      badge: document.querySelector("[data-drawer-badge]"),
      description: document.querySelector("[data-drawer-description]"),
      meta: document.querySelector("[data-drawer-meta]"),
      closeButton: document.querySelector('[data-action="close-drawer"]')
    };
  }

  function isDrawerOpen() {
    return drawerRefs?.root?.classList.contains("is-open");
  }

  function closeDrawer() {
    if (!drawerRefs?.root || !isDrawerOpen()) {
      return;
    }
    drawerRefs.root.classList.remove("is-open");
    drawerRefs.overlay?.classList.remove("is-open");
    drawerRefs.root.setAttribute("aria-hidden", "true");
    document.body.classList.remove("drawer-open");
  }

  function buildDetails(items) {
    return items.filter(([, value]) => value !== undefined && value !== null && value !== "");
  }

  function openDrawer({ type, title, badgeText, badgeClass, description, details }) {
    if (!drawerRefs?.root) {
      return;
    }
    drawerRefs.type.textContent = type || "Details";
    drawerRefs.title.textContent = title || "--";
    if (drawerRefs.badge) {
      drawerRefs.badge.textContent = badgeText || "--";
      drawerRefs.badge.className = `badge ${badgeClass || "paused"}`;
    }
    if (drawerRefs.description) {
      if (description) {
        drawerRefs.description.textContent = description;
        drawerRefs.description.hidden = false;
      } else {
        drawerRefs.description.textContent = "";
        drawerRefs.description.hidden = true;
      }
    }
    if (drawerRefs.meta) {
      drawerRefs.meta.innerHTML = "";
      if (Array.isArray(details) && details.length) {
        details.forEach(([label, value]) => {
          const row = document.createElement("div");
          row.className = "drawer-kv";
          const labelEl = document.createElement("div");
          labelEl.className = "drawer-label";
          labelEl.textContent = label;
          const valueEl = document.createElement("div");
          valueEl.className = "drawer-value";
          valueEl.textContent = formatValue(value);
          row.appendChild(labelEl);
          row.appendChild(valueEl);
          drawerRefs.meta.appendChild(row);
        });
      } else {
        drawerRefs.meta.innerHTML = '<div class="empty">No details available.</div>';
      }
    }

    drawerRefs.root.classList.add("is-open");
    drawerRefs.overlay?.classList.add("is-open");
    drawerRefs.root.setAttribute("aria-hidden", "false");
    document.body.classList.add("drawer-open");
  }

  function wireDrawer() {
    drawerRefs = getDrawerRefs();
    if (!drawerRefs?.root) {
      return;
    }
    drawerRefs.overlay?.addEventListener("click", closeDrawer);
    drawerRefs.closeButton?.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeDrawer();
      }
    });
  }

  function updateStatusDot(status) {
    const dot = document.querySelector("[data-status-dot]");
    if (!dot) {
      return;
    }
    dot.classList.remove("ok", "warn", "bad");
    const normalized = String(status || "").toLowerCase();
    const mapped = statusDotMap[normalized] || "bad";
    dot.classList.add(mapped);
  }

  function renderPills(name, items, options = {}) {
    const host = document.querySelector(`[data-list="${name}"]`);
    if (!host) {
      return;
    }
    host.innerHTML = "";
    if (!Array.isArray(items) || items.length === 0) {
      host.innerHTML = `<div class="empty">No ${name} data</div>`;
      return;
    }
    items.forEach((item) => {
      const label = typeof item === "string" ? item : item.title || item.label || item.name || "item";
      const pill = document.createElement(options.asButtons ? "button" : "div");
      pill.className = "pill";
      pill.textContent = label;
      if (options.asButtons) {
        pill.type = "button";
        pill.addEventListener("click", () => options.onClick?.(item));
      }
      host.appendChild(pill);
    });
  }

  function renderList(name, items, renderItem) {
    const host = document.querySelector(`[data-list="${name}"]`);
    if (!host) {
      return;
    }
    host.innerHTML = "";
    if (!Array.isArray(items) || items.length === 0) {
      host.innerHTML = `<div class="empty">No ${name} data</div>`;
      return;
    }
    items.forEach((item) => host.appendChild(renderItem(item)));
  }

  function createListItem({ title, meta, badgeText, badgeClass, rightText, onClick, ariaLabel }) {
    const row = document.createElement("div");
    row.className = "list-item";

    const left = document.createElement("div");
    left.className = "list-left";

    const titleEl = document.createElement("div");
    titleEl.className = "list-title";
    titleEl.textContent = title;
    left.appendChild(titleEl);

    if (meta) {
      const metaEl = document.createElement("div");
      metaEl.className = "list-meta";
      metaEl.textContent = meta;
      left.appendChild(metaEl);
    }

    row.appendChild(left);

    if (badgeText || rightText) {
      const right = document.createElement("div");
      right.className = "list-right";

      if (badgeText) {
        const badge = document.createElement("span");
        badge.className = `badge ${badgeClass || "paused"}`;
        badge.textContent = badgeText;
        right.appendChild(badge);
      }

      if (rightText) {
        const rightMeta = document.createElement("div");
        rightMeta.className = "list-right-meta";
        rightMeta.textContent = rightText;
        right.appendChild(rightMeta);
      }

      row.appendChild(right);
    }

    if (typeof onClick === "function") {
      row.classList.add("is-clickable");
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label", ariaLabel || `${title} details`);
      row.addEventListener("click", onClick);
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      });
    }

    return row;
  }

  function labelForStatus(status, map) {
    const key = String(status || "").toLowerCase();
    return map[key] || status || "unknown";
  }

  function renderModelItem(item) {
    const meta = [item.type, item.version, item.size].filter(Boolean).join(" · ");
    const label = labelForStatus(item.status, {
      ok: "ready",
      warn: "degraded",
      warming: "warming",
      queued: "queued",
      paused: "paused",
      linked: "linked"
    });
    return createListItem({
      title: item.name,
      meta,
      badgeText: label,
      badgeClass: item.status,
      onClick: () => openDrawer({
        type: "Model",
        title: item.name,
        badgeText: label,
        badgeClass: item.status,
        description: item.type,
        details: buildDetails([
          ["Version", item.version],
          ["Size", item.size]
        ])
      }),
      ariaLabel: `Open model ${item.name} details`
    });
  }

  function renderEndpointItem(item) {
    const meta = [item.method, item.latency && `latency ${item.latency}`].filter(Boolean).join(" · ");
    const label = labelForStatus(item.status, {
      ok: "live",
      warn: "degraded",
      warming: "warming",
      queued: "queued",
      paused: "paused"
    });
    return createListItem({
      title: item.path,
      meta,
      badgeText: label,
      badgeClass: item.status,
      onClick: () => openDrawer({
        type: "Endpoint",
        title: item.path,
        badgeText: label,
        badgeClass: item.status,
        description: item.method,
        details: buildDetails([
          ["Latency", item.latency],
          ["Route", item.path]
        ])
      }),
      ariaLabel: `Open endpoint ${item.path} details`
    });
  }

  function renderConnectionItem(item) {
    const latency = Number.isFinite(item.latency_ms) ? `${item.latency_ms}ms` : null;
    const meta = [item.type, latency && `latency ${latency}`].filter(Boolean).join(" · ");
    const status = String(item.status || "").toLowerCase();
    const label = labelForStatus(status, {
      linked: "linked",
      warming: "warming",
      queued: "queued",
      ok: "ok",
      warn: "warn"
    });
    return createListItem({
      title: item.name,
      meta,
      badgeText: label,
      badgeClass: status || "paused",
      onClick: () => openDrawer({
        type: "Connection",
        title: item.name,
        badgeText: label,
        badgeClass: status || "paused",
        description: item.type,
        details: buildDetails([
          ["Latency", latency],
          ["Type", item.type]
        ])
      }),
      ariaLabel: `Open connection ${item.name} details`
    });
  }

  function renderPipelineItem(item) {
    const meta = [item.mode, item.throughput].filter(Boolean).join(" · ");
    const state = String(item.state || "").toLowerCase();
    const label = labelForStatus(state, { running: "running", paused: "paused", queued: "queued" });
    return createListItem({
      title: item.name,
      meta,
      badgeText: label,
      badgeClass: state || "paused",
      onClick: () => openDrawer({
        type: "Pipeline",
        title: item.name,
        badgeText: label,
        badgeClass: state || "paused",
        description: item.mode,
        details: buildDetails([
          ["Throughput", item.throughput],
          ["Mode", item.mode]
        ])
      }),
      ariaLabel: `Open pipeline ${item.name} details`
    });
  }

  function renderRunItem(item) {
    const label = labelForStatus(item.status, { ok: "ok", warn: "warn", paused: "paused" });
    return createListItem({
      title: item.id,
      meta: item.summary,
      badgeText: label,
      badgeClass: item.status,
      rightText: item.duration,
      onClick: () => openDrawer({
        type: "Run",
        title: item.id,
        badgeText: label,
        badgeClass: item.status,
        description: item.summary,
        details: buildDetails([
          ["Duration", item.duration]
        ])
      }),
      ariaLabel: `Open run ${item.id} details`
    });
  }

  function renderActivityItem(item) {
    const label = labelForStatus(item.status, { ok: "ok", linked: "linked", paused: "paused", warn: "warn" });
    return createListItem({
      title: item.text,
      meta: item.time,
      badgeText: label,
      badgeClass: item.status,
      onClick: () => openDrawer({
        type: "Activity",
        title: item.text,
        badgeText: label,
        badgeClass: item.status,
        description: "Event log entry",
        details: buildDetails([
          ["Time", item.time]
        ])
      }),
      ariaLabel: "Open activity details"
    });
  }

  function renderActionItem(item) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "action-card";
    card.setAttribute("aria-label", `Open action ${item.name} details`);

    const top = document.createElement("div");
    top.className = "action-top";

    const titleWrap = document.createElement("div");
    const title = document.createElement("div");
    title.className = "action-title";
    title.textContent = item.name || "Action";
    const meta = document.createElement("div");
    meta.className = "action-meta";
    meta.textContent = item.tag || "control";
    titleWrap.appendChild(title);
    titleWrap.appendChild(meta);

    const statusLabel = labelForStatus(item.status, {
      ok: "ready",
      running: "running",
      queued: "queued",
      paused: "paused",
      warn: "watch"
    });
    const badge = document.createElement("span");
    badge.className = `badge ${item.status || "paused"}`;
    badge.textContent = statusLabel;

    top.appendChild(titleWrap);
    top.appendChild(badge);

    const desc = document.createElement("div");
    desc.className = "action-desc";
    desc.textContent = item.description || "No action details available.";

    const footer = document.createElement("div");
    footer.className = "action-footer";
    [item.eta && `eta ${item.eta}`, item.owner && `owner ${item.owner}`]
      .filter(Boolean)
      .forEach((text) => {
        const tag = document.createElement("span");
        tag.className = "action-tag";
        tag.textContent = text;
        footer.appendChild(tag);
      });

    card.appendChild(top);
    card.appendChild(desc);
    card.appendChild(footer);

    card.addEventListener("click", () => {
      openDrawer({
        type: "Action",
        title: item.name,
        badgeText: statusLabel,
        badgeClass: item.status,
        description: item.description,
        details: buildDetails([
          ["Tag", item.tag],
          ["Owner", item.owner],
          ["ETA", item.eta]
        ])
      });
      logActivity(`${item.name} checked`, item.status === "warn" ? "warn" : "ok");
    });

    return card;
  }

  function renderAlertItem(item) {
    const card = document.createElement("div");
    card.className = "alert-card";
    card.dataset.tone = item.tone || "warn";

    const title = document.createElement("div");
    title.className = "alert-title";
    title.textContent = item.title || "Alert";

    const summary = document.createElement("div");
    summary.className = "alert-meta";
    summary.textContent = item.summary || "No alert summary.";

    const meta = document.createElement("div");
    meta.className = "alert-meta";
    const eta = item.eta ? `eta ${item.eta}` : "eta --";
    const impact = item.impact ? `impact ${item.impact}` : "impact --";
    meta.textContent = `${eta} | ${impact}`;

    card.appendChild(title);
    card.appendChild(summary);
    card.appendChild(meta);
    return card;
  }

  function renderFocusItem(item) {
    const card = document.createElement("div");
    card.className = "focus-card";

    const top = document.createElement("div");
    top.className = "focus-top";

    const title = document.createElement("div");
    title.className = "action-title";
    title.textContent = item.title || "Focus item";

    const statusLabel = labelForStatus(item.status, {
      active: "active",
      planned: "planned",
      queued: "queued",
      paused: "paused"
    });
    const badge = document.createElement("span");
    badge.className = `badge ${item.status === "active" ? "ok" : "paused"}`;
    badge.textContent = statusLabel;

    top.appendChild(title);
    top.appendChild(badge);

    const meta = document.createElement("div");
    meta.className = "focus-meta";
    const owner = item.owner ? `owner ${item.owner}` : "owner --";
    const eta = item.eta ? `eta ${item.eta}` : "eta --";
    meta.textContent = `${owner} | ${eta}`;

    card.appendChild(top);
    card.appendChild(meta);
    return card;
  }

  function renderKeywords(items) {
    const host = document.querySelector('[data-list="keywords"]');
    if (!host) {
      return;
    }
    host.innerHTML = "";
    if (!Array.isArray(items) || items.length === 0) {
      host.innerHTML = '<div class="empty">No keywords yet. Run extraction.</div>';
      return;
    }
    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "keyword-card";

      const title = document.createElement("div");
      title.className = "keyword-title";
      title.textContent = item.term;

      const meta = document.createElement("div");
      meta.className = "keyword-meta";
      const type = document.createElement("span");
      type.textContent = item.type;
      const score = document.createElement("span");
      score.textContent = `${Math.round(item.score * 100)}%`;
      meta.appendChild(type);
      meta.appendChild(score);

      const bar = document.createElement("div");
      bar.className = "keyword-bar";
      const barFill = document.createElement("span");
      barFill.style.width = `${Math.round(item.score * 100)}%`;
      bar.appendChild(barFill);

      const sub = document.createElement("div");
      sub.className = "keyword-sub";
      sub.textContent = `mentions: ${item.count}`;

      card.appendChild(title);
      card.appendChild(meta);
      card.appendChild(bar);
      card.appendChild(sub);

      host.appendChild(card);
    });
  }

  function extractKeywords(text, options) {
    const rawTokens = text.match(/[A-Za-z][A-Za-z0-9-]*/g) || [];
    const entityTokens = text.match(/\b[A-Z][A-Za-z0-9-]{1,}\b/g) || [];
    const entitySet = new Set(entityTokens.map((token) => token.toLowerCase()));
    const displayMap = new Map();
    const counts = new Map();

    rawTokens.forEach((token) => {
      const lower = token.toLowerCase();
      if (STOPWORDS.has(lower)) {
        return;
      }
      if (lower.length < 2 || /^\d+$/.test(lower)) {
        return;
      }
      if (!displayMap.has(lower)) {
        displayMap.set(lower, token);
      }
      counts.set(lower, (counts.get(lower) || 0) + 1);
    });

    if (counts.size === 0) {
      return [];
    }

    const maxCount = Math.max(...counts.values());
    const entries = Array.from(counts.entries()).sort((a, b) => {
      if (b[1] !== a[1]) {
        return b[1] - a[1];
      }
      return a[0].localeCompare(b[0]);
    });

    const results = [];
    for (const [token, count] of entries) {
      const score = count / maxCount;
      if (score < options.minConfidence) {
        continue;
      }
      const isEntity = entitySet.has(token);
      if (isEntity && !options.includeEntities) {
        continue;
      }
      if (!isEntity && !options.includeConcepts) {
        continue;
      }
      results.push({
        term: displayMap.get(token) || token,
        type: isEntity ? "Entity" : "Concept",
        score,
        count
      });
      if (results.length >= options.topK) {
        break;
      }
    }

    return results;
  }

  function clampNumber(value, min, max) {
    if (!Number.isFinite(value)) {
      return min;
    }
    return Math.min(Math.max(value, min), max);
  }

  function getOptions() {
    const apiBaseField = document.querySelector('[data-field="api_base"]');
    const topKField = document.querySelector('[data-field="top_k"]');
    const minConfidenceField = document.querySelector('[data-field="min_confidence"]');
    const languageField = document.querySelector('[data-field="language"]');
    const includeEntitiesField = document.querySelector('[data-field="include_entities"]');
    const includeConceptsField = document.querySelector('[data-field="include_concepts"]');

    const rawTopK = parseInt(topKField?.value, 10);
    const rawMinConfidence = parseFloat(minConfidenceField?.value);
    const topK = clampNumber(Number.isFinite(rawTopK) ? rawTopK : 10, 1, 50);
    const minConfidence = clampNumber(Number.isFinite(rawMinConfidence) ? rawMinConfidence : 0.3, 0, 1);

    if (topKField) {
      topKField.value = String(topK);
    }
    if (minConfidenceField) {
      minConfidenceField.value = String(minConfidence);
    }

    return {
      apiBase: apiBaseField?.value?.trim() || state.data.system.api_url,
      topK,
      minConfidence,
      language: languageField?.value?.trim() || "en",
      includeEntities: includeEntitiesField?.checked ?? true,
      includeConcepts: includeConceptsField?.checked ?? true
    };
  }

  function updatePulseMetrics() {
    const metrics = state.data.metrics || {};

    const queueDepth = Number(metrics.queue_depth);
    if (Number.isFinite(queueDepth)) {
      metrics.queue_depth = Math.max(0, Math.round(queueDepth + Math.random() * 4 - 2));
    }

    const avgLatency = Number(metrics.avg_latency_ms);
    if (Number.isFinite(avgLatency)) {
      metrics.avg_latency_ms = Math.max(40, Math.round(avgLatency + Math.random() * 12 - 6));
    }

    const requestsToday = Number(metrics.requests_today);
    if (Number.isFinite(requestsToday)) {
      metrics.requests_today = requestsToday + Math.floor(Math.random() * 3);
    }

    setStat("mode", state.data.system.mode);
    setStat("avg_latency_ms", formatMs(metrics.avg_latency_ms));
    setStat("queue_depth", metrics.queue_depth);
    setStat("requests_today", metrics.requests_today);
    setStat("active_connectors", metrics.active_connectors);
    setStat("pipelines_running", metrics.pipelines_running);
    setStat("local_time", formatTimeStamp(new Date()));

    const health = calculateHealthScore(metrics);
    setStat("health_score", health.score);
    setStat("health_state", health.stateLabel);
    setMeter("health_score", health.score);
  }

  function updateRequestRate() {
    const rateValue = state.data.metrics.request_rate;
    const base = typeof rateValue === "number" ? rateValue : parseInt(String(rateValue), 10);
    if (Number.isFinite(base)) {
      const next = Math.max(1, base + Math.floor(Math.random() * 5) - 2);
      state.data.metrics.request_rate = typeof rateValue === "number" ? next : `${next}/min`;
    }
    setStat("request_rate", state.data.metrics.request_rate);
    setStat("last_refresh", formatTimeStamp(new Date()));
    updatePulseMetrics();
  }

  function updateCommandStatus(status, error) {
    setStat("command_status", status);
    setCommandError(error);
  }

  function setBusy(isBusy) {
    ["run-extract", "run-batch"].forEach((action) => {
      const button = document.querySelector(`[data-action="${action}"]`);
      if (button) {
        button.disabled = isBusy;
      }
    });
  }

  function logActivity(text, status = "ok") {
    const entry = { time: "just now", text, status };
    const current = Array.isArray(state.data.activity) ? state.data.activity : [];
    state.data.activity = [entry, ...current].slice(0, 6);
    renderList("activity", state.data.activity, renderActivityItem);
  }

  function handleSampleClick(sample) {
    const input = document.querySelector('[data-field="input"]');
    if (input) {
      input.value = sample.text || "";
      updateCommandStatus("Sample loaded");
    }
  }

  function handleRun(mode) {
    const input = document.querySelector('[data-field="input"]');
    const samples = Array.isArray(state.data.samples) ? state.data.samples : [];
    let text = input?.value?.trim() || "";
    let sampleCount = 1;

    if (mode === "batch") {
      if (!text && samples.length) {
        text = samples.map((sample) => sample.text).join(" ");
        sampleCount = samples.length;
      }
    }

    if (!text) {
      updateCommandStatus("Waiting", "Add text to analyze.");
      return;
    }

    updateCommandStatus(mode === "batch" ? "Running batch" : "Running extraction");
    setBusy(true);
    const options = getOptions();
    const start = performance.now();
    const delay = 420 + Math.random() * 620;

    window.setTimeout(() => {
      const keywords = extractKeywords(text, options);
      renderKeywords(keywords);

      const elapsed = Math.round(performance.now() - start);
      const processingTime = elapsed < 1000 ? `${elapsed}ms` : `${(elapsed / 1000).toFixed(2)}s`;
      const increment = mode === "batch" ? Math.max(1, Math.ceil(sampleCount / 2)) : 1;
      state.totalExtractions += increment;

      setStat("total_extractions", state.totalExtractions);
      setStat("last_run", formatTimeStamp(new Date()));
      setStat("last_keyword_count", keywords.length);
      setStat("last_processing_time", processingTime);
      updateRequestRate();

      updateCommandStatus(
        mode === "batch" ? `Batch complete (${sampleCount} samples)` : "Complete"
      );
      logActivity(
        mode === "batch"
          ? `Batch extraction complete (${sampleCount} samples)`
          : "Extraction complete",
        "ok"
      );
      setBusy(false);
    }, delay);
  }

  function clearResults() {
    const input = document.querySelector('[data-field="input"]');
    if (input) {
      input.value = "";
    }
    renderKeywords([]);
    setStat("last_run", "--");
    setStat("last_keyword_count", "--");
    setStat("last_processing_time", "--");
    updateCommandStatus("Cleared");
  }

  function openDocs() {
    window.open("README.md", "_blank", "noopener");
  }

  function focusCommand() {
    const section = document.querySelector('[data-component="command"]');
    if (section) {
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    const input = document.querySelector('[data-field="input"]');
    if (input) {
      input.focus({ preventScroll: true });
    }
  }

  function renderDashboard(data) {
    updateStatusDot(data.system.status);
    setStat("status", data.system.status);
    setStat("uptime", data.system.uptime);
    setStat("version", data.system.version);
    setStat("api_url", data.system.api_url);

    const modelsLoaded = Number(data.metrics.models_loaded) || data.models.length || 0;
    state.totalExtractions = Number(data.metrics.total_extractions) || state.totalExtractions || 0;

    setStat("models_loaded", modelsLoaded);
    setStat("total_extractions", state.totalExtractions);
    setStat("avg_processing_time", data.metrics.avg_processing_time);
    setStat("errors", data.metrics.errors);
    setStat("cache_size", data.metrics.cache_size);
    setStat("request_rate", data.metrics.request_rate);
    setStat("last_refresh", formatTimeStamp(new Date()));
    updatePulseMetrics();

    setStat("command_status", "Idle");
    setCommandError("");
    setStat("last_run", "--");
    setStat("last_keyword_count", "--");
    setStat("last_processing_time", "--");

    renderPills("capabilities", data.capabilities);
    renderPills("languages", data.languages);
    renderList("connections", data.connections, renderConnectionItem);
    renderList("pipelines", data.pipelines, renderPipelineItem);
    renderList("models", data.models, renderModelItem);
    renderList("endpoints", data.endpoints, renderEndpointItem);
    renderList("runs", data.runs, renderRunItem);
    renderList("activity", data.activity, renderActivityItem);
    renderPills("samples", data.samples, { asButtons: true, onClick: handleSampleClick });
    renderList("flight_actions", data.flight_actions, renderActionItem);
    renderList("alerts", data.alerts, renderAlertItem);
    renderList("focus", data.focus, renderFocusItem);

    const apiBaseField = document.querySelector('[data-field="api_base"]');
    if (apiBaseField && !apiBaseField.value) {
      apiBaseField.value = data.system.api_url;
    }
  }

  function wireActions() {
    const runExtractButton = document.querySelector('[data-action="run-extract"]');
    const runBatchButton = document.querySelector('[data-action="run-batch"]');
    const clearButton = document.querySelector('[data-action="clear-results"]');
    const openDocsButton = document.querySelector('[data-action="open-docs"]');
    const focusCommandButton = document.querySelector('[data-action="focus-command"]');

    runExtractButton?.addEventListener("click", () => handleRun("single"));
    runBatchButton?.addEventListener("click", () => handleRun("batch"));
    clearButton?.addEventListener("click", clearResults);
    openDocsButton?.addEventListener("click", openDocs);
    focusCommandButton?.addEventListener("click", focusCommand);
  }

  // ============================================
  // SEO INTELLIGENCE MODULE
  // ============================================

  const ML_API_BASE = "http://localhost:8003/api/v1";

  // Sample data for SEO features
  const seoSampleData = {
    intentKeywords: [
      "best laptop for programming 2024",
      "how to learn python",
      "amazon prime login",
      "buy running shoes online",
      "what is machine learning",
      "nike air max 90 price",
      "stackoverflow",
      "how to make coffee at home"
    ],
    clusterKeywords: [
      "best laptop 2024", "laptop reviews", "top laptops", "laptop comparison",
      "gaming laptop", "laptop for students", "cheap laptops", "laptop deals",
      "macbook pro", "dell xps", "hp laptop", "lenovo thinkpad",
      "laptop battery life", "laptop ssd", "laptop ram upgrade",
      "best budget laptop", "laptop for video editing", "portable laptop",
      "2 in 1 laptop", "touchscreen laptop"
    ]
  };

  // Mock intent classification (will use real API when available)
  function mockClassifyIntent(keywords) {
    const intents = ["commercial", "informational", "navigational", "transactional"];
    const patterns = {
      commercial: ["best", "top", "review", "compare", "vs"],
      informational: ["how", "what", "why", "guide", "tutorial", "learn"],
      navigational: ["login", "sign in", "official", "website"],
      transactional: ["buy", "price", "discount", "deal", "order", "shop"]
    };

    return keywords.map(kw => {
      const lower = kw.toLowerCase();
      let intent = "informational";
      let confidence = 0.75;

      for (const [type, words] of Object.entries(patterns)) {
        if (words.some(w => lower.includes(w))) {
          intent = type;
          confidence = 0.85 + Math.random() * 0.12;
          break;
        }
      }

      return {
        keyword: kw,
        intent: intent,
        confidence: Math.min(confidence, 0.98)
      };
    });
  }

  // Mock keyword clustering
  function mockClusterKeywords(keywords, numClusters) {
    const clusters = [];
    const perCluster = Math.ceil(keywords.length / numClusters);

    for (let i = 0; i < numClusters && i * perCluster < keywords.length; i++) {
      const clusterKeywords = keywords.slice(i * perCluster, (i + 1) * perCluster);
      if (clusterKeywords.length > 0) {
        clusters.push({
          id: i + 1,
          name: clusterKeywords[0],
          keywords: clusterKeywords,
          centroid: clusterKeywords[0],
          coherence: 0.7 + Math.random() * 0.25
        });
      }
    }

    return { clusters, outliers: [] };
  }

  // Mock SERP analysis
  function mockSerpAnalysis(query) {
    return {
      query: query,
      features: {
        featured_snippet: Math.random() > 0.5,
        knowledge_panel: Math.random() > 0.6,
        people_also_ask: true,
        local_pack: Math.random() > 0.7,
        image_pack: Math.random() > 0.4,
        video_carousel: Math.random() > 0.5,
        shopping_results: Math.random() > 0.6,
        related_searches: true
      },
      results: [
        { position: 1, domain: "example.com", title: `Best Guide to ${query}`, da: 85 },
        { position: 2, domain: "guide.org", title: `Complete ${query} Tutorial`, da: 78 },
        { position: 3, domain: "howto.net", title: `${query} - Everything You Need`, da: 72 }
      ]
    };
  }

  // Render intent classification results
  function renderIntentResults(results) {
    const container = document.querySelector('[data-list="intent-results"]');
    if (!container) return;

    if (!results || results.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state-text">Click "Classify" to analyze keywords</div></div>';
      return;
    }

    container.innerHTML = results.map(r => `
      <div class="intent-row">
        <div class="intent-keyword">${r.keyword}</div>
        <span class="intent-badge ${r.intent}">${r.intent}</span>
        <div>
          <div class="confidence-bar">
            <div class="confidence-bar-fill" style="width: ${r.confidence * 100}%"></div>
          </div>
          <div class="confidence-text">${(r.confidence * 100).toFixed(0)}%</div>
        </div>
      </div>
    `).join('');

    // Render distribution chart
    renderIntentDistribution(results);
  }

  function renderIntentDistribution(results) {
    const container = document.querySelector('[data-chart="intent-distribution"]');
    if (!container) return;

    const counts = { commercial: 0, informational: 0, navigational: 0, transactional: 0 };
    results.forEach(r => counts[r.intent]++);

    const total = results.length;
    const maxCount = Math.max(...Object.values(counts));

    container.innerHTML = Object.entries(counts).map(([intent, count]) => {
      const pct = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
      const barHeight = maxCount > 0 ? (count / maxCount) * 100 : 0;
      return `
        <div class="distribution-item">
          <div class="distribution-bar">
            <div class="distribution-bar-fill" style="height: ${barHeight}%"></div>
          </div>
          <div class="distribution-value">${pct}%</div>
          <div class="distribution-label">${intent.slice(0, 4)}</div>
        </div>
      `;
    }).join('');
  }

  // Render cluster results
  function renderClusterResults(data) {
    const container = document.querySelector('[data-list="cluster-results"]');
    if (!container) return;

    if (!data || !data.clusters || data.clusters.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="empty-state-text">Click "Cluster" to group keywords</div></div>';
      return;
    }

    container.innerHTML = data.clusters.map(cluster => `
      <div class="cluster-card">
        <div class="cluster-header" onclick="this.parentElement.classList.toggle('expanded')">
          <span class="cluster-name">${cluster.name}</span>
          <span class="cluster-count">${cluster.keywords.length} keywords</span>
        </div>
        <div class="cluster-keywords">
          ${cluster.keywords.map(kw => `
            <span class="cluster-keyword ${kw === cluster.centroid ? 'cluster-centroid' : ''}">${kw}</span>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  // Render SERP results
  function renderSerpResults(data) {
    const featuresContainer = document.querySelector('[data-list="serp-features"]');
    const resultsContainer = document.querySelector('[data-list="serp-results"]');

    if (featuresContainer && data.features) {
      const featureIcons = {
        featured_snippet: "📋",
        knowledge_panel: "📊",
        people_also_ask: "❓",
        local_pack: "📍",
        image_pack: "🖼️",
        video_carousel: "🎬",
        shopping_results: "🛒",
        related_searches: "🔗"
      };

      featuresContainer.innerHTML = Object.entries(data.features).map(([key, active]) => `
        <div class="serp-feature ${active ? 'active' : ''}">
          <span class="serp-feature-icon">${featureIcons[key] || '•'}</span>
          <span>${key.replace(/_/g, ' ')}</span>
        </div>
      `).join('');
    }

    if (resultsContainer && data.results) {
      resultsContainer.innerHTML = data.results.map(r => `
        <div class="serp-result">
          <div class="serp-position">#${r.position}</div>
          <div>
            <div class="serp-url">${r.domain}</div>
            <div class="serp-title">${r.title}</div>
          </div>
          <div class="serp-meta">
            <span class="serp-meta-item">DA: ${r.da}</span>
          </div>
        </div>
      `).join('');
    }
  }

  // Action handlers for SEO tools
  function handleIntentClassify() {
    const textarea = document.getElementById('intent-keywords');
    if (!textarea) return;

    const keywords = textarea.value.split('\n').map(k => k.trim()).filter(k => k);
    if (keywords.length === 0) {
      alert('Please enter at least one keyword');
      return;
    }

    // Use mock for now (replace with API call when available)
    const results = mockClassifyIntent(keywords);
    renderIntentResults(results);
  }

  function handleKeywordCluster() {
    const textarea = document.getElementById('cluster-keywords');
    const numClustersInput = document.querySelector('[data-field="num-clusters"]');
    if (!textarea) return;

    const keywords = textarea.value.split('\n').map(k => k.trim()).filter(k => k);
    const numClusters = parseInt(numClustersInput?.value || 10);

    if (keywords.length < 5) {
      alert('Please enter at least 5 keywords');
      return;
    }

    const results = mockClusterKeywords(keywords, numClusters);
    renderClusterResults(results);
  }

  function handleSerpAnalyze() {
    const input = document.getElementById('serp-query');
    if (!input || !input.value.trim()) {
      alert('Please enter a search query');
      return;
    }

    const results = mockSerpAnalysis(input.value.trim());
    renderSerpResults(results);
  }

  function loadIntentSamples() {
    const textarea = document.getElementById('intent-keywords');
    if (textarea) {
      textarea.value = seoSampleData.intentKeywords.join('\n');
    }
  }

  function loadClusterSamples() {
    const textarea = document.getElementById('cluster-keywords');
    if (textarea) {
      textarea.value = seoSampleData.clusterKeywords.join('\n');
    }
  }

  function loadSerpSample() {
    const input = document.getElementById('serp-query');
    if (input) {
      input.value = "best laptop for programming";
    }
  }

  function clearIntent() {
    const textarea = document.getElementById('intent-keywords');
    const results = document.querySelector('[data-list="intent-results"]');
    const dist = document.querySelector('[data-chart="intent-distribution"]');
    if (textarea) textarea.value = '';
    if (results) results.innerHTML = '';
    if (dist) dist.innerHTML = '';
  }

  function clearClusters() {
    const textarea = document.getElementById('cluster-keywords');
    const results = document.querySelector('[data-list="cluster-results"]');
    if (textarea) textarea.value = '';
    if (results) results.innerHTML = '';
  }

  function wireSeoActions() {
    document.querySelector('[data-action="run-intent"]')?.addEventListener('click', handleIntentClassify);
    document.querySelector('[data-action="load-intent-samples"]')?.addEventListener('click', loadIntentSamples);
    document.querySelector('[data-action="clear-intent"]')?.addEventListener('click', clearIntent);

    document.querySelector('[data-action="run-cluster"]')?.addEventListener('click', handleKeywordCluster);
    document.querySelector('[data-action="clear-clusters"]')?.addEventListener('click', clearClusters);

    document.querySelector('[data-action="run-serp"]')?.addEventListener('click', handleSerpAnalyze);
    document.querySelector('[data-action="load-serp-sample"]')?.addEventListener('click', loadSerpSample);

    // Add sample data loader for clusters via double-click on textarea
    document.getElementById('cluster-keywords')?.addEventListener('dblclick', loadClusterSamples);
  }

  // ============================================
  // END SEO INTELLIGENCE MODULE
  // ============================================

  async function init() {
    const data = await loadData();
    state.data = data;
    renderDashboard(data);
    wireDrawer();
    wireActions();
    wireSeoActions(); // Add SEO actions
  }

  init();
})();
