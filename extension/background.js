const SERVICE_URL = "http://127.0.0.1:8766/process";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "YT_ANKI_PROCESS") {
    return false;
  }

  fetch(SERVICE_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      video_url: message.videoUrl,
      language: message.language || "ru"
    })
  })
    .then(async (response) => {
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || `Service returned ${response.status}`);
      }
      sendResponse({ ok: true, payload });
    })
    .catch((error) => {
      sendResponse({ ok: false, error: error.message });
    });

  return true;
});
