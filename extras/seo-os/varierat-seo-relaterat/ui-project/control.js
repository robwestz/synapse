(() => {
  const fallbackConfig = {
    status: { refresh_interval_ms: 8000, timeout_ms: 1500 },
    tasks: [],
    surfaces: [],
    shortcuts: [],
    notes: {}
  };

  const statusRefs = new Map();
  const latencyHistory = new Map();
  const summaryRefs = {
    dot: document.querySelector('[data-status-summary] .dot'),
    label: document.querySelector('[data-status-summary] .status-label'),
    meta: document.querySelector('[data-status-summary] .status-meta')
  };
  const feedbackNode = document.querySelector('[data-control-feedback]');
  const launchpadNote = document.querySelector('[data-launchpad-note]');

  let config = fallbackConfig;
  let controlApi = { available: false, baseUrl: "", commandPath: "/api/command", statusPath: "/api/status" };
  let statusTimer = null;

  function buildTaskUrl(label) {
    const payload = encodeURIComponent(JSON.stringify([label]));
    return `vscode://command/workbench.action.tasks.runTask?${payload}`;
  }

  function variantClass(variant) {
    if (variant === "primary") return "primary";
    if (variant === "ghost") return "ghost";
    return "";
  }

  function formatTime(date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function setSummaryStatus(onlineCount, total) {
    if (!summaryRefs.dot || !summaryRefs.label || !summaryRefs.meta) {
      return;
    }
    summaryRefs.dot.classList.remove("ok", "warn", "bad");
    if (total === 0) {
      summaryRefs.dot.classList.add("warn");
      summaryRefs.label.textContent = "no targets";
    } else if (onlineCount === total) {
      summaryRefs.dot.classList.add("ok");
      summaryRefs.label.textContent = `${onlineCount}/${total} online`;
    } else if (onlineCount === 0) {
      summaryRefs.dot.classList.add("bad");
      summaryRefs.label.textContent = "offline";
    } else {
      summaryRefs.dot.classList.add("warn");
      summaryRefs.label.textContent = `${onlineCount}/${total} online`;
    }
    summaryRefs.meta.textContent = `last check ${formatTime(new Date())}`;
  }

  function createTaskCard(task) {
    const card = document.createElement("div");
    card.className = "control-card";

    const title = document.createElement("div");
    title.className = "control-title";
    title.textContent = task.title;

    const meta = document.createElement("div");
    meta.className = "control-meta";
    meta.textContent = task.description || "";

    const actions = document.createElement("div");
    actions.className = "control-actions";
    if (controlApi.available && task.command) {
      const button = document.createElement("button");
      button.className = `chip ${variantClass(task.variant)}`.trim();
      button.type = "button";
      button.dataset.command = task.command;
      button.textContent = "Run command";
      actions.appendChild(button);
    } else if (task.vscode_task) {
      const link = document.createElement("a");
      link.className = `chip ${variantClass(task.variant)}`.trim();
      link.href = buildTaskUrl(task.vscode_task);
      link.textContent = "Run task";
      actions.appendChild(link);
    } else {
      const button = document.createElement("button");
      button.className = "chip ghost";
      button.type = "button";
      button.disabled = true;
      button.textContent = "Unavailable";
      actions.appendChild(button);
    }

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(actions);
    return card;
  }

  function createShortcutChip(shortcut) {
    const link = document.createElement("a");
    link.className = `chip ${variantClass(shortcut.variant)}`.trim();
    link.href = shortcut.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = shortcut.title;
    if (shortcut.description) {
      link.title = shortcut.description;
    }
    return link;
  }

  function createSurfaceCard(surface) {
    const link = document.createElement("a");
    link.className = "control-link";
    link.href = surface.url;
    link.target = "_blank";
    link.rel = "noopener";

    const title = document.createElement("div");
    title.className = "control-title";
    title.textContent = surface.title;

    const meta = document.createElement("div");
    meta.className = "control-meta";
    meta.textContent = surface.description || "";

    const tag = document.createElement("div");
    tag.className = "control-tag";
    tag.textContent = surface.tag || surface.url;

    const status = document.createElement("div");
    status.className = "status-pill";
    const dot = document.createElement("span");
    dot.className = "dot warn";
    const label = document.createElement("span");
    label.className = "status-label";
    label.textContent = "checking";
    status.appendChild(dot);
    status.appendChild(label);

    const statusMeta = document.createElement("div");
    statusMeta.className = "status-meta";
    statusMeta.textContent = "last check --";

    link.appendChild(title);
    link.appendChild(meta);
    link.appendChild(tag);
    link.appendChild(status);
    link.appendChild(statusMeta);

    statusRefs.set(surface.id, { dot, label, meta: statusMeta, card: link });
    return link;
  }

  function renderTasks(tasks) {
    const host = document.querySelector('[data-grid="tasks"]');
    if (!host) return;
    host.innerHTML = "";
    tasks.forEach((task) => host.appendChild(createTaskCard(task)));
  }

  function renderShortcuts(shortcuts) {
    const host = document.querySelector('[data-grid="shortcuts"]');
    if (!host) return;
    host.innerHTML = "";
    shortcuts.forEach((shortcut) => host.appendChild(createShortcutChip(shortcut)));
  }

  function renderSurfaces(surfaces) {
    const host = document.querySelector('[data-grid="surfaces"]');
    if (!host) return;
    host.innerHTML = "";
    statusRefs.clear();
    surfaces.forEach((surface) => host.appendChild(createSurfaceCard(surface)));
  }

  function renderNotes(notes) {
    ["tasks", "surfaces", "reminder"].forEach((key) => {
      const node = document.querySelector(`[data-note="${key}"]`);
      if (node) {
        node.textContent = notes?.[key] || "";
      }
    });
  }

  function validateConfig(raw) {
    if (!raw || typeof raw !== "object") return false;
    if (!Array.isArray(raw.tasks) || !Array.isArray(raw.surfaces)) return false;
    if (!raw.status || typeof raw.status !== "object") return false;
    return true;
  }

  async function loadConfig() {
    try {
      const response = await fetch("control.config.json", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Config fetch failed");
      }
      const data = await response.json();
      if (!validateConfig(data)) {
        throw new Error("Config invalid");
      }
      return data;
    } catch (error) {
      return fallbackConfig;
    }
  }

  async function ping(url, timeoutMs) {
    if (!url) return { ok: false, status: 0, error: "no url" };
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        cache: "no-store",
        mode: "cors",
        signal: controller.signal
      });
      window.clearTimeout(timeout);
      return { ok: response.ok, status: response.status, error: "" };
    } catch (error) {
      const message = error?.name === "AbortError" ? "timeout" : "network error";
      return { ok: false, status: 0, error: message };
    }
  }

  async function checkSurface(surface) {
    const refs = statusRefs.get(surface.id);
    if (!refs) return false;
    const start = performance.now();
    const result = await ping(surface.health || surface.url, config.status.timeout_ms);
    const latency = Math.round(performance.now() - start);
    refs.dot.classList.remove("ok", "warn", "bad");
    refs.dot.classList.add(result.ok ? "ok" : "bad");
    refs.label.textContent = result.ok ? "online" : "offline";
    if (result.ok) {
      const history = latencyHistory.get(surface.id) || [];
      history.push(latency);
      if (history.length > 5) {
        history.shift();
      }
      latencyHistory.set(surface.id, history);
      const avg = Math.round(history.reduce((sum, value) => sum + value, 0) / history.length);
      refs.meta.textContent = `last check ${formatTime(new Date())} - ${latency}ms (avg ${avg}ms)`;
      if (refs.card) {
        refs.card.title = `Latency history: ${history.map((value) => `${value}ms`).join(", ")}`;
      }
    } else if (result.status) {
      refs.meta.textContent = `last check ${formatTime(new Date())} - HTTP ${result.status}`;
      if (refs.card) {
        refs.card.title = `Last error: HTTP ${result.status}`;
      }
    } else {
      const message = result.error || "offline";
      refs.meta.textContent = `last check ${formatTime(new Date())} - ${message}`;
      if (refs.card) {
        refs.card.title = `Last error: ${message}`;
      }
    }
    return result.ok;
  }

  async function refreshStatus() {
    if (!Array.isArray(config.surfaces)) return;
    const results = await Promise.all(
      config.surfaces.map((surface) => checkSurface(surface))
    );
    const onlineCount = results.filter(Boolean).length;
    setSummaryStatus(onlineCount, results.length);
  }

  function openAllSurfaces() {
    const targets = config.surfaces.filter((surface) => surface.open_on_launch);
    if (targets.length === 0) {
      return;
    }
    targets.forEach((surface) => {
      window.open(surface.url, "_blank", "noopener");
    });
  }

  function buildApiUrl(path) {
    const base = controlApi.baseUrl || "";
    if (!base) {
      return path;
    }
    return new URL(path, base).toString();
  }

  function setFeedback(message, tone = "info") {
    if (!feedbackNode) {
      return;
    }
    feedbackNode.textContent = message;
    feedbackNode.dataset.tone = tone;
  }

  async function sendCommand(command) {
    if (!controlApi.available) {
      setFeedback("Local control server not detected.", "warn");
      return;
    }
    try {
      const response = await fetch(buildApiUrl(controlApi.commandPath), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data?.ok === false) {
        setFeedback(data?.message || "Command failed.", "warn");
        return;
      }
      setFeedback(data?.message || "Command sent.", "ok");
      await refreshStatus();
    } catch (error) {
      setFeedback("Command failed to send.", "warn");
    }
  }

  function wireActions() {
    document.querySelector('[data-grid="tasks"]')?.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) {
        return;
      }
      const button = target.closest("[data-command]");
      if (button instanceof HTMLElement) {
        const command = button.dataset.command;
        if (command) {
          sendCommand(command);
        }
      }
    });
    document.querySelector('[data-action="refresh-status"]')?.addEventListener("click", () => {
      refreshStatus();
    });
    document.querySelector('[data-action="open-all"]')?.addEventListener("click", () => {
      openAllSurfaces();
    });
  }

  function startAutoRefresh() {
    if (statusTimer) {
      window.clearInterval(statusTimer);
    }
    const interval = config.status.refresh_interval_ms || 8000;
    statusTimer = window.setInterval(() => refreshStatus(), interval);
  }

  async function detectLocalControl() {
    const baseUrl = config.control_api?.base_url || "";
    controlApi = {
      available: false,
      baseUrl,
      statusPath: config.control_api?.status_path || "/api/status",
      commandPath: config.control_api?.command_path || "/api/command"
    };
    try {
      const response = await fetch(buildApiUrl(controlApi.statusPath), { cache: "no-store" });
      if (!response.ok) {
        throw new Error("status offline");
      }
      controlApi.available = true;
      setFeedback("Local control server detected.", "ok");
    } catch (error) {
      controlApi.available = false;
      setFeedback("Local control server offline. Using VS Code tasks.", "warn");
    }
    if (launchpadNote) {
      launchpadNote.textContent = controlApi.available ? "Local control server" : "VS Code tasks";
    }
  }

  async function init() {
    config = await loadConfig();
    await detectLocalControl();
    renderTasks(config.tasks || []);
    renderShortcuts(config.shortcuts || []);
    renderSurfaces(config.surfaces || []);
    renderNotes(config.notes || {});
    wireActions();
    await refreshStatus();
    startAutoRefresh();
  }

  init();
})();
