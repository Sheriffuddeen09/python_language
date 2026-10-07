from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch


app = FastAPI(
    title="Islam Path of Knowledge Translation Service",
    version="1.0.0",
)


MODEL_NAME = "facebook/nllb-200-distilled-600M"


print("Loading NLLB model...")
print(f"Model: {MODEL_NAME}")

 
device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print(f"Using device: {device}")

 
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

 
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME
)

model.to(device)
model.eval()


print("NLLB model loaded successfully.")

 
NLLB_LANGUAGES = {
    "ace_Arab": "Acehnese (Arabic)",
    "ace_Latn": "Acehnese (Latin)",
    "acm_Arab": "Mesopotamian Arabic",
    "acq_Arab": "Ta'izzi-Adeni Arabic",
    "aeb_Arab": "Tunisian Arabic",
    "afr_Latn": "Afrikaans",
    "ajp_Arab": "South Levantine Arabic",
    "aka_Latn": "Akan",
    "als_Latn": "Tosk Albanian",
    "amh_Ethi": "Amharic",
    "apc_Arab": "North Levantine Arabic",
    "arb_Arab": "Modern Standard Arabic",
    "ars_Arab": "Najdi Arabic",
    "ary_Arab": "Moroccan Arabic",
    "arz_Arab": "Egyptian Arabic",
    "asm_Beng": "Assamese",
    "ast_Latn": "Asturian",
    "awa_Deva": "Awadhi",
    "ayr_Latn": "Central Aymara",
    "azb_Arab": "South Azerbaijani",
    "azj_Latn": "North Azerbaijani",
    "bak_Cyrl": "Bashkir",
    "bam_Latn": "Bambara",
    "ban_Latn": "Balinese",
    "bel_Cyrl": "Belarusian",
    "bem_Latn": "Bemba",
    "ben_Beng": "Bengali",
    "bho_Deva": "Bhojpuri",
    "bjn_Arab": "Banjar (Arabic)",
    "bjn_Latn": "Banjar (Latin)",
    "bod_Tibt": "Tibetan",
    "bos_Latn": "Bosnian",
    "bug_Latn": "Buginese",
    "bul_Cyrl": "Bulgarian",
    "cat_Latn": "Catalan",
    "ceb_Latn": "Cebuano",
    "ces_Latn": "Czech",
    "cjk_Latn": "Chokwe",
    "ckb_Arab": "Central Kurdish",
    "cmn_Hans": "Chinese (Simplified)",
    "cmn_Hant": "Chinese (Traditional)",
    "crh_Latn": "Crimean Tatar",
    "cym_Latn": "Welsh",
    "dan_Latn": "Danish",
    "deu_Latn": "German",
    "dik_Latn": "Southwestern Dinka",
    "dyu_Latn": "Dyula",
    "dzo_Tibt": "Dzongkha",
    "ell_Grek": "Greek",
    "eng_Latn": "English",
    "epo_Latn": "Esperanto",
    "est_Latn": "Estonian",
    "eus_Latn": "Basque",
    "ewe_Latn": "Ewe",
    "fao_Latn": "Faroese",
    "fij_Latn": "Fijian",
    "fin_Latn": "Finnish",
    "fon_Latn": "Fon",
    "fra_Latn": "French",
    "fur_Latn": "Friulian",
    "fuv_Latn": "Nigerian Fulfulde",
    "gaz_Latn": "West Central Oromo",
    "gla_Latn": "Scottish Gaelic",
    "gle_Latn": "Irish",
    "glg_Latn": "Galician",
    "grn_Latn": "Guarani",
    "guj_Gujr": "Gujarati",
    "hat_Latn": "Haitian Creole",
    "heb_Hebr": "Hebrew",
    "hin_Deva": "Hindi",
    "hne_Deva": "Chhattisgarhi",
    "hrv_Latn": "Croatian",
    "hun_Latn": "Hungarian",
    "hye_Armn": "Armenian",
    "ibo_Latn": "Igbo",
    "ilo_Latn": "Ilocano",
    "ind_Latn": "Indonesian",
    "isl_Latn": "Icelandic",
    "ita_Latn": "Italian",
    "jav_Latn": "Javanese",
    "jpn_Jpan": "Japanese",
    "kab_Latn": "Kabyle",
    "kac_Latn": "Kachin",
    "kam_Latn": "Kamba",
    "kan_Knda": "Kannada",
    "kas_Arab": "Kashmiri (Arabic)",
    "kas_Deva": "Kashmiri (Devanagari)",
    "kat_Geor": "Georgian",
    "knc_Arab": "Central Kanuri (Arabic)",
    "knc_Latn": "Central Kanuri (Latin)",
    "kaz_Cyrl": "Kazakh",
    "kbp_Latn": "Kabiye",
    "kea_Latn": "Kabuverdianu",
    "khm_Khmr": "Khmer",
    "kik_Latn": "Kikuyu",
    "kin_Latn": "Kinyarwanda",
    "kir_Cyrl": "Kyrgyz",
    "kmb_Latn": "Kimbundu",
    "kmr_Latn": "Northern Kurdish",
    "kon_Latn": "Kongo",
    "kor_Hang": "Korean",
    "lao_Laoo": "Lao",
    "lij_Latn": "Ligurian",
    "lim_Latn": "Limburgish",
    "lin_Latn": "Lingala",
    "lit_Latn": "Lithuanian",
    "lmo_Latn": "Lombard",
    "ltg_Latn": "Latgalian",
    "ltz_Latn": "Luxembourgish",
    "lua_Latn": "Luba-Kasai",
    "lug_Latn": "Ganda",
    "luo_Latn": "Luo",
    "lus_Latn": "Mizo",
    "lvs_Latn": "Standard Latvian",
    "mag_Deva": "Magahi",
    "mai_Deva": "Maithili",
    "mal_Mlym": "Malayalam",
    "mar_Deva": "Marathi",
    "min_Latn": "Minangkabau",
    "mkd_Cyrl": "Macedonian",
    "mlt_Latn": "Maltese",
    "mni_Beng": "Meitei",
    "mos_Latn": "Mossi",
    "mri_Latn": "Maori",
    "mya_Mymr": "Burmese",
    "nld_Latn": "Dutch",
    "nno_Latn": "Norwegian Nynorsk",
    "nob_Latn": "Norwegian Bokmål",
    "npi_Deva": "Nepali",
    "nso_Latn": "Northern Sotho",
    "nus_Latn": "Nuer",
    "nya_Latn": "Chichewa",
    "oci_Latn": "Occitan",
    "ory_Orya": "Odia",
    "pag_Latn": "Pangasinan",
    "pan_Guru": "Punjabi",
    "pap_Latn": "Papiamento",
    "pbt_Arab": "Southern Pashto",
    "pes_Arab": "Iranian Persian",
    "plt_Latn": "Plateau Malagasy",
    "pol_Latn": "Polish",
    "por_Latn": "Portuguese",
    "prs_Arab": "Dari",
    "quy_Latn": "Quechua",
    "ron_Latn": "Romanian",
    "run_Latn": "Rundi",
    "rus_Cyrl": "Russian",
    "sag_Latn": "Sango",
    "san_Deva": "Sanskrit",
    "sat_Olck": "Santali",
    "scn_Latn": "Sicilian",
    "shn_Mymr": "Shan",
    "sin_Sinh": "Sinhala",
    "slk_Latn": "Slovak",
    "slv_Latn": "Slovenian",
    "smo_Latn": "Samoan",
    "sna_Latn": "Shona",
    "snd_Arab": "Sindhi",
    "som_Latn": "Somali",
    "sot_Latn": "Southern Sotho",
    "spa_Latn": "Spanish",
    "srd_Latn": "Sardinian",
    "srp_Cyrl": "Serbian",
    "ssw_Latn": "Swati",
    "sun_Latn": "Sundanese",
    "swe_Latn": "Swedish",
    "swh_Latn": "Swahili",
    "szl_Latn": "Silesian",
    "tam_Taml": "Tamil",
    "taq_Latn": "Tamasheq",
    "taq_Tfng": "Tamasheq (Tifinagh)",
    "tat_Cyrl": "Tatar",
    "tel_Telu": "Telugu",
    "tgk_Cyrl": "Tajik",
    "tha_Thai": "Thai",
    "tir_Ethi": "Tigrinya",
    "tpi_Latn": "Tok Pisin",
    "tsn_Latn": "Tswana",
    "tso_Latn": "Tsonga",
    "tuk_Latn": "Turkmen",
    "tum_Latn": "Tumbuka",
    "tur_Latn": "Turkish",
    "twi_Latn": "Twi",
    "tzm_Tfng": "Central Atlas Tamazight",
    "uig_Arab": "Uyghur",
    "ukr_Cyrl": "Ukrainian",
    "umb_Latn": "Umbundu",
    "urd_Arab": "Urdu",
    "uzn_Latn": "Uzbek",
    "vec_Latn": "Venetian",
    "vie_Latn": "Vietnamese",
    "war_Latn": "Waray",
    "wol_Latn": "Wolof",
    "xho_Latn": "Xhosa",
    "ydd_Hebr": "Eastern Yiddish",
    "yor_Latn": "Yoruba",
    "yue_Hant": "Cantonese",
    "zho_Hans": "Chinese (Simplified)",
    "zho_Hant": "Chinese (Traditional)",
    "zsm_Latn": "Malay",
    "zul_Latn": "Zulu",
}


