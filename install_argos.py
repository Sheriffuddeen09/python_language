import os
import sys
import traceback
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

ARGOS_DIR = BASE_DIR / "argos_packages"

ARGOS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

os.environ["ARGOS_PACKAGE_DIR"] = str(ARGOS_DIR)

import argostranslate.settings

argostranslate.settings.package_data_dir = str(ARGOS_DIR)

argostranslate.settings.package_dirs = [ARGOS_DIR]

print("Argos package data directory:",
      argostranslate.settings.package_data_dir)

print("Argos package directories:",
      argostranslate.settings.package_dirs)

import argostranslate.package
import argostranslate.translate

REQUIRED_PAIRS = [
    ("ar", "en"),
    ("en", "ar"),
]


# ==================================================
# INSTALLATION
# ==================================================

def install_languages():

    print("\n" + "=" * 60)
    print("ISLAM PATH OF KNOWLEDGE")
    print("ARGOS TRANSLATION INSTALLER")
    print("=" * 60)

    print("Package directory:", ARGOS_DIR)

    # Update package index
    print("\nUpdating Argos package index...")

    argostranslate.package.update_package_index()

    packages = (
        argostranslate.package.get_available_packages()
    )

    print("Available packages:", len(packages))

    if not packages:
        raise RuntimeError(
            "No Argos packages found. Check network connectivity."
        )

    # Install each required direction
    for source_code, target_code in REQUIRED_PAIRS:

        print(
            f"\nInstalling {source_code} -> {target_code}"
        )

        package = next(
            (
                item
                for item in packages
                if item.from_code == source_code
                and item.to_code == target_code
            ),
            None
        )

        if package is None:
            raise RuntimeError(
                f"Package not found: "
                f"{source_code} -> {target_code}"
            )

        print(
            f"Downloading {package.from_name} "
            f"-> {package.to_name}"
        )

        download_path = package.download()

        if not download_path:
            raise RuntimeError(
                f"Download failed: "
                f"{source_code} -> {target_code}"
            )

        argostranslate.package.install_from_path(
            download_path
        )

        print(
            f"Installed: {source_code} -> {target_code}"
        )

    # ==================================================
    # VERIFY LANGUAGES
    # ==================================================

    print("\nVerifying installed languages...")

    installed = (
        argostranslate.translate.get_installed_languages()
    )

    installed_codes = {
        language.code
        for language in installed
    }

    for language in installed:

        print(
            f"\n{language.name} ({language.code})"
        )

        for translation in language.translations_from:

            print(
                f"  {language.code} -> "
                f"{translation.to_lang.code}"
            )

    # Verify both directions
    for source_code, target_code in REQUIRED_PAIRS:

        source = (
            argostranslate.translate
            .get_language_from_code(source_code)
        )

        target = (
            argostranslate.translate
            .get_language_from_code(target_code)
        )

        if source is None or target is None:
            raise RuntimeError(
                f"Missing installed language: "
                f"{source_code} or {target_code}"
            )

        translation = source.get_translation(target)

        if translation is None:
            raise RuntimeError(
                f"Translation route missing: "
                f"{source_code} -> {target_code}"
            )

        print(
            f"Verified: {source_code} -> {target_code}"
        )

    print("\n" + "=" * 60)
    print("INSTALLATION COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print("Installed languages:", sorted(installed_codes))


if __name__ == "__main__":

    try:
        install_languages()

    except Exception as error:

        print("\nINSTALLATION FAILED")
        print(str(error))

        traceback.print_exc()

        sys.exit(1)
