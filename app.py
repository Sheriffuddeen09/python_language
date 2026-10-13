import os
import gc
import logging
from pathlib import Path
from threading import RLock
from typing import Optional

import argostranslate.package
import argostranslate.translate
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langdetect import detect, LangDetectException

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
ARGOS_DIR = BASE_DIR / "argos_packages"
ARGOS_DIR.mkdir(parents=True, exist_ok=True)

os.environ["ARGOS_PACKAGE_DIR"] = str(ARGOS_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("translation-service")

app = FastAPI(
    title="Islam Path of Knowledge Translation Service",
    version="5.0.0",
    description="Language detection and translation using Argos Translate.",
)

# Change these origins to your real frontend domains in production.
# Keep localhost origins if you also use the local React development server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

translation_lock = RLock()

# Common language names and aliases.
# The actual available languages are discovered from Argos below.
LANGUAGE_NAMES = {
    "af": "Afrikaans",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "az": "Azerbaijani",
    "eu": "Basque",
    "bn": "Bengali",
    "bg": "Bulgarian",
    "ca": "Catalan",
    "zh-cn": "Chinese",
    "zh": "Chinese",
    "zh-tw": "Chinese (Traditional)",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "nl": "Dutch",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "fi": "Finnish",
    "fr": "French",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "is": "Icelandic",
    "id": "Indonesian",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "kn": "Kannada",
    "kk": "Kazakh",
    "ko": "Korean",
    "ky": "Kyrgyz",
    "la": "Latin",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "mk": "Macedonian",
    "ms": "Malay",
    "ml": "Malayalam",
    "mr": "Marathi",
    "mn": "Mongolian",
    "ne": "Nepali",
    "no": "Norwegian",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "pa": "Punjabi",
    "ro": "Romanian",
    "ru": "Russian",
    "sr": "Serbian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "es": "Spanish",
    "sw": "Swahili",
    "sv": "Swedish",
    "tl": "Tagalog",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "cy": "Welsh",
    "yo": "Yoruba",
}

# langdetect codes that need conversion to Argos package codes.
# Only use a mapping if the corresponding language exists in Argos.
DETECTION_ALIASES = {
    "zh-cn": "zh",
    "zh-tw": "zt",
}

class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source_language: Optional[str] = Field(
        default=None, min_length=2, max_length=50
    )
    target_language: str = Field(
        default="english", min_length=2, max_length=50
    )


# --------------------------------------------------
# LANGUAGE HELPERS
# --------------------------------------------------

def normalize_name(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def get_installed_languages():
    return argostranslate.translate.get_installed_languages()


def get_installed_codes():
    return {language.code for language in get_installed_languages()}


def get_available_packages():
    try:
        return argostranslate.package.get_available_packages()
    except Exception:
        logger.exception("Could not read Argos package index")
        return []


def get_package_languages():
    """
    Return languages found in the currently available package index.
    This is broader than only the languages installed on this server.
    """
    languages = {}

    for package in get_available_packages():
        languages[package.from_code] = package.from_name
        languages[package.to_code] = package.to_name

    for code, name in LANGUAGE_NAMES.items():
        if code in languages:
            languages[code] = name

    return languages


def resolve_language(value: str):
    """
    Resolve a language name, code, or supported alias to an Argos code.
    """
    normalized = normalize_name(value)

    # Check actual installed languages.
    for language in get_installed_languages():
        if normalized == normalize_name(language.code):
            return language.code

        if normalized == normalize_name(language.name):
            return language.code

    # Check names and common language codes from the package index.
    available = get_package_languages()

    for code, name in available.items():
        if normalized == normalize_name(code):
            return code

        if normalized == normalize_name(name):
            return code

    # Check the common language names dictionary.
    for code, name in LANGUAGE_NAMES.items():
        if normalized in {
            normalize_name(code),
            normalize_name(name),
        }:
            # Do not accept a language that Argos does not know about.
            if code in available or code in get_installed_codes():
                return code

    # Common special aliases.
    aliases = {
        "farsi": "fa",
        "persian": "fa",
        "mandarin": "zh",
        "chinese-simplified": "zh",
        "chinese-traditional": "zt",
        "filipino": "tl",
        "tagalog": "tl",
    }

    code = aliases.get(normalized)

    if code and (
        code in available or code in get_installed_codes()
    ):
        return code

    return None


def language_display_name(code: str) -> str:
    for language in get_installed_languages():
        if language.code == code:
            return language.name

    return LANGUAGE_NAMES.get(code, code.upper())


def detect_language(text: str):
    """
    Identify the likely language and verify that Argos knows it.
    Short text may be ambiguous; the frontend should handle unknown results.
    """
    try:
        detected = detect(text)
    except LangDetectException:
        return None

    detected = DETECTION_ALIASES.get(detected, detected)

    if detected in get_package_languages() or detected in get_installed_codes():
        return detected

    return None


def find_translation(source_code: str, target_code: str):
    """
    Ask Argos for a translation object. Argos may use intermediate
    languages when suitable installed packages are available.
    """
    source = argostranslate.translate.get_language_from_code(source_code)
    target = argostranslate.translate.get_language_from_code(target_code)

    if source is None or target is None:
        return None

    return source.get_translation(target)


# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "success": True,
        "service": "Islam Path of Knowledge Translation Service",
        "version": "5.0.0",
        "endpoints": [
            "/health",
            "/languages",
            "/installed",
            "/detect-language",
            "/can-translate",
            "/translate",
        ],
    }


@app.get("/health")
def health():
    installed = get_installed_languages()

    return {
        "success": True,
        "status": "running",
        "installed_languages": [
            {"code": language.code, "name": language.name}
            for language in installed
        ],
        "installed_language_count": len(installed),
        "package_directory": str(ARGOS_DIR),
    }


@app.get("/languages")
def languages():
    """
    Return languages in the Argos package index.
    A language appearing here does not guarantee that every pair exists.
    """
    available = get_package_languages()
    installed_codes = get_installed_codes()

    return {
        "success": True,
        "languages": [
            {
                "code": code,
                "name": name,
                "installed": code in installed_codes,
            }
            for code, name in sorted(
                available.items(), key=lambda item: item[1].lower()
            )
        ],
        "count": len(available),
    }


@app.get("/installed")
def installed():
    installed_languages = get_installed_languages()

    return {
        "success": True,
        "languages": [
            {
                "code": language.code,
                "name": language.name,
                "can_translate_to": [
                    {
                        "code": translation.to_lang.code,
                        "name": translation.to_lang.name,
                    }
                    for translation in language.translations_from
                ],
            }
            for language in installed_languages
        ],
    }


@app.get("/detect-language")
def detect_language_endpoint(
    text: str = Query(..., min_length=1, max_length=5000)
):
    code = detect_language(text)

    if not code:
        return {
            "success": True,
            "detected": False,
            "language": None,
            "message": (
                "Language could not be identified as a language "
                "available in the Argos package index."
            ),
        }

    return {
        "success": True,
        "detected": True,
        "language": {
            "code": code,
            "name": language_display_name(code),
        },
    }


@app.get("/can-translate")
def can_translate(
    source_language: str = Query(...),
    target_language: str = Query("english"),
):
    source_code = resolve_language(source_language)
    target_code = resolve_language(target_language)

    if not source_code:
        return {
            "success": True,
            "supported": False,
            "reason": "Unsupported source language.",
        }

    if not target_code:
        return {
            "success": True,
            "supported": False,
            "reason": "Unsupported target language.",
        }

    if source_code == target_code:
        return {
            "success": True,
            "supported": True,
            "source_language": source_code,
            "target_language": target_code,
        }

    try:
        with translation_lock:
            translation = find_translation(source_code, target_code)

        supported = translation is not None

        return {
            "success": True,
            "supported": supported,
            "source_language": source_code,
            "target_language": target_code,
            "reason": None if supported else (
                "No installed translation route exists for this pair."
            ),
        }

    except Exception:
        logger.exception("Translation capability check failed")
        return {
            "success": True,
            "supported": False,
            "reason": "Could not verify this translation pair.",
        }


@app.post("/translate")
def translate(request: TranslationRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Text cannot be empty.",
        )

    source_code = (
        resolve_language(request.source_language)
        if request.source_language
        else detect_language(text)
    )

    target_code = resolve_language(request.target_language)

    if not source_code:
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not identify a supported source language. "
                "Choose the language manually."
            ),
        )

    if not target_code:
        raise HTTPException(
            status_code=422,
            detail="The requested target language is not supported.",
        )

    if source_code == target_code:
        return {
            "success": True,
            "source_language": source_code,
            "source_language_name": language_display_name(source_code),
            "target_language": target_code,
            "target_language_name": language_display_name(target_code),
            "translation": text,
        }

    try:
        with translation_lock:
            # This checks installed translation routes, including
            # any intermediate routes Argos can construct.
            translation = find_translation(source_code, target_code)

            if translation is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"No installed translation route from "
                        f"{language_display_name(source_code)} to "
                        f"{language_display_name(target_code)}."
                    ),
                )

            translated_text = translation.translate(text)

        if not translated_text:
            raise HTTPException(
                status_code=502,
                detail="The translation service returned an empty result.",
            )

        return {
            "success": True,
            "source_language": source_code,
            "source_language_name": language_display_name(source_code),
            "target_language": target_code,
            "target_language_name": language_display_name(target_code),
            "translation": translated_text,
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Translation failed")
        raise HTTPException(
            status_code=500,
            detail="Translation failed. Please try again.",
        )

    finally:
        gc.collect()