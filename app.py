
import os
import logging
import threading
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent

# Render can use a custom path; locally use the project folder.
ARGOS_DIR = Path(
    os.getenv(
        "ARGOS_PACKAGE_DIR",
        str(BASE_DIR / "argos_packages")
    )
)

ARGOS_DIR.mkdir(parents=True, exist_ok=True)

os.environ["ARGOS_PACKAGES_DIR"] = str(ARGOS_DIR)
os.environ["ARGOS_CHUNK_TYPE"] = "MINISBD"
os.environ["ARGOS_DEVICE_TYPE"] = "cpu"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "True")

import argostranslate.settings
import argostranslate.package
import argostranslate.translate

argostranslate.settings.package_data_dir = ARGOS_DIR
argostranslate.settings.package_dirs = [ARGOS_DIR]
argostranslate.settings.chunk_type = (
    argostranslate.settings.ChunkType.MINISBD
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger("translation-service")

translation_lock = threading.RLock()

APP_VERSION = "5.2.1"

LANGUAGE_ALIASES = {
    "ar": "ar",
    "ara": "ar",
    "arabic": "ar",

    "en": "en",
    "eng": "en",
    "english": "en",

    "yo": "yo",
    "yor": "yo",
    "yoruba": "yo",

    "ha": "ha",
    "hau": "ha",
    "hausa": "ha",

    "fr": "fr",
    "fra": "fr",
    "fre": "fr",
    "french": "fr",

    "es": "es",
    "spa": "es",
    "spanish": "es",

    "pt": "pt",
    "por": "pt",
    "portuguese": "pt",

    "de": "de",
    "deu": "de",
    "ger": "de",
    "german": "de",

    "zh": "zh",
    "zho": "zh",
    "chi": "zh",
    "chinese": "zh",

    "ru": "ru",
    "rus": "ru",
    "russian": "ru",

    "tr": "tr",
    "tur": "tr",
    "turkish": "tr",

    "it": "it",
    "ita": "it",
    "italian": "it",

    "hi": "hi",
    "hin": "hi",
    "hindi": "hi",

    "ja": "ja",
    "jpn": "ja",
    "japanese": "ja",

    "ko": "ko",
    "kor": "ko",
    "korean": "ko",
}

LANGUAGE_NAMES = {
    "ar": "Arabic",
    "en": "English",
    "yo": "Yoruba",
    "ha": "Hausa",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "de": "German",
    "zh": "Chinese",
    "ru": "Russian",
    "tr": "Turkish",
    "it": "Italian",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
}


def normalize_language(value: str) -> str:
    if not value:
        return ""

    value = value.strip().lower().replace("_", "-")

    # Accept values such as eng_Latn and arb_Arab.
    if "-" in value:
        value = value.split("-")[0]

    if "_" in value:
        value = value.split("_")[0]

    return LANGUAGE_ALIASES.get(value, value)


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code.upper())


# =========================================================
# ARGOS CACHE AND PACKAGE HELPERS
# =========================================================

def clear_argos_cache():
    try:
        cache_clear = getattr(
            argostranslate.translate.get_installed_languages,
            "cache_clear",
            None
        )

        if cache_clear:
            cache_clear()

    except Exception:
        logger.exception("Could not clear Argos language cache")


def get_installed_packages():
    """
    Read installed packages from settings.package_dirs.

    Argos expects package directories to be inside ARGOS_DIR,
    for example argos_packages/ar_en/metadata.json.
    """
    clear_argos_cache()

    try:
        return argostranslate.package.get_installed_packages()
    except Exception:
        logger.exception("Failed to read installed Argos packages")
        return []


def get_installed_languages():
    clear_argos_cache()

    try:
        return argostranslate.translate.get_installed_languages()
    except Exception:
        logger.exception("Failed to load installed Argos languages")
        return []


def get_package_details():
    packages = get_installed_packages()
    result = []

    for package in packages:
        result.append({
            "from_code": getattr(package, "from_code", None),
            "from_name": getattr(package, "from_name", None),
            "to_code": getattr(package, "to_code", None),
            "to_name": getattr(package, "to_name", None),
            "package_version": str(
                getattr(package, "package_version", "")
            ),
            "package_path": str(
                getattr(package, "package_path", "")
            ),
        })

    return result


