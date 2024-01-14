import random
from bs4 import BeautifulSoup as bs
from pathlib import Path
import json
import requests
from tqdm import tqdm
from newspaper.urls import get_domain, urljoin_if_valid
import newspaper


newssites = Path("newspaper/resources/misc/popular_sources.txt").read_text().split("\n")

results = {}

for site in tqdm(newssites):
    if len(site) < 3:
        continue
    if not (site.startswith("http://") or site.startswith("https://")):
        site = "http://" + site

    nr_err = 0
    while True:
        try:
            result = requests.get(site, timeout=(5, 10))
            break
        except Exception as e:
            nr_err += 1
            if nr_err > 3:
                print(f"Url {site} Error: {e}")
                break
            continue

    if result.status_code != 200:
        results[site] = f"Error {result.status_code} in {site}. Html: {result.text}"
        continue

    soup = bs(result.content, "html.parser")
    links = soup.find_all("a")
    links = [link.get("href") for link in links]
    links = [link.lower() for link in links if link is not None]
    links = [
        link if link.startswith("http") else urljoin_if_valid(site, link)
        for link in links
    ]
    links = [link for link in links if get_domain(link) == get_domain(site)]
    links_ = [link for link in links if abs(len(link) - len(site)) > 20]
    if len(links_) > 3:
        links = links_

    links = list(set(links))

    for link in random.sample(links, min(5, len(links))):
        try:
            article = newspaper.article(link)
            results[link] = {
                "title": article.title,
                "authors": article.authors,
                "publish_date": article.publish_date,
                "top_image": article.top_image,
                "tags": article.tags,
                "text": article.text,
            }
        except Exception as e:
            results[link] = f"Error: {str(e)}  url: {link}"

    json.dump(
        results,
        open("tests/localdebug/results.json", "w", encoding="utf-8"),
        indent=4,
        ensure_ascii=False,
        default=str,
    )
