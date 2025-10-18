# match_fetcher: simple scraper-based match & results fetcher
# NOTE: This module uses requests + BeautifulSoup to scrape match results/jadval from public pages.
# Web scraping may break if site layout changes. Prefer official APIs for production.
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import os

logger = logging.getLogger(__name__)

USER_AGENT = os.getenv('USER_AGENT', 'realbot/1.0')

def fetch_realmadrid_latest_matches() -> List[Dict]:
    """
    Scrape the Real Madrid news page to find recent match reports or result lines.
    Returns list of dicts: [{'title': str, 'summary': str, 'link': str}]
    This is a simple best-effort scraper and may require adjustments.
    """
    url = 'https://www.realmadrid.com/en/news'
    headers = {'User-Agent': USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'lxml')
        results = []
        # Find article blocks (site structure may change)
        for article in soup.select('article')[:10]:
            a = article.find('a', href=True)
            title = article.get_text(strip=True)[:200]
            link = a['href'] if a else url
            if link and link.startswith('/'):
                link = 'https://www.realmadrid.com' + link
            summary_tag = article.find('p')
            summary = summary_tag.get_text(strip=True) if summary_tag else ''
            results.append({'title': title, 'summary': summary, 'link': link})
        return results
    except Exception as e:
        logger.exception('Error fetching RealMadrid matches: %s', e)
        return []

def fetch_from_site(url: str) -> List[Dict]:
    """
    Generic fetcher that scrapes simple article lists from a provided URL.
    Use for Marca/Goal/AS with caution — each site has different DOM structure.
    """
    headers = {'User-Agent': USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'lxml')
        items = []
        # Try several generic selectors
        selectors = ['article', '.news-item', '.news-list__item', '.Card']
        for sel in selectors:
            for node in soup.select(sel)[:8]:
                a = node.find('a', href=True)
                title = (node.get_text(strip=True)[:250]) if node else ''
                link = a['href'] if a else url
                if link and link.startswith('/'):
                    # heuristic for Marca/AS
                    if 'marca' in url:
                        link = 'https://e00-marca.uecdn.es' + link
                    elif 'as.com' in url:
                        link = 'https://as.com' + link
                    else:
                        link = link
                summary_tag = node.find('p') if node else None
                summary = summary_tag.get_text(strip=True) if summary_tag else ''
                items.append({'title': title, 'summary': summary, 'link': link})
            if items:
                break
        return items
    except Exception as e:
        logger.exception('Error fetching from site %s: %s', url, e)
        return []