def find_translation(source_code: str, target_code: str):
    """
    Find a direct installed translation.

    This checks the actual installed language objects rather
    than the remote Argos package index.
    """
    source_code = normalize_language(source_code)
    target_code = normalize_language(target_code)

    languages = get_installed_languages()

    source_language = next(
        (language for language in languages
         if language.code == source_code),
        None
    )

    target_language = next(
        (language for language in languages
         if language.code == target_code),
        None
    )

    if not source_language or not target_language:
        return None

    try:
        return source_language.get_translation(target_language)
    except Exception:
        logger.exception(
            "Could not find translation %s -> %s",
            source_code,
            target_code
        )
        return None


def get_translation_routes():
    routes = []

    for package in get_installed_packages():
        from_code = getattr(package, "from_code", None)
        to_code = getattr(package, "to_code", None)

        if from_code and to_code:
            routes.append({
                "source": from_code,
                "source_name": getattr(package, "from_name", None),
                "target": to_code,
                "target_name": getattr(package, "to_name", None),
            })

    return routes


def verify_argos():
    """
    Run once when FastAPI starts and log what Argos can see.
    """
    logger.info("========================================")
    logger.info("Starting translation service %s", APP_VERSION)
    logger.info("Application directory: %s", BASE_DIR)
    logger.info("Argos package directory: %s", ARGOS_DIR)
    logger.info(
        "Argos configured package directory: %s",
        argostranslate.settings.package_data_dir
    )
    logger.info(
        "Argos package search directories: %s",
        argostranslate.settings.package_dirs
    )

    if not ARGOS_DIR.exists():
        logger.error("Argos package directory does not exist")
        return

    logger.info(
        "Folders inside package directory: %s",
        [item.name for item in ARGOS_DIR.iterdir() if item.is_dir()]
    )

    packages = get_installed_packages()
    languages = get_installed_languages()

    logger.info("Installed package count: %s", len(packages))
    logger.info("Installed language count: %s", len(languages))

    for package in packages:
        logger.info(
            "Package: %s -> %s | %s",
            getattr(package, "from_code", "?"),
            getattr(package, "to_code", "?"),
            getattr(package, "package_path", "?")
        )

    for language in languages:
        logger.info(
            "Installed language: %s (%s)",
            language.name,
            language.code
        )

    logger.info("Translation routes: %s", get_translation_routes())
    logger.info("========================================")


# =========================================================
# REQUEST MODELS
# =========================================================

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_language: str = Field(..., min_length=1)
    target_language: str = Field(..., min_length=1)


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def detect_language_code(text: str) -> Optional[str]:
    """
    Lightweight fallback detection.

    Arabic is detected by its Unicode character range.
    For Latin-script languages, install langdetect if you
    need automatic language identification.
    """
    if not text or not text.strip():
        return None

    arabic_characters = sum(
        1 for char in text
        if "\u0600" <= char <= "\u06FF"
        or "\u0750" <= char <= "\u077F"
        or "\u08A0" <= char <= "\u08FF"
    )

    if arabic_characters:
        return "ar"

    try:
        from langdetect import detect
        detected = detect(text)
        return normalize_language(detected)
    except ImportError:
        return None
    except Exception:
        return None


# =========================================================
# FASTAPI LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_argos()
    yield


app = FastAPI(
    title="Islam Path of Knowledge Translation Service",
    description="Offline translation API powered by Argos Translate",
    version=APP_VERSION,
    lifespan=lifespan
)

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": "Islam Path of Knowledge Translation Service",
        "version": APP_VERSION,
        "status": "running",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():
    packages = get_installed_packages()
    languages = get_installed_languages()
    routes = get_translation_routes()

    return {
        "success": True,
        "status": "running",
        "version": APP_VERSION,

        "installed_package_count": len(packages),
        "installed_language_count": len(languages),

        "installed_languages": [
            {
                "code": language.code,
                "name": language.name,
            }
            for language in languages
        ],

        "translation_routes": routes,

        "package_directory": str(ARGOS_DIR),
        "package_directory_exists": ARGOS_DIR.exists(),

        "package_search_directories": [
            str(directory)
            for directory in argostranslate.settings.package_dirs
        ],
    }


