const BUTTON_ID = "yt-anki-create-button";
const REPAIR_BUTTON_ID = "yt-anki-repair-button";
const SELECT_ID = "yt-anki-language-select";
const STATUS_ID = "yt-anki-status-pill";
const LANGUAGES = [
  ["ru", "RU"],
  ["es", "ES"],
  ["fr", "FR"],
  ["de", "DE"],
  ["it", "IT"],
  ["ja", "JA"]
];

function sendMessage(message) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(message, (response) => {
      resolve(response || { ok: false, error: chrome.runtime.lastError?.message || "No response" });
    });
  });
}

function currentVideoUrl() {
  const url = new URL(window.location.href);
  const videoId = url.searchParams.get("v");
  if (!videoId) {
    throw new Error("No YouTube video id found on this page");
  }
  return `https://www.youtube.com/watch?v=${videoId}`;
}

function selectedLanguage() {
  return document.getElementById(SELECT_ID)?.value || "ru";
}

function setStatus(text, tone = "idle") {
  const status = document.getElementById(STATUS_ID);
  if (!status) {
    return;
  }
  status.textContent = text;
  const colors = {
    idle: ["#f1f3f4", "#3c4043"],
    work: ["#e8f0fe", "#174ea6"],
    ok: ["#e6f4ea", "#137333"],
    error: ["#fce8e6", "#a50e0e"]
  };
  const [background, color] = colors[tone] || colors.idle;
  status.style.background = background;
  status.style.color = color;
}

function formatProgress(payload) {
  if (!payload) {
    return "Waiting";
  }
  const hasCount = Number.isInteger(payload.current) && Number.isInteger(payload.total);
  const count = hasCount ? ` ${payload.current}/${payload.total}` : "";
  return `${payload.message || payload.state || "Working"}${count}`;
}

async function pollJob(jobId, button, label, repair) {
  while (true) {
    const response = await sendMessage({ type: "YT_ANKI_JOB_STATUS", jobId });
    if (!response?.ok) {
      throw new Error(response?.error || "Could not read job status");
    }
    const status = response.payload;
    if (status.state === "complete") {
      return status.result || {};
    }
    if (status.state === "error") {
      throw new Error(status.error || "Processing failed");
    }
    const text = formatProgress(status);
    setStatus(text, "work");
    button.textContent = repair ? "Repairing..." : "Working...";
    button.title = text;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

function makeLanguageSelect() {
  const select = document.createElement("select");
  select.id = SELECT_ID;
  select.title = "Transcript language";
  select.style.cssText = [
    "height: 36px",
    "border: 1px solid rgba(0,0,0,.15)",
    "border-radius: 18px",
    "background: white",
    "color: #111",
    "font: 500 13px Arial, sans-serif",
    "padding: 0 8px",
    "margin-left: 8px"
  ].join(";");

  LANGUAGES.forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
  return select;
}

function makeStatus() {
  const status = document.createElement("span");
  status.id = STATUS_ID;
  status.textContent = "Ready";
  status.style.cssText = [
    "height: 28px",
    "line-height: 28px",
    "border-radius: 14px",
    "background: #f1f3f4",
    "color: #3c4043",
    "font: 500 12px Arial, sans-serif",
    "padding: 0 10px",
    "margin-left: 8px",
    "max-width: 180px",
    "overflow: hidden",
    "text-overflow: ellipsis",
    "white-space: nowrap"
  ].join(";");
  return status;
}

function baseButtonStyle(background, color = "white") {
  return [
    "height: 36px",
    "padding: 0 14px",
    "border: 1px solid rgba(0,0,0,.15)",
    "border-radius: 18px",
    `background: ${background}`,
    `color: ${color}`,
    "font: 500 14px Arial, sans-serif",
    "cursor: pointer",
    "margin-left: 8px"
  ].join(";");
}

function makeProcessButton({ id, label, title, repair, background, color }) {
  const button = document.createElement("button");
  button.id = id;
  button.type = "button";
  button.textContent = label;
  button.title = title;
  button.style.cssText = baseButtonStyle(background, color);

  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = repair ? "Repairing..." : "Working...";
    setStatus(repair ? "Repairing" : "Processing", "work");
    let videoUrl;
    try {
      videoUrl = currentVideoUrl();
    } catch (error) {
      button.disabled = false;
      button.textContent = "Error";
      button.title = error.message;
      setStatus("No video", "error");
      return;
    }
    let result;
    try {
      const response = await sendMessage({
        type: "YT_ANKI_PROCESS",
        videoUrl,
        language: selectedLanguage(),
        repair
      });
      if (!response?.ok) {
        throw new Error(response?.error || "Could not create cards");
      }
      result = await pollJob(response.payload.job_id, button, label, repair);
    } catch (error) {
      button.disabled = false;
      button.textContent = "Error";
      button.title = error.message || "Could not create cards";
      setStatus(error.message || "Failed", "error");
      setTimeout(() => {
        button.textContent = label;
      }, 4000);
      return;
    }
    button.disabled = false;
    const count = result.cards_created || 0;
    const deleted = result.cards_deleted || 0;
    button.textContent = repair ? `Fixed ${count}` : `Added ${count}`;
    button.title = repair
      ? `Deleted ${deleted} old cards and created ${count} cards`
      : `Created ${count} cards`;
    setStatus(repair ? `Fixed ${count}` : `Added ${count}`, "ok");
    setTimeout(() => {
      button.textContent = label;
      setStatus("Ready", "idle");
    }, 5000);
  });

  return button;
}

function makeButton() {
  return makeProcessButton({
    id: BUTTON_ID,
    label: "Anki",
    title: "Create Anki cards from this video's transcript",
    repair: false,
    background: "#0b57d0",
    color: "white"
  });
}

function makeRepairButton() {
  return makeProcessButton({
    id: REPAIR_BUTTON_ID,
    label: "Repair",
    title: "Delete and recreate this video's Anki cards, ignoring the seen-word database",
    repair: true,
    background: "#fbbc04",
    color: "#202124"
  });
}

function injectButton() {
  if (document.getElementById(BUTTON_ID)) {
    return;
  }
  const actions = document.querySelector("#top-level-buttons-computed");
  if (!actions) {
    return;
  }
  actions.prepend(makeStatus());
  actions.prepend(makeLanguageSelect());
  actions.prepend(makeRepairButton());
  actions.prepend(makeButton());
  sendMessage({ type: "YT_ANKI_GET_CONFIG" }).then((response) => {
    if (response?.ok && response.payload?.language) {
      const select = document.getElementById(SELECT_ID);
      if (select) {
        select.value = response.payload.language;
      }
    }
  });
}

const observer = new MutationObserver(injectButton);
observer.observe(document.documentElement, { childList: true, subtree: true });
injectButton();
