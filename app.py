import gc
import os
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import argostranslate.package
import argostranslate.translate


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Islam Path of Knowledge Translation Service",
    version="3.0.0",
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Store Argos models inside the Render service directory.
# This keeps everything together and makes the location predictable.
ARGOS_DIR = BASE_DIR / "argos_packages"

ARGOS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

os.environ["ARGOS_PACKAGE_DIR"] = str(ARGOS_DIR)


# ============================================================
# LOCK
# ============================================================

translation_lock = Lock()


# ============================================================
# LANGUAGE LIST
# ============================================================

LANGUAGES = {
    "english": {
        "code": "en",
        "name": "English",
    },

    "arabic": {
        "code": "ar",
        "name": "Arabic",
    },

    "french": {
        "code": "fr",
        "name": "French",
    },

    "spanish": {
        "code": "es",
        "name": "Spanish",
    },

    "german": {
        "code": "de",
        "name": "German",
    },

    "portuguese": {
        "code": "pt",
        "name": "Portuguese",
    },

    "italian": {
        "code": "it",
        "name": "Italian",
    },

    "turkish": {
        "code": "tr",
        "name": "Turkish",
    },

    "hindi": {
        "code": "hi",
        "name": "Hindi",
    },

    "indonesian": {
        "code": "id",
        "name": "Indonesian",
    },

    "russian": {
        "code": "ru",
        "name": "Russian",
    },

    "chinese": {
        "code": "zh",
        "name": "Chinese",
    },

    "japanese": {
        "code": "ja",
        "name": "Japanese",
    },

    "korean": {
        "code": "ko",
        "name": "Korean",
    },

    "dutch": {
        "code": "nl",
        "name": "Dutch",
    },

    "swedish": {
        "code": "sv",
        "name": "Swedish",
    },

    "ukrainian": {
        "code": "uk",
        "name": "Ukrainian",
    },

    "polish": {
        "code": "pl",
        "name": "Polish",
    },

    "greek": {
        "code": "el",
        "name": "Greek",
    },

    "hebrew": {
        "code": "he",
        "name": "Hebrew",
    },

    "persian": {
        "code": "fa",
        "name": "Persian",
    },

    "urdu": {
        "code": "ur",
        "name": "Urdu",
    },

    "swahili": {
        "code": "sw",
        "name": "Swahili",
    },
}


# ============================================================
# ALIASES
# ============================================================

LANGUAGE_ALIASES = {
    "en": "en",
    "english": "en",

    "ar": "ar",
    "arabic": "ar",

    "fr": "fr",
    "french": "fr",

    "es": "es",
    "spanish": "es",

    "de": "de",
    "german": "de",

    "pt": "pt",
    "portuguese": "pt",

    "it": "it",
    "italian": "it",

    "tr": "tr",
    "turkish": "tr",

    "hi": "hi",
    "hindi": "hi",

    "id": "id",
    "indonesian": "id",

    "ru": "ru",
    "russian": "ru",

    "zh": "zh",
    "zh-cn": "zh",
    "chinese": "zh",

    "ja": "ja",
    "japanese": "ja",

    "ko": "ko",
    "korean": "ko",

    "nl": "nl",
    "dutch": "nl",

    "sv": "sv",
    "swedish": "sv",

    "uk": "uk",
    "ukrainian": "uk",

    "pl": "pl",
    "polish": "pl",

    "el": "el",
    "greek": "el",

    "he": "he",
    "hebrew": "he",

    "fa": "fa",
    "persian": "fa",
    "farsi": "fa",

    "ur": "ur",
    "urdu": "ur",

    "sw": "sw",
    "swahili": "sw",
}


# ============================================================
# REQUEST
# ============================================================

class TranslationRequest(BaseModel):

    text: str

    source_language: str

    target_language: str


# ============================================================
# RESOLVE LANGUAGE
# ============================================================

def resolve_language(language: str):

    if not isinstance(language, str):
        return None

    value = language.strip().lower()

    return LANGUAGE_ALIASES.get(value)


# ============================================================
# FIND INSTALLED TRANSLATION
# ============================================================

def get_translation(source_code, target_code):

    try:

        translation = (
            argostranslate.translate
            .get_translation_from_codes(
                source_code,
                target_code,
            )
        )

        return translation

    except Exception:

        return None


# ============================================================
# INSTALL LANGUAGE PAIR
# ============================================================

