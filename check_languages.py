
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARGOS_DIR = BASE_DIR / "argos_packages"

os.environ["ARGOS_PACKAGES_DIR"] = str(ARGOS_DIR)
os.environ["ARGOS_CHUNK_TYPE"] = "MINISBD"
os.environ["ARGOS_DEVICE_TYPE"] = "cpu"

import argostranslate.settings
import argostranslate.translate

argostranslate.settings.package_data_dir = ARGOS_DIR
argostranslate.settings.package_dirs = [ARGOS_DIR]
argostranslate.settings.chunk_type = (
    argostranslate.settings.ChunkType.MINISBD
)

languages = argostranslate.translate.get_installed_languages()

print("\nINSTALLED LANGUAGES")

for language in languages:
    print(language.code, "-", language.name)

print("\nAVAILABLE TRANSLATION ROUTES")

for source in languages:
    for target in languages:
        if source.code == target.code:
            continue

        translation = source.get_translation(target)

        if translation:
            print(
                source.code,
                "->",
                target.code
            )