LANGUAGE_NAMES = {
    code.lower(): name
    for code, name in NLLB_LANGUAGES.items()
}

LANGUAGE_CODES_BY_NAME = {
    name.lower(): code
    for code, name in NLLB_LANGUAGES.items()
}


LANGUAGE_ALIASES = {
    "chinese": "zho_Hans",
    "mandarin": "zho_Hans",
    "simplified chinese": "zho_Hans",
    "traditional chinese": "zho_Hant",
    "persian": "pes_Arab",
    "farsi": "pes_Arab",
    "igbo": "ibo_Latn",
    "yoruba": "yor_Latn",
    "hausa": "hau_Latn",
    "arabic": "arb_Arab",
    "english": "eng_Latn",
    "french": "fra_Latn",
    "spanish": "spa_Latn",
    "german": "deu_Latn",
    "portuguese": "por_Latn",
    "turkish": "tur_Latn",
    "urdu": "urd_Arab",
    "swahili": "swh_Latn",
    "amharic": "amh_Ethi",
    "italian": "ita_Latn",
    "dutch": "nld_Latn",
    "russian": "rus_Cyrl",
    "japanese": "jpn_Jpan",
    "korean": "kor_Hang",
    "hindi": "hin_Deva",
    "bengali": "ben_Beng",
    "malay": "zsm_Latn",
}


