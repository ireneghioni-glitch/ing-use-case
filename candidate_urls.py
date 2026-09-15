"""
Marketing Spy — Manually curated candidate URLs, per bank.

Why manual: reproducibility. A fixed, human-reviewed list is easier to
justify to the business ("this is what we considered, and why") than an
agent freely exploring a sitemap — it also removes a source of
non-determinism (no risk of the agent wandering off-scope or hallucinating
a URL) and cuts LLM calls per page since the agent no longer needs to
decide "should I even look at this page?".

Each entry: (url, short_note). The note is just for your own reference
when reviewing this file later — it is not sent to the LLM.

All URLs below have been checked against each bank's robots.txt as of
2026-09-15 (see robots_checker.py) and confirmed ALLOWED for the exact
paths listed. Re-check if you add new URLs later.
"""

CANDIDATE_URLS = {
    "ing": [
        ("https://www.ing.be/fr/particuliers/epargner/compte-epargne-jeune", "youth savings account (FR)"),
        ("https://www.ing.be/fr/particuliers/epargner/comparatif-compte-epargne-jeune", "youth savings comparison (FR)"),
        ("https://www.ing.be/fr/particuliers/jeunes", "youth hub page (FR)"),
        ("https://www.ing.be/fr/particuliers/cartes-de-credit/carte-de-credit-jeunes", "youth credit card (FR)"),
        ("https://www.ing.be/fr/particuliers/gerer-le-quotidien/turning18_forparents", "turning 18 — for parents (FR)"),
        ("https://www.ing.be/fr/particuliers/epargner/compte-epargne-automatique-jeune", "automatic youth savings (FR)"),
        # NOTE: the 4 EN equivalents (youth, youth-savings-account,
        # compare-savings-accounts-youth, credit-card-youth) were dropped —
        # same content as the FR pages above, just translated. Keeping both
        # would inflate ING's page count vs. the other banks (FR-only) with
        # near-identical layout/visual features, not genuinely distinct
        # data points. See conversation notes, 2026-09-15.
    ],

    "bnp_fortis": [
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes", "youth hub page"),
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/comptes-bancaires/compte-a-vue/compte-jeune", "youth current account"),
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/jeune-travailleur", "young worker hub"),
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/jeune-travailleur/premier-logement", "young worker — first home"),
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/argent-de-poche", "pocket money"),
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/budget-enfant", "child budget"),
        ("https://www.bnpparibasfortis.be/fr/public/particuliers/banque-au-quotidien/banque-pour-les-jeunes/etudiant", "student page"),
        ("https://www.bnpparibasfortis.be/en/public/individuals/save-and-invest/insurance-investments/junior-future-plan", "Junior Future Plan — youth investment product"),
        ("https://www.bnpparibasfortis.be/fr/public/article/etudier-a-l-etranger-moyen-de-paiement", "studying abroad — payment method"),
        # NOTE: this bank's WAF served a fake "maintenance" page to every
        # automated request during testing (2026-09-15) despite robots.txt
        # allowing these paths and the pages working fine in a normal
        # browser. If that recurs, document BNP Fortis as manually
        # collected (screenshots/text captured by hand) rather than via
        # this pipeline — see conversation notes.
    ],

    "kbc": [
        # NOTE: carte-credit-etudiants.html removed — KBC restructured their
        # site and now redirects it to compte-jeunes.html, where the student
        # prepaid card content is folded in (confirmed via search + a
        # Playwright redirect check on 2026-09-15). Was a duplicate, not a
        # scraper bug.
        ("https://www.kbcbrussels.be/particuliers/fr/produits/paiements/comptes-a-vue/compte-jeunes.html", "youth current account (includes student prepaid card info)"),
        ("https://www.kbcbrussels.be/particuliers/fr/jeunes/18-ans.html", "turning 18 hub"),
        ("https://www.kbcbrussels.be/particuliers/fr/jeunes/18-ans/digitaal.htm", "turning 18 — digital banking"),
        ("https://www.kbcbrussels.be/particuliers/fr/jeunes/etudier-a-l-etranger.html", "studying abroad"),
        ("https://www.kbcbrussels.be/particuliers/fr/jeunes/changer-de-compte.html", "switching accounts (youth)"),
        ("https://www.kbcbrussels.be/particuliers/fr/jeunes/conseils-recevoir-argent-de-poche.html", "pocket money — receiving"),
        ("https://www.kbcbrussels.be/particuliers/fr/placements/investir-pour-les-jeunes.html", "investing for young people"),
    ],

    "belfius": [
        ("https://www.belfius.be/site/retail/fr/produits/paiement/compte-bancaire-pour-jeunes", "youth current account hub"),
        ("https://www.belfius.be/site/retail/fr/produits/paiement/compte-bancaire/beats-star", "Beats Star — youth-branded account"),
        ("https://www.belfius.be/site/retail/fr/produits/paiement/carte-de-credit-et-prepayee/mastercard-star", "Star Mastercard — youth-branded card"),
        # NOTE: only 3 pages found via the two retail sitemaps
        # (retail/fr/googlesitemap.xml had none relevant; site/retail/fr/
        # sitemap.xml had these 3). Belfius's sitemap coverage for youth
        # content appears thinner than the other banks — document this as
        # a known scope limitation rather than assuming more pages exist
        # but weren't found.
    ],

    "revolut": [
        ("https://www.revolut.com/revolut-kids-teens/", "Kids & Teens product hub"),
        ("https://www.revolut.com/revolut-kids-and-teens-parent-and-guardians/", "Kids & Teens — for parents/guardians"),
        ("https://www.revolut.com/revolut-for-ages-16-17/", "16-17 account"),
        ("https://www.revolut.com/kids-teens/referrals/", "Kids & Teens referral page"),
        ("https://www.revolut.com/fr-BE/", "Belgium homepage — general positioning, no dedicated youth segment found (documented scope decision, see brief's 'justify your scope')"),
    ],
}


def get_urls(bank: str) -> list[str]:
    """Return just the URL strings for a bank, dropping the notes."""
    return [url for url, _note in CANDIDATE_URLS.get(bank, [])]