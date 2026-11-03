
import os
from pathlib import Path

# ==========================================
# ARGOS CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
ARGOS_DIR = BASE_DIR / "argos_packages"
ARGOS_DIR.mkdir(parents=True, exist_ok=True)

os.environ["ARGOS_PACKAGES_DIR"] = str(ARGOS_DIR)
os.environ["ARGOS_CHUNK_TYPE"] = "MINISBD"
os.environ["ARGOS_DEVICE_TYPE"] = "cpu"
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "True")

import argostranslate.settings
import argostranslate.package

argostranslate.settings.package_data_dir = ARGOS_DIR
argostranslate.settings.package_dirs = [ARGOS_DIR]
argostranslate.settings.chunk_type = (
    argostranslate.settings.ChunkType.MINISBD
)

# ==========================================
# LANGUAGES TO INSTALL
# ==========================================

LANGUAGES = {
    "ha": "Hausa",
    "yo": "Yoruba",
    "fr": "French",
    "sw": "Swahili",
    "ur": "Urdu",
    "id": "Indonesian",
    "tr": "Turkish",
    "fa": "Persian",
    "bn": "Bengali",
    "ms": "Malay",
    "es": "Spanish",
    "de": "German",
    "pt": "Portuguese",
    "hi": "Hindi",
    "zh": "Chinese",
    "ko": "Korean",
}

# ==========================================
# UPDATE OFFICIAL PACKAGE INDEX
# ==========================================

print("\nUpdating Argos package index...")

argostranslate.package.update_package_index()

available = argostranslate.package.get_available_packages()
installed = argostranslate.package.get_installed_packages()

installed_pairs = {
    (p.from_code, p.to_code)
    for p in installed
}

# ==========================================
# FIND AND INSTALL ENGLISH PAIRS
# ==========================================

success = []
unavailable = []
failed = []

for code, name in LANGUAGES.items():

    print(f"\nChecking {name} ({code})...")

    matching = [
        p for p in available
        if (
            (p.from_code == "en" and p.to_code == code)
            or
            (p.from_code == code and p.to_code == "en")
        )
    ]

    if not matching:
        print(f"NOT AVAILABLE: {name}")
        unavailable.append(name)
        continue

    for package in matching:

        pair = (package.from_code, package.to_code)

        if pair in installed_pairs:
            print(
                f"Already installed: "
                f"{package.from_code} -> {package.to_code}"
            )
            continue

        try:
            print(
                f"Downloading: "
                f"{package.from_code} -> {package.to_code}"
            )

            download_path = package.download()

            argostranslate.package.install_from_path(
                download_path
            )

            installed_pairs.add(pair)

            success.append(
                f"{package.from_code} -> {package.to_code}"
            )

            print("INSTALLATION SUCCESSFUL")

        except Exception as e:

            failed.append(
                f"{package.from_code} -> "
                f"{package.to_code}: {e}"
            )

            print("INSTALLATION FAILED:", e)


# ==========================================
# SUMMARY
# ==========================================

print("\n================================")
print("INSTALLATION SUMMARY")
print("================================")

print("\nSuccessfully installed:")

for item in success:
    print("OK:", item)

print("\nUnavailable languages:")

for item in unavailable:
    print("-", item)

print("\nFailed installations:")

for item in failed:
    print("-", item)

print("\nAll installed packages:")

for package in argostranslate.package.get_installed_packages():
    print(
        package.from_code,
        "->",
        package.to_code,
        "|",
        package.package_version
    )

print("\nFinished.")
