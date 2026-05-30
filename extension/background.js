const DEFAULT_CONFIG = {
  serviceUrl: "http://127.0.0.1:8766",
  language: "ru"
};

async function getConfig() {
  const stored = await chrome.storage.sync.get(DEFAULT_CONFIG);
  return {
    serviceUrl: normalizeServiceUrl(stored.serviceUrl || DEFAULT_CONFIG.serviceUrl),
    language: stored.language || DEFAULT_CONFIG.language
  };
}

async function setConfig(config) {
  const next = {
    serviceUrl: normalizeServiceUrl(config.serviceUrl || DEFAULT_CONFIG.serviceUrl),
    language: config.language || DEFAULT_CONFIG.language
  };
  await chrome.storage.sync.set(next);
  return next;
}

function normalizeServiceUrl(value) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error("Service URL must be a valid URL.");
  }
  const allowedHosts = new Set(["127.0.0.1", "localhost", "[::1]"]);
  if (parsed.protocol !== "http:" || !allowedHosts.has(parsed.hostname)) {
    throw new Error("Service URL must be local, for example http://127.0.0.1:8766.");
  }
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  parsed.search = "";
  parsed.hash = "";
  return parsed.toString().replace(/\/+$/, "");
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Service returned ${response.status}`);
  }
  return payload;
}

async function getJson(url) {
  const response = await fetch(url);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Service returned ${response.status}`);
  }
  return payload;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message?.type) {
    return false;
  }

  (async () => {
    if (message.type === "YT_ANKI_GET_CONFIG") {
      sendResponse({ ok: true, payload: await getConfig() });
      return;
    }

    if (message.type === "YT_ANKI_SET_CONFIG") {
      sendResponse({ ok: true, payload: await setConfig(message.config || {}) });
      return;
    }

    const config = await getConfig();

    if (message.type === "YT_ANKI_HEALTH") {
      sendResponse({ ok: true, payload: await getJson(`${config.serviceUrl}/health`) });
      return;
    }

    if (message.type === "YT_ANKI_JOB_STATUS") {
      sendResponse({
        ok: true,
        payload: await getJson(`${config.serviceUrl}/jobs/${message.jobId}`)
      });
      return;
    }

    if (message.type === "YT_ANKI_PROCESS") {
      const payload = await postJson(`${config.serviceUrl}/process`, {
        video_url: message.videoUrl,
        language: message.language || config.language,
        repair: Boolean(message.repair)
      });
      sendResponse({ ok: true, payload });
      return;
    }

    sendResponse({ ok: false, error: `Unknown message type: ${message.type}` });
  })()
    .catch((error) => {
      sendResponse({ ok: false, error: error.message || String(error) });
    })
    .finally(() => undefined);

  return true;
});