def resolve_language(language: str) -> str | None:
    """
    Convert a language name/code into an NLLB language code.
    """

    value = language.strip()

    if not value:
        return None

    if value in NLLB_LANGUAGES:
        return value

    lower_value = value.lower()

    if lower_value in LANGUAGE_NAMES:
        return lower_value

    if lower_value in LANGUAGE_CODES_BY_NAME:
        return LANGUAGE_CODES_BY_NAME[lower_value]

    if lower_value in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[lower_value]

    return None


class TranslationRequest(BaseModel):
    text: str
    source_language: str
    target_language: str = "english"


@app.get("/health")
def health():

    return {
        "success": True,
        "service": "translation",
        "model": MODEL_NAME,
        "device": str(device),
        "language_count": len(NLLB_LANGUAGES),
    }

@app.get("/languages")
def languages():

    return {
        "success": True,
        "count": len(NLLB_LANGUAGES),
        "languages": [
            {
                "code": code,
                "name": name,
            }
            for code, name in NLLB_LANGUAGES.items()
        ],
    }


@app.post("/translate")
def translate(request: TranslationRequest):

    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Text is required.",
        )

    source_language = resolve_language(
        request.source_language
    )

    if not source_language:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported source language: "
                f"{request.source_language}"
            ),
        )

    target_language = resolve_language(
        request.target_language
    )

    if not target_language:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported target language: "
                f"{request.target_language}"
            ),
        )

    if source_language == target_language:

        return {
            "success": True,
            "source_language": source_language,
            "source_language_name": NLLB_LANGUAGES[source_language],
            "target_language": target_language,
            "target_language_name": NLLB_LANGUAGES[target_language],
            "translation": text,
        }

    try:

        print(
            f"Translating "
            f"{source_language} -> {target_language}"
        )

        tokenizer.src_lang = source_language

        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        inputs = {
            key: value.to(device)
            for key, value in inputs.items()
        }

        forced_bos_token_id = tokenizer.convert_tokens_to_ids(
            target_language
        )

        with torch.no_grad():

            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=4,
            )

        translation = tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens=True,
        )[0]

        print("Translation completed.")

        return {
            "success": True,
            "source_language": source_language,
            "source_language_name": NLLB_LANGUAGES[source_language],
            "target_language": target_language,
            "target_language_name": NLLB_LANGUAGES[target_language],
            "translation": translation,
        }

    except Exception as e:

        print("Translation error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Translation failed.",
        )