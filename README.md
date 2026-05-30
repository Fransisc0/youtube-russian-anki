# YouTube Russian-to-Anki Card Generator

Open-source local tool for creating Anki sentence cards from captioned YouTube videos.

Local Chrome extension + Python service for turning captioned YouTube videos into Anki sentence cards.

## What It Does

- Adds a button to YouTube watch pages.
- Sends the current video URL to a local FastAPI service.
- Downloads captions and audio with `yt-dlp`.
- Splits captions into timestamped sentences.
- Clips sentence audio with `ffmpeg`.
- Finds new Russian lemmas using a local SQLite learner database.
- Translates full sentences to English with DeepL.
- Gets Russian word glosses and IPA from Wiktionary when available.
- Creates Anki cards through AnkiConnect.

## Setup

1. Install runtime tools:
   - Python 3.11+
   - `ffmpeg`
   - `yt-dlp`
   - Anki with the AnkiConnect add-on
2. Install Python dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `DEEPL_AUTH_KEY`.
4. Start Anki.
5. Run the service:

   ```powershell
   .\.venv\Scripts\python.exe -m yt_anki.service
   ```

6. Load `extension/` as an unpacked extension in Chrome:
   - Open `chrome://extensions`
   - Enable Developer Mode
   - Click "Load unpacked"
   - Select this repo's `extension` folder
7. Click the extension icon and press "Check" to confirm it can reach the local service.

## Usage

1. Open a YouTube video with captions in your learner language.
2. Select the transcript language next to the injected "Anki" button if needed.
3. Click the "Anki" button injected near the YouTube action bar.
4. Watch the on-page status and service logs for progress.
5. Review the created deck in Anki.

## Chrome Extension

The unpacked extension lives in `extension/`.

- `manifest.json` defines the Manifest V3 extension.
- `content.js` injects the YouTube page button, language selector, and status pill.
- `background.js` talks to the local service.
- `popup.html` lets you configure the service URL and default transcript language.

The service defaults to `http://127.0.0.1:8766`. AnkiConnect should remain on its usual `http://127.0.0.1:8765`.

## Card Shape

Front:

- Russian sentence
- Sentence audio, playable/autoplayable by Anki

Back:

- English sentence translation
- Word glosses, one per line:

```text
govorit (govorit, /govorit/) - to speak
```

## Notes

- V1 stops if no usable transcript exists. It does not run Whisper.
- IPA is only taken from Wiktionary. Missing IPA is left blank.
- The first time a lemma is encountered, the sentence can become a card. Seen lemmas are tracked in `data/learner.sqlite3`.
- The local service defaults to port `8766` so it does not conflict with AnkiConnect on `8765`.

## Development

Run the unit tests:

```powershell
python -m unittest discover -s tests
```

## License

MIT
