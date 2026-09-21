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

All URLs below were part of the manually curated research inventory.
The original entries were checked against each bank's robots.txt as of
2026-09-15 (see robots_checker.py). Newly added URLs should be re-checked
against robots.txt before running the scraper. Entries marked [CHECK]
were not treated as fully verified Belgian/localised pages.

UPDATE 2026-09-18: ING's robots.txt (https://www.ing.be/robots.txt) only
disallows "/video" — every ING/ing_adult URL below is allowed. Cross-checked
all "ing" URLs against https://www.ing.be/sitemap-cms.xml: 15 of 16 matched
verbatim. The one exception, ing-plus-deals, is NOT in the sitemap but is
live with a self-referencing canonical (fetched directly to confirm) — kept,
flagged as live-but-unlisted rather than treated as a scraper bug. Added 5
new ING entries below to close a real gap: ING previously had no under-18
current/youth account (compte-jeune / ING Go To 18), which every other bank
in the "10-24 free account" comparison set (KBC, CBC, Crelan, vdk, Beobank,
Belfius) already has. Also note: sitemap lastmod on
comparatif-compte-epargne-jeune, compte-epargne-automatique-jeune and
compte-epargne-classique shows 2026-09-16, i.e. AFTER the 2026-09-15
verification pass — content on those three pages should be re-scraped
before being treated as current, even though the URLs themselves are stable.
"""


# Suggested downstream tags (not sent to the LLM):
# YOUTH_ACCOUNT, STUDENT_ACCOUNT, FREE_ACCOUNT, CURRENT_ACCOUNT,
# DEBIT_CARD, CREDIT_CARD, SAVINGS, INVESTING, ETF_STOCKS,
# CASHBACK_REWARDS, REFERRAL, STUDENT_PROMOTION, WELCOME_BONUS,
# TRAVEL, ERASMUS, STUDENT_JOB, FIRST_SALARY, FIRST_HOME,
# PERSONAL_LOAN, MOBILE_APP, DIGITAL_ONBOARDING, FINANCIAL_EDUCATION,
# YOUTH_CONTENT, AGE_LIMIT, YOUTH_TO_ADULT_TRANSITION
#
# Research universe:
# Traditional/universal: ING, BNP Paribas Fortis, KBC, CBC, Belfius,
# Argenta, Beobank, Crelan, vdk, Europabank.
# Digital/challenger: Hello bank!, Revolut, N26, bunq, Nickel, Openbank,
# Trade Republic, Keytrade.
# Digital wealth/investing: MeDirect.

CANDIDATE_URLS = {
    "ing": [
        ("https://www.ing.be/fr/particuliers/epargner/compte-epargne-jeune", "youth savings account (FR)"),
        ("https://www.ing.be/fr/particuliers/epargner/comparatif-compte-epargne-jeune", "youth savings comparison (FR) — [RE-VERIFY] sitemap lastmod 2026-09-16, after original 09-15 check"),
        ("https://www.ing.be/fr/particuliers/jeunes", "youth hub page (FR)"),
        ("https://www.ing.be/fr/particuliers/cartes-de-credit/carte-de-credit-jeunes", "youth credit card (FR)"),
        ("https://www.ing.be/fr/particuliers/gerer-le-quotidien/turning18_forparents", "turning 18 — for parents (FR)"),
        ("https://www.ing.be/fr/particuliers/epargner/compte-epargne-automatique-jeune", "automatic youth savings (FR) — [RE-VERIFY] sitemap lastmod 2026-09-16, after original 09-15 check"),
        # --- 20-25 Subsidized Track ---
        ("https://www.ing.be/fr/particuliers/comptes-bancaire-packs/pack-go", "ING Go 18-25 — completely free daily banking entry-level tier"),
        ("https://www.ing.be/fr/particuliers/comptes-bancaire-packs/pack-more-jeunes", "ING More 18-25 — subsidized life-stage tier (includes Visa Classic + lifestyle perks like Amazon Prime)"),

        # --- 25-29 Transitional Track (The "Young Workers" Pivot) ---
        ("https://www.ing.be/fr/particuliers/comptes-bancaire-packs/comparez-packs", "Packs comparison engine — mapping the pricing cliff when youth eligibility expires at age 26"),
        ("https://www.ing.be/fr/particuliers/comptes-bancaire-packs/pack-more", "ING More (Standard Adult) — tracking conditional waiver requirements (e.g., lower monthly fee if €700+ is deposited monthly)"),
        ("https://www.ing.be/fr/particuliers/gerer-le-quotidien/ing-plus-deals", "ING+ Deals cashback engine — key positioning element used to retain price-sensitive young workers — [NOT IN SITEMAP but confirmed live 2026-09-18, self-referencing canonical; live-but-unlisted, not a scraper bug"),

        # --- Added 2026-09-18: closing the under-18 gap ---
        ("https://www.ing.be/fr/particuliers/comptes-bancaire-packs/compte-jeune", "ING Go To 18 — free youth current account + debit card, ages 8-17, €50 welcome offer (the under-18 entry product; direct comparator to KBC/CBC compte-jeunes). In sitemap, lastmod 2026-09-15."),
        ("https://www.ing.be/fr/particuliers/gerer-le-quotidien/carte-de-debit", "debit card — no ING page previously covered DEBIT_CARD. In sitemap, lastmod 2026-09-11."),
        ("https://www.ing.be/fr/particuliers/comptes-bancaire-packs/ouvrir-un-compte-bancaire-en-ligne", "digital onboarding — comparator to CBC ouvrir-compte-en-ligne. In sitemap, lastmod 2026-09-07."),
        ("https://www.ing.be/fr/particuliers/gerer-le-quotidien/mgm-inviter-ao", "member-get-member referral — REFERRAL tag otherwise only covered by Revolut. In sitemap, lastmod 2026-09-07."),
        ("https://www.ing.be/fr/particuliers/epargner/epargne-vers-propriete", "saving towards first home — comparator to BNP jeune-travailleur/premier-logement. In sitemap, lastmod 2026-09-07."),

        # NOTE: the 4 EN equivalents (youth, youth-savings-account,
        # compare-savings-accounts-youth, credit-card-youth) were dropped —
        # same content as the FR pages above, just translated. Keeping both
        # would inflate ING's page count vs. the other banks (FR-only) with
        # near-identical layout/visual features, not genuinely distinct
        # data points. See conversation notes, 2026-09-15.
    ],

    # ING-only: adult/general equivalents of the youth pages above, added to
    # compare how ING communicates to young people vs. general/adult
    # customers on the SAME product types (savings account, automatic
    # savings, credit card, comparison page, savings hub). Not present for
    # other banks — this is a within-ING comparison, separate from the
    # cross-bank youth comparison. turning18_forparents has no adult
    # equivalent by nature (life-stage specific).
    "ing_adult": [
        ("https://www.ing.be/fr/particuliers/epargner/compte-epargne-classique", "general savings account (mirrors compte-epargne-jeune) — [RE-VERIFY] sitemap lastmod 2026-09-16, after original 09-15 check"),
        ("https://www.ing.be/fr/particuliers/epargner/compte-epargne-automatique", "general automatic savings (mirrors compte-epargne-automatique-jeune)"),
        ("https://www.ing.be/fr/particuliers/cartes-de-credit/carte-de-credit-visa", "general Visa credit card (mirrors carte-de-credit-jeunes)"),
        ("https://www.ing.be/fr/particuliers/cartes-de-credit/comparatif-cartes-de-credit", "general credit card comparison (closest match to comparatif-compte-epargne-jeune)"),
        ("https://www.ing.be/fr/particuliers/epargner", "general savings hub (mirrors jeunes hub)"),
        # --- Added 2026-09-18 ---
        ("https://www.ing.be/fr/particuliers/investir/commencer-a-investir", "start investing — ING previously had no 'start investing' page vs. KBC/Hello bank! which both have one. In sitemap, lastmod 2026-09-10."),
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
        ("https://www.kbc.be/particuliers/fr/produits/paiements/comptes-a-vue/compte-jeunes.html", "[OK] youth account, free 10-24"),
        ("https://www.kbc.be/particuliers/fr/jeunes/18-ans.html", "[OK] turning 18"),
        ("https://www.kbc.be/particuliers/fr/campagne/compte-jeunes-action.html", "[OK] youth account acquisition campaign (powerbank incentive)"),
        ("https://www.kbc.be/particuliers/fr/jeunes.html", "[CHECK] youth hub — inferred from the CBC/KBC Brussels pattern"),

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
        ("https://www.revolut.com/en-BE/revolut-kids-and-teens-benefits/", "[OK] Kids & Teens BENEFITS — distinct page from the hub, kid-facing voice, 6-17 in BE"),
        ("https://www.revolut.com/fr-BE/revolut-kids-and-teens-benefits/", "[CHECK] FR equivalent of the above (fr-FR version confirmed live)"),
        ("https://www.revolut.com/fr-BE/kids-and-teens/kids-savings-account/", "[CHECK] Kids & Teens savings account — direct comparator to ING compte-epargne-jeune (fr-FR confirmed)"),
        ("https://www.revolut.com/fr-BE/u18-activation/", "[CHECK] parent-approval landing page — the 'my teen wants to join' funnel (fr-FR confirmed)"),
        ("https://www.revolut.com/revolut-under-18-benefits-parents-and-guardians/", "[OK] legacy under-18 parents page — still live, note it predates the Kids & Teens rename"),
        ("https://www.revolut.com/get-revolut-under-18", "[NAV] the conversion endpoint every youth-page CTA points to"),
        ("https://www.revolut.com/fr-BE/legal/revolut-under18/", "[CHECK] Kids & Teens T&Cs — the only place age gates, card fees and limits are stated precisely (en-FR/en-US confirmed)"),
        ("https://www.revolut.com/blog/post/revolut-under-18-the-account-built-for-teens/", "[OK] blog — launch positioning for the teen proposition, useful for tone analysis"),

    ],

    # --- Digital-only / free models -------------------------------------
   # Hello bank! is BNP Paribas Fortis' mobile brand. Keep it SEPARATE from
   # "bnp_fortis": different site, different tone, different age framing
   # (18-27 only, no minors offer on the BE site — unlike hellobank.fr,
   # which has Hello Origin for 12-17. Do not mix the two domains.)
   "hello_bank": [
       ("https://www.hellobank.be/fr/notre-offre/comptes-et-cartes/compte-courant-27y", "[OK] Hello4You — youth payment account, 18-27 (the core youth page)"),
       ("https://www.hellobank.be/fr/notre-offre/comptes-et-cartes/compte-all-in-gratuit", "[NAV] general all-in free account — adult equivalent of Hello4You"),
       ("https://www.hellobank.be/fr/notre-offre/comptes-et-cartes/carte-de-credit", "[NAV] Hello Visa credit card"),
       ("https://www.hellobank.be/fr/notre-offre/comptes-et-cartes/application-hello-bank", "[NAV] the app — main digital-first positioning page"),
       ("https://www.hellobank.be/fr/notre-offre/epargner-et-placer/compte-epargne-boost", "[NAV] Boost savings account"),
       ("https://www.hellobank.be/fr/notre-offre/epargner-et-placer/commencer-a-investir", "[NAV] investing for beginners — closest to KBC 'investir pour les jeunes'"),
       ("https://www.hellobank.be/fr/devenir-hello", "[NAV] onboarding / become a client"),
       ("https://www.hellobank.be/fr/infos-conseils", "[NAV] advice-article hub (age-neutral, useful for tone comparison)"),
       # NOTE: no turning-18 or parents page exists on the BE site. Hello4You
       # simply converts to a standard formula at 28 — that conversion is
       # described inside compte-courant-27y. Worth flagging in the brief:
       # Hello bank! BE has no minors proposition at all.
   ],
   "argenta": [
       ("https://www.argenta.be/fr/thema/les-jeunes.html", "[OK] youth hub page"),
       ("https://www.argenta.be/fr/thema/les-jeunes/les-parents/affaires-bancaires-au-quotidien-pour-votre-ado.html", "[OK] for parents — teen account + debit card from 11"),
       ("https://www.argenta.be/fr/formules/green.html", "[NAV] Formule Green — the free account used as the youth product"),
       ("https://www.argenta.be/fr/argenta-vous-informe/j-ai-18-ans-et-maintenant.html", "[NAV] turning 18 (equivalent of ING turning18 / KBC 18-ans)"),
       ("https://www.argenta.be/fr/argenta-vous-informe/que-devez-vous-savoir-en-tant-qu-etudiant-jobiste.html", "[OK] student jobs"),
       ("https://www.argenta.be/fr/argenta-vous-informe/10-conseils-destines-aux-jeunes-pour-economiser-de-l-argent.html", "[OK] 10 saving tips for young people"),
       ("https://www.argenta.be/fr/argenta-vous-informe/une-carte-bancaire-personnelle-pour-votre-enfant-a-partir-de-quel-age.html", "[NAV] at what age a child gets their own card"),
       ("https://www.argenta.be/fr/argenta-vous-informe/7-conseils-pour-apprendre-a-votre-enfant-a-epargner.html", "[NAV] teaching a child to save"),
       ("https://www.argenta.be/fr/thema/votre-famille-et-vous/que-devez-vous-regler-lors-d-une-naissance/ouvrir-un-compte-pour-votre-enfant.html", "[NAV] opening an account for your child"),
       ("https://www.argenta.be/fr/payer/banque-par-internet.html", "Argenta online/mobile web onboarding entry point"),
       ("https://www.argenta.be/nl/thema/jongeren.html", "Argenta core youth hub positioning page (Flemish baseline root)"),
   ],

   # --- Fintech / neo-banks --------------------------------------------
"n26": [
        ("https://n26.com/fr-be/moins-de-18-ans", "[OK] N26 under-18s — card for 7-17, parent-managed (the youth page) — verified live on fr-be"),
        ("https://n26.com/fr-be/compte-bancaire-gratuit", "[NAV] Standard — free account, the entry tier young adults land on"),
        ("https://n26.com/fr-be/compte-bancaire", "[NAV] Smart"),
        ("https://n26.com/fr-be/tarifs", "[NAV] plan comparison"),
        ("https://n26.com/fr-be/compte-epargne", "[NAV] savings"),
        ("https://n26.com/fr-be/actions-et-etfs", "[NAV] stocks & ETFs — youth-skewing investing pitch"),
        ("https://n26.com/fr-be/sitemap", "[NAV] sitemap — use this to confirm the full fr-be inventory"),
        ("https://n26.com/fr-fr/compte-bancaire-etudiant", "[OK-OTHER-MARKET] student account — live on fr-fr, no fr-be equivalent — reference only"),
        ("https://n26.com/fr-fr/indice-du-cout-des-etudes", "[OK-OTHER-MARKET] Education Price Index — youth/student cost-of-study content, no fr-be equivalent found in sitemap"),
        ("https://n26.com/de-de/taschengeld-und-finanzielle-bildung", "[OK-OTHER-MARKET] pocket money & financial education — youth-targeted content, DE only, no fr-be equivalent found in sitemap"),
        ("https://n26.com/en-fr/blog/how-to-open-a-bank-account-in-luxembourg", "[UNVERIFIED] N26 Cross-border / Expat student onboarding strategy reference"),
        ("https://n26.com/en-eu/iban-number", "[UNVERIFIED] N26 local/EU IBAN consumer education page"),
        ("https://n26.com/en-fr/blog/guide-to-eu-banking-acronyms", "[UNVERIFIED] N26 functional onboarding/literacy messaging guidelines"),
    ],

  
   "beobank": [
        ("https://www.beobank.be/fr/payer/comptes-courants/compte-jeunes.html", "Beobank youth current account — direct youth banking comparator"),
        ("https://www.beobank.be/fr/payer/cartes-de-credit/young-mastercard.html", "Young Mastercard — student/young adult credit proposition"),
        ("https://www.beobank.be/fr/payer/comptes-courants.html", "Beobank current accounts — adult equivalent / youth transition"),
        ("https://www.beobank.be/fr/payer/cartes-de-credit.html", "Beobank credit card portfolio — useful for young-adult credit comparison"),
        ("https://www.beobank.be/fr/epargner.html", "Beobank savings hub"),
        ("https://www.beobank.be/fr/investir.html", "Beobank investing hub — useful for young investor proposition"),
        ("https://www.beobank.be/fr/actualites.html", "Beobank campaigns/news — acquisition and promotional messaging"),
    ],
     
}


def get_urls(bank: str) -> list[str]:
    """Return just the URL strings for a bank, dropping the notes."""
    return [url for url, _note in CANDIDATE_URLS.get(bank, [])]
