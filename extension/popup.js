function sendMessage(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, (response) => {
      resolve(response || { ok: false, error: chrome.runtime.lastError?.message || "No response" });
    });
  });
}

function setStatus(text, isError = false) {
  const status = document.getElementById("status");
  status.textContent = text;
  status.style.color = isError ? "#a50e0e" : "#137333";
}

async function loadConfig() {
  const response = await sendMessage({ type: "YT_ANKI_GET_CONFIG" });
  if (!response.ok) {
    setStatus(response.error || "Could not load settings", true);
    return;
  }
  document.getElementById("service-url").value = response.payload.serviceUrl;
  document.getElementById("language").value = response.payload.language;
  setStatus("Ready");
}

async function saveConfig() {
  const config = {
    serviceUrl: document.getElementById("service-url").value.trim(),
    language: document.getElementById("language").value
  };
  const response = await sendMessage({ type: "YT_ANKI_SET_CONFIG", config });
  if (!response.ok) {
    setStatus(response.error || "Could not save settings", true);
    return false;
  }
  document.getElementById("service-url").value = response.payload.serviceUrl;
  document.getElementById("language").value = response.payload.language;
  setStatus("Saved");
  return true;
}

async function checkService() {
  const saved = await saveConfig();
  if (!saved) {
    return;
  }
  setStatus("Checking...");
  const response = await sendMessage({ type: "YT_ANKI_HEALTH" });
  if (!response.ok) {
    setStatus(response.error || "Service is not reachable", true);
    return;
  }
  setStatus("Service is reachable");
}

function reloadExtension() {
  setStatus("Reloading extension...");
  chrome.runtime.reload();
}

document.getElementById("save").addEventListener("click", saveConfig);
document.getElementById("check").addEventListener("click", checkService);
document.getElementById("reload-extension").addEventListener("click", reloadExtension);
loadConfig();
