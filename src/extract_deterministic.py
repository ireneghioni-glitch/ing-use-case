'''
`extract_deterministic.py`
==========================
This file contains functions (small, reusable blocks of code) that calculate the 
so-called "deterministic" features.
'''

import json
from pathlib import Path
import spacy    # for sentence splitting

from src.config import GLOSSARY_PATH, ASSETS_PATH

# Lazy loaders — load model only at first call
_nlp_cache = {}

def _get_nlp(language: str):
    if language not in _nlp_cache:
        model_name = {
            "nl": "nl_core_news_sm",
            "fr": "fr_core_news_sm",
            "en": "en_core_web_sm",
        }[language]
        _nlp_cache[language] = spacy.load(model_name)
    return _nlp_cache[language]


# ========== Functions ==========

def load_glossary(path: Path = GLOSSARY_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def jargon_density(
        text: str, 
        language: str, 
        glossary: dict
) -> float:
    '''
    Counts jargon words percentage in scraped text.
    '''
    words = text.lower().split()
    if not words:
        return 0.0
    # defensive terms identification in current language in glossary
    terms = glossary.get(language, [])
    count = sum(1 for word in words if word in terms)
    return (count / len(words)) * 100


def mean_sentence_length(
        text: str, 
        language: str
) -> float:
    '''
    Calculates average number of tokens (words) per sentence.
    '''
    # lazy loader previously defined
    nlp = _get_nlp(language)
    # make spaCy analyze the text (gives back a Doc file)
    doc = nlp(text)
    # make Doc as a list of sentences (made of tokens=words)
    sentences = list(doc.sents)
    if not sentences:
        return 0.0
    # return sum of tokens in each sentence / number of sentences
    # --> average number of tokens per sentence
    return sum(len(sent) for sent in sentences) / len(sentences)


def word_count(text: str) -> int:
    '''
    Counts words in text.
    '''
    return len(text.split())


if __name__ == "__main__":

    # load glossary
    glossary = load_glossary()
    print(f"Loaded {len(glossary['en'])} English terms, {len(glossary['nl'])} Dutch terms, {len(glossary['fr'])} French terms.")

    # load first record from assets JSONL
    with open (ASSETS_PATH, "r", encoding="utf-8") as f:
        first_record = json.loads(f.readline())

    text = first_record["text"]
    bank = first_record.get("bank", "unknown")
    url = first_record.get("url", "unknown")
    # Language is not in `campaign_asset.jsonl` record yet: 
    # assume Dutch for KBC Brussels, French for Belfius, English for ING/Revolut 
    # as a placeholder - `SCRAPER.PY` TO BE FIXED WITH LANGUAGE
    language = "nl" if "kbc" in bank.lower() else "fr" if "belfius" in bank.lower() else "en"

    print(f"\nTesting on first asset: {bank} — {url}")
    print(f"Assumed language: {language}")
    print(f"Text length: {len(text)} chars")
    print(f"Word count: {word_count(text)}")
    print(f"Jargon density: {jargon_density(text, language, glossary):.2f} per 100 words")
    print(f"Mean sentence length: {mean_sentence_length(text, language):.2f} words")