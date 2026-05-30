from __future__ import annotations

from dataclasses import dataclass

from .deepl_client import DeepLClient
from .settings import Settings


@dataclass(frozen=True)
class TranslationRequest:
    text: str
    source_lang: str
    target_lang: str


class Translator:
    def translate(self, request: TranslationRequest) -> str:
        raise NotImplementedError


class DeepLTranslator(Translator):
    def __init__(self, auth_key: str) -> None:
        self.client = DeepLClient(auth_key)

    def translate(self, request: TranslationRequest) -> str:
        return self.client.translate(
            request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )


class ArgosTranslator(Translator):
    def __init__(self, auto_install: bool = True) -> None:
        self.auto_install = auto_install

    def translate(self, request: TranslationRequest) -> str:
        try:
            import argostranslate.package
            import argostranslate.translate
        except ImportError as exc:
            raise RuntimeError(
                "Argos Translate is not installed. Run install.bat or pip install -r requirements.txt."
            ) from exc

        source = normalize_argos_language(request.source_lang)
        target = normalize_argos_language(request.target_lang)
        installed = argostranslate.translate.get_installed_languages()
        source_language = next((lang for lang in installed if lang.code == source), None)
        target_language = next((lang for lang in installed if lang.code == target), None)

        if not source_language or not target_language or not source_language.get_translation(target_language):
            if not self.auto_install:
                raise RuntimeError(f"Argos language package is not installed for {source}->{target}.")
            install_argos_package(source, target)
            installed = argostranslate.translate.get_installed_languages()
            source_language = next((lang for lang in installed if lang.code == source), None)
            target_language = next((lang for lang in installed if lang.code == target), None)

        if not source_language or not target_language:
            raise RuntimeError(f"Argos language package is not available for {source}->{target}.")

        translation = source_language.get_translation(target_language)
        if translation is None:
            raise RuntimeError(f"Argos language package is not available for {source}->{target}.")
        return translation.translate(request.text)


def install_argos_package(source: str, target: str) -> None:
    import argostranslate.package

    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package = next(
        (
            item
            for item in available_packages
            if item.from_code == source and item.to_code == target
        ),
        None,
    )
    if package is None:
        raise RuntimeError(f"No Argos package found for {source}->{target}.")
    package_path = package.download()
    argostranslate.package.install_from_path(package_path)


def normalize_argos_language(language: str) -> str:
    language = language.lower()
    if "-" in language:
        language = language.split("-", 1)[0]
    if language == "en-us":
        return "en"
    return language


def create_translator(settings: Settings) -> Translator:
    provider = settings.translation_provider.lower()
    if provider == "argos":
        return ArgosTranslator(auto_install=settings.argos_auto_install)
    if provider == "deepl":
        if not settings.deepl_auth_key:
            raise RuntimeError("DEEPL_AUTH_KEY is required when TRANSLATION_PROVIDER=deepl.")
        return DeepLTranslator(settings.deepl_auth_key)
    raise RuntimeError(f"Unknown TRANSLATION_PROVIDER: {settings.translation_provider}")
