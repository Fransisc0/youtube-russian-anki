from __future__ import annotations


class DeepLClient:
    def __init__(self, auth_key: str) -> None:
        self.auth_key = auth_key
        self.endpoint = (
            "https://api-free.deepl.com/v2/translate"
            if auth_key.endswith(":fx")
            else "https://api.deepl.com/v2/translate"
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        import requests

        if not self.auth_key:
            raise RuntimeError("DEEPL_AUTH_KEY is required before creating Anki cards.")
        response = requests.post(
            self.endpoint,
            data={
                "auth_key": self.auth_key,
                "text": text,
                "source_lang": source_lang.upper(),
                "target_lang": target_lang,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["translations"][0]["text"]
