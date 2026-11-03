
import os
import traceback
from pathlib import Path

# Configure Argos BEFORE importing it.
BASE_DIR = Path(__file__).resolve().parent
ARGOS_DIR = BASE_DIR / "argos_packages"

os.environ["ARGOS_PACKAGES_DIR"] = str(ARGOS_DIR)
os.environ["ARGOS_CHUNK_TYPE"] = "MINISBD"
os.environ["ARGOS_DEVICE_TYPE"] = "cpu"

import argostranslate.settings
import argostranslate.package
import argostranslate.translate

argostranslate.settings.package_data_dir = ARGOS_DIR
argostranslate.settings.package_dirs = [ARGOS_DIR]
argostranslate.settings.chunk_type = (
    argostranslate.settings.ChunkType.MINISBD
)


def test_translation(source_code, target_code, text):
    print(f"\n{source_code.upper()} -> {target_code.upper()}:")

    try:
        languages = argostranslate.translate.get_installed_languages()

        source = next(
            (lang for lang in languages if lang.code == source_code),
            None
        )

        target = next(
            (lang for lang in languages if lang.code == target_code),
            None
        )

        if source is None:
            print(f"SOURCE LANGUAGE NOT FOUND: {source_code}")
            return

        if target is None:
            print(f"TARGET LANGUAGE NOT FOUND: {target_code}")
            return

        print(
            "Available outgoing translations:",
            [str(t) for t in source.translations_from]
        )

        translation = source.get_translation(target)

        if translation is None:
            print("TRANSLATION OBJECT IS NONE")
            print("Argos did not register this translation route.")
            return

        print("Translation object:", translation)

        result = translation.translate(text)

        print("TRANSLATION SUCCESSFUL:")
        print(result)

    except Exception as error:
        print("TRANSLATION ERROR:", repr(error))
        traceback.print_exc()


def main():
    print("\n========== ARGOS PACKAGE TEST ==========")

    print("\nPackage directory:")
    print(argostranslate.settings.package_dirs)

    print("\nChunk type:")
    print(argostranslate.settings.chunk_type)

    print("\nPackage folders:")

    for folder in ARGOS_DIR.iterdir():
        if folder.is_dir():
            try:
                package = argostranslate.package.Package(folder)

                print("\nPACKAGE:", folder.name)
                print("From:", package.from_code)
                print("To:", package.to_code)
                print("From name:", package.from_name)
                print("To name:", package.to_name)
                print("Version:", package.package_version)
                print("PACKAGE LOADED SUCCESSFULLY")

            except Exception:
                print("PACKAGE LOAD ERROR:", folder.name)
                traceback.print_exc()

    packages = argostranslate.package.get_installed_packages()

    print("\nInstalled packages:")

    for package in packages:
        print(
            package.from_code,
            "->",
            package.to_code,
            package.package_path
        )

    print("Package count:", len(packages))

    languages = argostranslate.translate.get_installed_languages()

    print("\nInstalled languages:")

    for language in languages:
        print(language.code, language.name)
        print(
            "Outgoing routes:",
            [str(t) for t in language.translations_from]
        )

    print("Language count:", len(languages))

    test_translation(
        "ar",
        "en",
        "مرحبا بكم في طريق المعرفة الإسلامية"
    )

    test_translation(
        "en",
        "ar",
        "Welcome to the Islamic Path of Knowledge"
    )

    print("\n========== END ARGOS TEST ==========")


if __name__ == "__main__":
    main()