# =========================================================
# INSTALLED PACKAGES
# =========================================================

@app.get("/installed")
def installed():
    packages = get_package_details()
    languages = get_installed_languages()

    return {
        "success": True,
        "package_directory": str(ARGOS_DIR),
        "installed_package_count": len(packages),
        "installed_language_count": len(languages),
        "packages": packages,
        "languages": [
            {
                "code": language.code,
                "name": language.name,
            }
            for language in languages
        ],
        "translation_routes": get_translation_routes(),
    }


# =========================================================
# AVAILABLE INSTALLED LANGUAGES
# =========================================================

@app.get("/languages")
def languages():
    installed_languages = get_installed_languages()

    return {
        "success": True,
        "languages": [
            {
                "code": language.code,
                "name": language.name,
            }
            for language in installed_languages
        ],
        "count": len(installed_languages),
    }


# =========================================================
# DETECT LANGUAGE
# =========================================================

@app.post("/detect-language")
def detect_language(payload: dict):
    text = str(payload.get("text", "")).strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Text is required"
        )

    code = detect_language_code(text)

    return {
        "success": True,
        "language": code,
        "language_name": language_name(code) if code else None,
        "detected": code is not None,
    }


# =========================================================
# CHECK TRANSLATION SUPPORT
# =========================================================

@app.get("/can-translate")
def can_translate(
    source_language: str = Query(...),
    target_language: str = Query(...)
):
    source_code = normalize_language(source_language)
    target_code = normalize_language(target_language)

    if source_code == target_code:
        return {
            "success": True,
            "supported": True,
            "source_language": source_code,
            "target_language": target_code,
            "reason": "Source and target languages are the same.",
        }

    try:
        with translation_lock:
            translation = find_translation(
                source_code,
                target_code
            )

        supported = translation is not None

        return {
            "success": True,
            "supported": supported,
            "source_language": source_code,
            "target_language": target_code,
            "reason": (
                "Translation route is installed."
                if supported
                else "No installed direct translation route exists for this pair."
            ),
        }

    except Exception as error:
        logger.exception("Translation support check failed")

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =========================================================
# TRANSLATE
# =========================================================

@app.post("/translate")
def translate_text(request: TranslationRequest):
    text = request.text.strip()

    source_code = normalize_language(
        request.source_language
    )

    target_code = normalize_language(
        request.target_language
    )

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Text cannot be empty"
        )

    if source_code == target_code:
        return {
            "success": True,
            "translated_text": text,
            "source_language": source_code,
            "target_language": target_code,
            "message": "Source and target languages are the same.",
        }

    try:
        with translation_lock:
            translation = find_translation(
                source_code,
                target_code
            )

            if translation is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"No installed translation route exists "
                        f"for {source_code} -> {target_code}."
                    )
                )

            translated_text = translation.translate(text)

        if not translated_text:
            raise HTTPException(
                status_code=500,
                detail="The translation model returned an empty result."
            )

        return {
            "success": True,
            "translated_text": translated_text,
            "source_language": source_code,
            "source_language_name": language_name(source_code),
            "target_language": target_code,
            "target_language_name": language_name(target_code),
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("Translation failed")

        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(error)}"
        )


# =========================================================
# DIAGNOSTICS
# =========================================================

@app.get("/diagnostics")
def diagnostics():
    folders = []

    if ARGOS_DIR.exists():
        for folder in ARGOS_DIR.iterdir():
            if folder.is_dir():
                metadata = folder / "metadata.json"

                folders.append({
                    "folder": folder.name,
                    "path": str(folder),
                    "metadata_exists": metadata.exists(),
                    "model_exists": (folder / "model").exists(),
                    "sentencepiece_exists": (
                        folder / "sentencepiece.model"
                    ),
                })

    packages = get_package_details()

    return {
        "success": True,
        "python_package_directory": str(ARGOS_DIR),
        "directory_exists": ARGOS_DIR.exists(),
        "package_folders": folders,
        "installed_packages": packages,
        "installed_package_count": len(packages),
        "configured_argos_directory": str(
            argostranslate.settings.package_data_dir
        ),
        "configured_search_directories": [
            str(path)
            for path in argostranslate.settings.package_dirs
        ],
    }
