"""Scrape diagram images from Art of Problem Solving wiki for problems marked [Diagram]."""

import json
import os
import re
import time
import urllib.request
from html.parser import HTMLParser

PROBLEMS_PATH = os.path.join(os.path.dirname(__file__), 'amc', 'json')
IMAGES_PATH = os.path.join(os.path.dirname(__file__), 'static', 'images')
AOPS_BASE = 'https://artofproblemsolving.com/wiki/index.php'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


class DiagramParser(HTMLParser):
    """Extract diagram image URLs from an HTML snippet."""
    def __init__(self):
        super().__init__()
        self.diagrams = []

    def handle_starttag(self, tag, attrs):
        if tag != 'img':
            return
        d = dict(attrs)
        cls = d.get('class', '')
        alt = d.get('alt', '')
        src = d.get('src', '')

        # Skip logos and UI images
        if 'Logo' in src or 'logo' in src or 'assets/' in src:
            return

        is_diagram = False
        # Asymptote diagrams: class latexcenter or alt starts with [asy]
        if 'latexcenter' in cls or alt.strip().startswith('[asy]'):
            is_diagram = True
        # Uploaded wiki images
        elif 'mw-file-element' in cls:
            is_diagram = True

        if is_diagram:
            if src.startswith('//'):
                src = 'https:' + src
            self.diagrams.append(src)


def build_url(contest, year, variant, number):
    if contest == 'AIME':
        return f"{AOPS_BASE}/{year}_AIME_{variant}_Problems/Problem_{number}"
    elif contest == 'AMC 10':
        return f"{AOPS_BASE}/{year}_AMC_10{variant}_Problems/Problem_{number}"
    elif contest == 'AMC 12':
        return f"{AOPS_BASE}/{year}_AMC_12{variant}_Problems/Problem_{number}"
    return None


def fetch_page(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"FETCH ERROR: {e}")
        return None


def download_image(img_url, dest_path):
    req = urllib.request.Request(img_url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(dest_path, 'wb') as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"DOWNLOAD ERROR: {e}")
        return False


def extract_problem_section(html):
    """Extract only the problem section from the page (between Problem and Solution headings)."""
    m = re.search(r'<h2>.*?[Pp]roblem.*?</h2>(.*?)<h2>', html, re.DOTALL)
    return m.group(1) if m else None


def main():
    os.makedirs(IMAGES_PATH, exist_ok=True)

    total = 0
    found = 0
    no_diagram = 0
    failed = 0

    for fname in sorted(os.listdir(PROBLEMS_PATH)):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(PROBLEMS_PATH, fname)
        with open(fpath, 'r') as f:
            data = json.load(f)

        contest = data.get('contest', '')
        year = data.get('year', '')
        modified = False

        for variant in data['variants']:
            for problem in data['variants'][variant]:
                if '[Diagram]' not in problem['problem']:
                    continue

                total += 1
                num = problem['number']
                safe_contest = contest.replace(' ', '')
                img_base = f"{safe_contest}_{year}_{variant}_{num}"
                label = f"{contest} {year} {variant} #{num}"

                url = build_url(contest, year, variant, num)
                if not url:
                    print(f"[{total}] {label} - SKIP unknown contest")
                    failed += 1
                    continue

                print(f"[{total}] {label} ...", end=' ', flush=True)

                html = fetch_page(url)
                if not html:
                    failed += 1
                    continue

                section = extract_problem_section(html)
                if not section:
                    print("no problem section found")
                    failed += 1
                    continue

                parser = DiagramParser()
                parser.feed(section)

                if not parser.diagrams:
                    # No diagram on AOPS either — remove placeholder
                    problem['problem'] = problem['problem'].replace(' [Diagram]', '').replace('[Diagram]', '')
                    modified = True
                    no_diagram += 1
                    print("no diagram on AOPS, removed placeholder")
                    time.sleep(0.3)
                    continue

                img_tags = []
                for i, diagram_url in enumerate(parser.diagrams):
                    suffix = f"_{i}" if len(parser.diagrams) > 1 else ""
                    img_fname = f"{img_base}{suffix}.png"
                    img_path = os.path.join(IMAGES_PATH, img_fname)

                    if os.path.exists(img_path):
                        ok = True
                    else:
                        ok = download_image(diagram_url, img_path)

                    if ok:
                        img_tags.append(f'[IMG:{img_fname}]')

                if img_tags:
                    replacement = ' '.join(img_tags)
                    problem['problem'] = problem['problem'].replace('[Diagram]', replacement)
                    modified = True
                    found += 1
                    print(f"OK ({len(img_tags)} image(s))")
                else:
                    failed += 1
                    print("download failed")

                time.sleep(0.3)

        if modified:
            with open(fpath, 'w') as f:
                json.dump(data, f, indent=2)

    print(f"\nDone: {found} scraped, {no_diagram} no diagram on AOPS, {failed} failed, {total} total")


if __name__ == '__main__':
    main()