def install_language_pair(
    source_code,
    target_code,
):

    print(
        f"Checking translation package: "
        f"{source_code} -> {target_code}"
    )

    # First check if already installed.

    translation = get_translation(
        source_code,
        target_code,
    )

    if translation is not None:

        print(
            f"Translation package already installed: "
            f"{source_code} -> {target_code}"
        )

        return translation

    print("Updating Argos package index...")

    try:

        argostranslate.package.update_package_index()

    except Exception as e:

        print(
            "Could not update Argos package index:",
            str(e),
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Translation package index could not "
                "be downloaded."
            ),
        )

    available_packages = (
        argostranslate.package
        .get_available_packages()
    )

    package = None

    # Direct language pair.

    for available_package in available_packages:

        if (
            available_package.from_code
            == source_code
            and
            available_package.to_code
            == target_code
        ):

            package = available_package

            break

    if package is None:

        raise HTTPException(
            status_code=422,
            detail=(
                f"No direct offline translation package "
                f"exists for {source_code} -> {target_code}."
            ),
        )

    print(
        f"Downloading translation package: "
        f"{source_code} -> {target_code}"
    )

    try:

        package_path = package.download()

        print(
            "Installing translation package..."
        )

        argostranslate.package.install_from_path(
            package_path
        )

        # Remove downloaded archive after installation
        # to reduce disk usage.

        try:

            package_path.unlink(
                missing_ok=True
            )

        except Exception:
            pass

    except Exception as e:

        print(
            "Translation package installation failed:",
            str(e),
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Could not install the translation "
                "language package."
            ),
        )

    # Refresh language list.

    try:

        argostranslate.translate.get_installed_languages.cache_clear()

    except Exception:
        pass

    translation = get_translation(
        source_code,
        target_code,
    )

    if translation is None:

        raise HTTPException(
            status_code=500,
            detail=(
                "Translation package was installed "
                "but could not be loaded."
            ),
        )

    print(
        f"Translation package ready: "
        f"{source_code} -> {target_code}"
    )

    return translation


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,
        "service": (
            "Islam Path of Knowledge "
            "Translation Service"
        ),
        "status": "running",
        "engine": "Argos Translate",
        "offline_model": True,
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    try:

        installed = (
            argostranslate.translate
            .get_installed_languages()
        )

        installed_languages = [
            {
                "code": language.code,
                "name": language.name,
            }
            for language in installed
        ]

    except Exception:

        installed_languages = []

    return {
        "success": True,
        "service": "translation",
        "engine": "Argos Translate",
        "offline_model": True,
        "installed_languages": installed_languages,
    }


# ============================================================
# LANGUAGES
# ============================================================

@app.get("/languages")
def languages():

    return {
        "success": True,
        "count": len(LANGUAGES),
        "languages": [
            {
                "name": data["name"],
                "code": data["code"],
            }
            for data in LANGUAGES.values()
        ],
    }


# ============================================================
# INSTALLED PACKAGES
# ============================================================

@app.get("/installed")
def installed():

    try:

        packages = (
            argostranslate.package
            .get_installed_packages()
        )

        result = []

        for package in packages:

            result.append(
                {
                    "from": package.from_code,
                    "from_name": package.from_name,
                    "to": package.to_code,
                    "to_name": package.to_name,
                    "version": package.package_version,
                }
            )

        return {
            "success": True,
            "count": len(result),
            "packages": result,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ============================================================
# TRANSLATE
# ============================================================

@app.post("/translate")
def translate(request: TranslationRequest):

    text = request.text.strip()

    if not text:

        raise HTTPException(
            status_code=422,
            detail="Text is required.",
        )

    source_code = resolve_language(
        request.source_language
    )

    if source_code is None:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported source language: "
                f"{request.source_language}"
            ),
        )

    target_code = resolve_language(
        request.target_language
    )

    if target_code is None:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported target language: "
                f"{request.target_language}"
            ),
        )

    # Same language.

    if source_code == target_code:

        return {
            "success": True,
            "source_language": source_code,
            "target_language": target_code,
            "translation": text,
        }

    # --------------------------------------------------------
    # Only one translation operation at a time.
    #
    # This is important for a 512 MB instance.
    # --------------------------------------------------------

    with translation_lock:

        translation = install_language_pair(
            source_code,
            target_code,
        )

        try:

            translated_text = translation.translate(
                text
            )

        except Exception as e:

            print(
                "Translation failed:",
                str(e),
            )

            raise HTTPException(
                status_code=500,
                detail="Translation failed.",
            )

        # Give Python a chance to release temporary objects.

        gc.collect()

    return {
        "success": True,
        "source_language": source_code,
        "target_language": target_code,
        "translation": translated_text,
    }