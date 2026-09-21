
from pathlib import Path

from marketing_spy.banks import BANKS


from marketing_spy.sitemap_discovery import (
    discover_bank_urls,
)

from marketing_spy.url_filter import (
    is_relevant,
    create_note,
)


OUTPUT_FILE = Path(
    "output/candidate_urls.py"
)


def generate_candidate_urls():

    all_candidates = {}

    for bank, domain in BANKS.items():

        print()
        print(
            f"Discovering URLs for {bank}"
        )

        urls = discover_bank_urls(
            bank=bank,
            domain=domain,
        )

        candidates = []

        for url in urls:

            if is_relevant(url):

                note = create_note(url)

                candidates.append(
                    (
                        url,
                        note,
                    )
                )

        all_candidates[bank] = (
            candidates
        )

        print(
            f"{bank}: "
            f"{len(urls)} total URLs → "
            f"{len(candidates)} candidates"
        )

    write_candidate_file(
        all_candidates
    )


def write_candidate_file(data):

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            '"""AUTO-GENERATED FILE.\n'
            'Do not manually edit this file.\n'
            'Generated from bank sitemaps.\n'
            '"""\n\n'
        )

        file.write(
            "CANDIDATE_URLS = {\n"
        )

        for bank, candidates in data.items():

            file.write(
                f'    "{bank}": [\n'
            )

            for url, note in candidates:

                file.write(
                    f"        "
                    f"({url!r}, {note!r}),\n"
                )

            file.write(
                "    ],\n"
            )

        file.write(
            "}\n\n"
        )

        file.write(
            "def get_urls(bank: str) -> list[str]:\n"
        )

        file.write(
            '    """Return URL strings for a bank."""\n'
        )

        file.write(
            "    return [\n"
            "        url\n"
            "        for url, _note in "
            "CANDIDATE_URLS.get(bank, [])\n"
            "    ]\n"
        )


if __name__ == "__main__":

    generate_candidate_urls()