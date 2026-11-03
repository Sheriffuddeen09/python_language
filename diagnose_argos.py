
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARGOS_DIR = BASE_DIR / "argos_packages"

os.environ["ARGOS_PACKAGE_DIR"] = str(ARGOS_DIR)

import argostranslate.settings
import argostranslate.package
import argostranslate.translate

argostranslate.settings.package_data_dir = str(ARGOS_DIR)

print("\n========== ARGOS DIAGNOSTICS ==========")

print("\nPython:")
print(sys.executable)

print("\nArgos version:")
try:
    from importlib.metadata import version
    print(version("argostranslate"))
except Exception as e:
    print(e)

print("\nEnvironment package directory:")
print(os.environ.get("ARGOS_PACKAGE_DIR"))

print("\nConfigured package directory:")
print(argostranslate.settings.package_data_dir)

print("\nArgos settings attributes:")
for name in dir(argostranslate.settings):
    if "dir" in name.lower() or "path" in name.lower():
        try:
            print(name, "=", getattr(argostranslate.settings, name))
        except Exception:
            pass

print("\nPackage directory exists:")
print(ARGOS_DIR.exists())

print("\nDirectory contents:")

if ARGOS_DIR.exists():
    for item in ARGOS_DIR.rglob("*"):
        print(
            "DIR " if item.is_dir() else "FILE",
            item
        )

print("\nInstalled languages:")

try:
    installed = (
        argostranslate.translate
        .get_installed_languages()
    )

    print("Count:", len(installed))

    for language in installed:
        print(
            language.name,
            language.code
        )

        for translation in language.translations_from:
            print(
                "  ",
                language.code,
                "->",
                translation.to_lang.code
            )

except Exception as e:
    print("ERROR:", repr(e))

print("\nPackage index:")

try:
    packages = (
        argostranslate.package
        .get_available_packages()
    )

    print("Available:", len(packages))

except Exception as e:
    print("ERROR:", repr(e))

print("\n========== END DIAGNOSTICS ==========")
