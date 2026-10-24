import requests
import time
import json
import re
import random

API_URL = "https://ro.wikisource.org/w/api.php"

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "readabilityRomanian/1.0 "
        "(Romanian text research project; contact: your-email@example.com)"
    ),
    "Accept-Encoding": "gzip",
})


class ParagraphFetcher:

    def __init__(self):
        self.subcategories = []
        self.works = {}

        self.subcategories = json.load(open('categories.json', 'r'))
        for subcat in self.subcategories:
            if subcat['keep'] == 0:
                self.subcategories.remove(subcat)
        self.works = json.load(open('works.json', 'r', encoding="utf-8"))
        # self.get_subcategories("Genul epic")

        # for item in self.subcategories:
        #     self.get_works(item["title"])

    def normalize_category(self, category):
        if not category.startswith("Categorie:"):
            category = f"Categorie:{category}"

        return category

    def get_category_members(self, category, member_type=None):

        category = self.normalize_category(category)

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "max",
            "format": "json",
            "maxlag": "5",
        }

        if member_type:
            params["cmtype"] = member_type

        results = []

        while True:

            response = session.get(
                API_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                if retry_after is not None:
                    wait_time = float(retry_after)
                else:
                    wait_time = 5

                print(
                    f"Rate limited. Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            response.raise_for_status()

            data = response.json()

            if "error" in data:

                error_code = data["error"].get("code")

                if error_code == "maxlag":
                    print("Wiki server is busy. Waiting 5 seconds...")
                    time.sleep(5)
                    continue

                raise RuntimeError(data["error"])

            results.extend(
                data["query"]["categorymembers"]
            )

            if "continue" not in data:
                break

            params.update(data["continue"])

            time.sleep(0.5)

        return results

    def get_work_metadata(self, work):

        params = {
            "action": "query",
            "pageids": work["pageid"],
            "prop": "info|categories",
            "inprop": "url",
            "cllimit": "max",
            "format": "json",
            "maxlag": "5",
        }

        while True:

            response = session.get(
                API_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                if retry_after is not None:
                    wait_time = float(retry_after)
                else:
                    wait_time = 5

                print(
                    f"Rate limited while fetching metadata. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)

                continue

            response.raise_for_status()

            data = response.json()

            if "error" in data:

                error_code = data["error"].get("code")

                if error_code == "maxlag":
                    print(
                        "Wiki server is busy. Waiting 5 seconds..."
                    )
                    time.sleep(5)
                    continue

                raise RuntimeError(data["error"])

            pages = data["query"]["pages"]

            page = next(iter(pages.values()))

            metadata = {
                "pageid": page.get("pageid"),
                "title": page.get("title"),
                "length": page.get("length"),
                "touched": page.get("touched"),
                "lastrevid": page.get("lastrevid"),
                "url": page.get("fullurl"),
                "categories": [
                    category["title"]
                    for category in page.get("categories", [])
                ]
            }

            return metadata

    def inspect_category(self, category):

        print(f"\n=== {category} ===")

        members = self.get_category_members(category)

        subcategories = [
            item
            for item in members
            if item["ns"] == 14
        ]

        pages = [
            item
            for item in members
            if item["ns"] == 0
        ]

        print(
            f"\nSubcategories ({len(subcategories)}):"
        )

        for item in subcategories:
            print(f"  [C] {item['title']}")

        print(
            f"\nPages ({len(pages)}):"
        )

        for item in pages:
            print(f"  [P] {item['title']}")

        return subcategories, pages

    def get_subcategories(self, cat_name):

        members = self.get_category_members(cat_name)

        self.subcategories = [
            item
            for item in members
            if item["ns"] == 14
        ]

        if len(self.subcategories) == 0:
            print(
                f"No subcategories found for category {cat_name}"
            )
        else:
            print(
                f"{len(self.subcategories)} "
                f"subcategories found for category {cat_name}"
            )

    def get_works(self, subcat_name):

        members = self.get_category_members(subcat_name)

        pages = [
            item
            for item in members
            if item["ns"] == 0
        ]

        if len(pages) == 0:
            print(
                f"No works found for category {subcat_name}"
            )
        else:

            print(
                f"{len(pages)} works found for category {subcat_name}"
            )

            for work in pages:
            #
            #     print(
            #         f"Fetching metadata: {work['title']}"
            #     )
            #
            #     metadata = self.get_work_metadata(work)
            #
            #     work["metadata"] = metadata
            #
                work['category'] = subcat_name.split(":")[-1]
                self.works[work['pageid']] = work

        time.sleep(1)

    def get_random_paragraph(self, work):

        pageid = work["pageid"]

        params = {
            "action": "query",
            "prop": "revisions",
            "pageids": pageid,
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
            "maxlag": "5",
        }

        # ---------------------------------------------------------
        # Fetch page
        # ---------------------------------------------------------

        while True:
            response = session.get(
                API_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = float(retry_after) if retry_after else 5

                print(
                    f"Rate limited. Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error_code = data["error"].get("code")

                if error_code == "maxlag":
                    print(
                        "Wiki server is busy. Waiting 5 seconds..."
                    )
                    time.sleep(5)
                    continue

                raise RuntimeError(data["error"])

            break

        # ---------------------------------------------------------
        # Extract wikitext
        # ---------------------------------------------------------

        pages = data.get("query", {}).get("pages", {})
        page = pages.get(str(pageid))

        if not page or "revisions" not in page:
            return None

        wikitext = (
            page["revisions"][0]
            ["slots"]["main"]["*"]
        )

        # ---------------------------------------------------------
        # Split into candidate paragraphs
        # ---------------------------------------------------------

        raw_paragraphs = re.split(
            r"\n\s*\n",
            wikitext
        )

        candidates = []

        for paragraph in raw_paragraphs:

            original = paragraph.strip()

            if not original:
                continue

            # -----------------------------------------------------
            # Reject obvious non-prose blocks
            # -----------------------------------------------------

            # Headings
            if re.match(r"^\s*=+.*=+\s*$", original):
                continue

            # Templates
            if "{{" in original or "}}" in original:
                continue

            # Tables
            if (
                    original.startswith("{|")
                    or original.startswith("|")
                    or original.startswith("! ")
                    or original.startswith("|}")
            ):
                continue

            # Categories
            if "[[Categorie:" in original:
                continue

            # Files / images
            if re.search(
                    r"\[\[(?:Fișier|File|Imagine):",
                    original,
                    re.IGNORECASE
            ):
                continue

            # References / footnotes
            if re.search(
                    r"<ref\b|</ref>|<references\b",
                    original,
                    re.IGNORECASE
            ):
                continue

            # HTML blocks
            if re.search(
                    r"<(?:div|table|center|poem|blockquote|nowiki)\b",
                    original,
                    re.IGNORECASE
            ):
                continue

            # Horizontal separators
            if re.match(r"^\s*----+\s*$", original):
                continue

            # -----------------------------------------------------
            # Reject lists
            # -----------------------------------------------------

            lines = [
                line.strip()
                for line in original.splitlines()
                if line.strip()
            ]

            if not lines:
                continue

            list_lines = 0

            for line in lines:
                if re.match(
                        r"^(?:[*#;:]|\d+[.)])\s+",
                        line
                ):
                    list_lines += 1

            if list_lines > 0:
                continue

            # -----------------------------------------------------
            # Reject likely poetry
            # -----------------------------------------------------

            # Poetry tends to have many short lines.
            if len(lines) >= 3:

                short_lines = sum(
                    len(line.split()) <= 8
                    for line in lines
                )

                if short_lines / len(lines) >= 0.6:
                    continue

            # -----------------------------------------------------
            # Convert basic wiki markup
            # -----------------------------------------------------

            text = original

            # Internal links:
            # [[target|display text]] -> display text
            text = re.sub(
                r"\[\[([^\]|]+)\|([^\]]+)\]\]",
                r"\2",
                text
            )

            # [[target]] -> target
            text = re.sub(
                r"\[\[([^\]]+)\]\]",
                r"\1",
                text
            )

            # External links:
            # [https://example.com text] -> text
            text = re.sub(
                r"\[https?://[^\s\]]+\s+([^\]]+)\]",
                r"\1",
                text
            )

            # Remove bare external links
            text = re.sub(
                r"\[https?://[^\]]+\]",
                "",
                text
            )

            # Bold / italic
            text = re.sub(
                r"'{2,5}",
                "",
                text
            )

            # HTML tags
            text = re.sub(
                r"<[^>]+>",
                "",
                text
            )

            # HTML entities
            text = text.replace("&nbsp;", " ")
            text = text.replace("&amp;", "&")
            text = text.replace("&quot;", '"')
            text = text.replace("&lt;", "<")
            text = text.replace("&gt;", ">")

            text = re.sub(
                r"<!--.*?-->",
                "",
                text,
                flags=re.DOTALL
            )

            text = re.sub(
                r"\{\{.*?\}\}",
                "",
                text,
                flags=re.DOTALL
            )

            text = re.sub(
                r"\s+",
                " ",
                text
            ).strip()

            if not text:
                continue


            words = text.split()

            # Too short to be a useful narrative paragraph
            if len(words) < 30:
                continue

            if len(words) > 150:
                continue

            sentence_endings = re.findall(
                r"[.!?…](?:[\"»”']+)?",
                text
            )

            if len(sentence_endings) == 0:
                continue


            # Reject text with an unusually high proportion of
            # symbols / markup remnants.
            alphanumeric_chars = sum(
                char.isalnum()
                for char in text
            )

            if len(text) == 0:
                continue

            alpha_ratio = (
                    alphanumeric_chars / len(text)
            )

            if alpha_ratio < 0.65:
                continue

            # Reject paragraphs containing obvious metadata

            metadata_patterns = [
                r"\bISBN\b",
                r"\bISSN\b",
                r"\beditura\b",
                r"\bediția\b",
                r"\bediție\b",
                r"\bvolumul\b",
                r"\bvol\.\b",
                r"\bcapitolul\b.*\d+",
                r"\bpagina\b.*\d+",
                r"\btraducere de\b",
                r"\btipărit la\b",
                r"\bimprimat la\b",
            ]

            metadata_found = False

            for pattern in metadata_patterns:
                if re.search(
                        pattern,
                        text,
                        re.IGNORECASE
                ):
                    metadata_found = True
                    break

            if metadata_found:
                continue

            # Reject paragraphs dominated by uppercase text

            letters = [
                char
                for char in text
                if char.isalpha()
            ]

            if letters:

                uppercase_ratio = sum(
                    char.isupper()
                    for char in letters
                ) / len(letters)

                if (
                        uppercase_ratio > 0.70
                        and len(letters) > 20
                ):
                    continue

            candidates.append(text)

        # Return random candidate
        if not candidates:
            return None

        return {
            "title": work["title"],
            "author": work.get("author"),
            "publication_year": work.get("publication_year"),
            "paragraph": random.choice(candidates)
        }

    def pick_at_random(self, nr_choices):
        # for i in range(nr_choices):
        #     work_id = random.choice(list(self.works.keys()))
        #     paragraph = self.get_random_paragraph(self.works[work_id])
        paragraph_list = []
        total_paragraphs = len(self.works) * nr_choices
        ctr = 0
        for work_id in self.works:
            selected_paragraphs = set([])
            for choice in range(nr_choices):
                paragraph = self.get_random_paragraph(self.works[work_id])
                if paragraph is not None:
                    prev_len = len(selected_paragraphs)
                    selected_paragraphs.add(paragraph['paragraph'])
                    if len(selected_paragraphs) != prev_len:
                        paragraph_list.append(paragraph)
                ctr += 1
                print(str(ctr) + " / " + str(total_paragraphs) + " done")
        with open('paragraphs.json', 'w', encoding='utf-8') as f:
            json.dump(paragraph_list, f)

    def print_works(self):

        for id in self.works.keys():
            print(self.works[id])

        print(f"\nTotal works: {len(self.works)}")
        with open('works.json', 'w') as f:
            json.dump(self.works, f)

    def print_categories(self):

        for category in self.subcategories:
            print(category)
        print(f"\nTotal categories: {len(self.subcategories)}")
        with open('categories.json', 'w') as f:
            json.dump(self.subcategories, f)

pf = ParagraphFetcher()
pf.pick_at_random(4)