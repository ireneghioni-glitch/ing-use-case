from urllib.parse import urlparse

# Strict age/segment matching anchors
YOUTH_TARGET_GROUPS = {
    "YOUTH_ACCOUNT": [
        "compte-jeune", "compte-jeunes", "comptejeune", "youth-account",
        "youth", "jeunes", "jeune", "jongeren", "jong",
        "hello4you", "beats-new", "18-25", "under-18"
    ],
    "STUDENT_ACCOUNT": [
        "student", "studenten", "etudiant", "étudiant", "etudiants", "étudiants"
    ]
}

PRODUCT_CATEGORIES = {
    "CURRENT_ACCOUNT": ["compte-a-vue", "compte-courant", "current-account", "bank-account"],
    "SAVINGS": ["epargne", "épargne", "savings", "saving", "spaar"],
    "INVESTING": ["investir", "investissement", "investing", "placement", "actions", "etf"],
    "DEBIT_CARD": ["carte-de-debit", "carte-debit", "debit-card"],
    "CREDIT_CARD": ["carte-de-credit", "carte-credit", "credit-card"],
    "REFERRAL": ["referral", "referrals", "parrainage", "inviter", "invite"],
    "TRAVEL": ["travel", "voyage", "voyager", "etranger", "étranger", "abroad"],
    "FINANCIAL_EDUCATION": ["conseils", "conseil", "tips", "guide", "education", "apprendre"]
}


def classify_url(url: str) -> list[str]:
    """Return all matching category tags for a given URL."""
    path = urlparse(url).path.lower()
    tags = []

    # Check Core Youth/Student categories
    for tag, keywords in YOUTH_TARGET_GROUPS.items():
        if any(keyword in path for keyword in keywords):
            tags.append(tag)

    # Check generic product rules
    for tag, keywords in PRODUCT_CATEGORIES.items():
        if any(keyword in path for keyword in keywords):
            tags.append(tag)

    return tags


def is_relevant(url: str) -> bool:
    """
    Returns True only if the URL's path actually targets Youth/Students.
    """
    path = urlparse(url).path.lower()

    return any(
        keyword in path
        for keywords in YOUTH_TARGET_GROUPS.values()
        for keyword in keywords
    )


def create_note(url: str) -> str:
    path = urlparse(url).path
    if not path or path == "/":
        return "homepage"

    last_part = path.rstrip("/").split("/")[-1]

    # Clean out technical document suffixes
    for extension in [".html", ".htm", ".php", ".xml"]:
        if last_part.endswith(extension):
            last_part = last_part[:-len(extension)]

    return last_part.replace("-", " ").replace("_", " ")
