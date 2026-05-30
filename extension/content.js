const BUTTON_ID = "yt-anki-create-button";
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

function makeButton() {
  const button = document.createElement("button");
  button.id = BUTTON_ID;
  button.type = "button";
  button.textContent = "Anki";
  button.title = "Create Anki cards from this video's Russian transcript";
  button.style.cssText = [
    "height: 36px",
    "padding: 0 14px",
    "border: 1px solid rgba(0,0,0,.15)",
    "border-radius: 18px",
    "background: #0b57d0",
    "color: white",
    "font: 500 14px Arial, sans-serif",
    "cursor: pointer",
    "margin-left: 8px"
  ].join(";");

  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "Working...";
    setStatus("Processing", "work");
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
    const response = await sendMessage({
      type: "YT_ANKI_PROCESS",
      videoUrl,
      language: selectedLanguage()
    });
    button.disabled = false;
    if (!response?.ok) {
      button.textContent = "Error";
      button.title = response?.error || "Could not create cards";
      setStatus(response?.error || "Failed", "error");
      setTimeout(() => {
        button.textContent = "Anki";
      }, 4000);
      return;
    }
    const count = response.payload.cards_created;
    button.textContent = `Added ${count}`;
    button.title = `Created ${count} cards`;
    setStatus(`Added ${count}`, "ok");
    setTimeout(() => {
      button.textContent = "Anki";
      setStatus("Ready", "idle");
    }, 5000);
  });

  return button;
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
