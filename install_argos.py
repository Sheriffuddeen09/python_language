
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARGOS_DIR = BASE_DIR / "argos_packages"

ARGOS_DIR.mkdir(parents=True, exist_ok=True)

# Configure the package directory before importing Argos.
os.environ["ARGOS_PACKAGE_DIR"] = str(ARGOS_DIR)

import argostranslate.package
import argostranslate.settings
import argostranslate.translate

# Ensure Argos uses the intended directory.
argostranslate.settings.package_data_dir = str(ARGOS_DIR)

print(f"Installing Argos packages into: {ARGOS_DIR}")

argostranslate.package.update_package_index()
packages = argostranslate.package.get_available_packages()

# Install Arabic -> English and English -> Arabic.
required_pairs = [
    ("ar", "en"),
    ("en", "ar"),
]

for source_code, target_code in required_pairs:
    package = next(
        (
            item
            for item in packages
            if item.from_code == source_code
            and item.to_code == target_code
        ),
        None,
    )

    if package is None:
        print(f"Package not found: {source_code} -> {target_code}")
        continue

    print(f"Downloading {source_code} -> {target_code}...")
    download_path = package.download()
    argostranslate.package.install_from_path(download_path)
    print(f"Installed {source_code} -> {target_code}")

print("\nInstalled languages:")

for language in argostranslate.translate.get_installed_languages():
    print(f"{language.code}: {language.name}")
    for translation in language.translations_from:
        print(f"  -> {translation.to_lang.code}")
