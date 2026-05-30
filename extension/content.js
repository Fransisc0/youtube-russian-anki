const BUTTON_ID = "yt-anki-create-button";
const SELECT_ID = "yt-anki-language-select";

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

  [
    ["ru", "RU"],
    ["es", "ES"],
    ["fr", "FR"],
    ["de", "DE"],
    ["it", "IT"],
    ["ja", "JA"]
  ].forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    select.appendChild(option);
  });
  return select;
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

  button.addEventListener("click", () => {
    button.disabled = true;
    button.textContent = "Working...";
    let videoUrl;
    try {
      videoUrl = currentVideoUrl();
    } catch (error) {
      button.disabled = false;
      button.textContent = "Error";
      button.title = error.message;
      return;
    }
    chrome.runtime.sendMessage(
      { type: "YT_ANKI_PROCESS", videoUrl, language: selectedLanguage() },
      (response) => {
        button.disabled = false;
        if (!response?.ok) {
          button.textContent = "Error";
          button.title = response?.error || "Could not create cards";
          setTimeout(() => {
            button.textContent = "Anki";
          }, 4000);
          return;
        }
        button.textContent = `Added ${response.payload.cards_created}`;
        button.title = `Created ${response.payload.cards_created} cards`;
        setTimeout(() => {
          button.textContent = "Anki";
        }, 5000);
      }
    );
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
  actions.prepend(makeLanguageSelect());
  actions.prepend(makeButton());
}

const observer = new MutationObserver(injectButton);
observer.observe(document.documentElement, { childList: true, subtree: true });
injectButton();
