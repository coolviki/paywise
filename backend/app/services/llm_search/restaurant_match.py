"""Restaurant-name matching used to find the RIGHT restaurant page on District.

Bug this fixes: the old matcher counted any query word appearing anywhere in a
link's text or URL. District URLs end in the locality ("...-connaught-place-new-delhi"),
so a query like "Social Connaught Place" matched every CP restaurant on the words
"connaught" + "place", and the first one listed (e.g. Themis Barbecue House) won.

Rules now:
  * The query is split into NAME tokens and LOCATION tokens. Only name tokens
    decide whether a candidate is the restaurant; location tokens only rank
    between genuine name matches (e.g. two outlets of the same chain).
  * Every distinctive name token must appear in the candidate's NAME (link text
    or page title) - never just in its address/URL locality.
  * After fetching, the page's own title is checked the same way, so a wrong
    page is rejected even if it was reached by URL guessing or a redirect.
"""
import re
from difflib import SequenceMatcher
from typing import Iterable, List, Optional, Set, Tuple

# Multi-word localities / cities. Matched as whole phrases, longest first.
LOCATION_PHRASES = [
    # NCR
    "connaught place", "rajiv chowk", "janpath", "khan market", "hauz khas village", "hauz khas",
    "defence colony", "greater kailash", "vasant kunj", "vasant vihar", "nehru place", "saket",
    "select citywalk", "aerocity", "chanakyapuri", "lodhi colony", "south extension", "rajouri garden",
    "netaji subhash place", "punjabi bagh", "dlf cyber hub", "dlf cyber city", "cyber hub", "cyberhub",
    "cyber city", "golf course road", "sohna road", "mg road", "dlf phase", "sector",
    "new delhi", "delhi ncr", "delhi", "ncr", "gurgaon", "gurugram", "noida", "greater noida", "faridabad",
    # Mumbai
    "lower parel", "bandra west", "bandra", "andheri west", "andheri", "juhu", "worli", "colaba",
    "powai", "goregaon", "malad", "kala ghoda", "bkc", "mumbai",
    # Bangalore
    "indiranagar", "koramangala", "whitefield", "brigade road", "jp nagar", "hsr layout",
    "ub city", "church street", "bangalore", "bengaluru",
    # Other cities
    "hyderabad", "chennai", "pune", "kolkata", "ahmedabad", "jaipur", "chandigarh",
    "india",
]
LOCATION_ABBREVIATIONS = {
    "cp": "connaught place", "gk": "greater kailash", "hkv": "hauz khas village",
    "ggn": "gurgaon", "bkc": "bkc",
}
# Words that don't identify a restaurant on their own
FILLER = {"the", "and", "restaurant", "restaurants", "restro", "outlet", "branch", "at", "in", "near",
          "bar", "kitchen", "cafe", "of", "by"}
# Spelling variants that should count as the same word
SYNONYMS = {"barbeque": "barbecue", "bbq": "barbecue", "café": "cafe", "n": "and"}


def tokens(text: Optional[str]) -> List[str]:
    if not text:
        return []
    t = text.lower().replace("&", " and ").replace("'", "").replace("’", "")
    t = re.sub(r"[^a-z0-9À-ɏ]+", " ", t)
    return [SYNONYMS.get(w, w) for w in t.split()]


def split_query(restaurant: str, city: str = "") -> Tuple[List[str], Set[str]]:
    """Return (name_tokens, location_tokens) for a user's restaurant query."""
    text = " " + " ".join(tokens(restaurant)) + " "
    loc: Set[str] = set()
    for abbr, full in LOCATION_ABBREVIATIONS.items():
        if f" {abbr} " in text:
            text = text.replace(f" {abbr} ", " ")
            loc.update(full.split())
    for phrase in sorted(LOCATION_PHRASES, key=len, reverse=True):
        p = f" {phrase} "
        while p in text:
            text = text.replace(p, " ")
            loc.update(phrase.split())
    # "sector 29" -> drop the number too
    text = re.sub(r"(?<= )\d{1,3}(?= )", " ", text) if "sector" in loc else text
    name = [w for w in text.split() if w]
    if not name:  # the whole query was location words: fall back to all of it
        name = tokens(restaurant)
    for w in tokens(city):
        loc.update(LOCATION_ABBREVIATIONS.get(w, w).split())
    return name, loc


def _word_match(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 5 and len(b) >= 5:
        return SequenceMatcher(None, a, b).ratio() >= 0.85
    return False


def required_tokens(name_tokens: List[str]) -> List[str]:
    req = [w for w in name_tokens if w not in FILLER]
    return req or list(name_tokens)


def name_matches(name_tokens: List[str], candidate_name: Optional[str]) -> bool:
    """True if every distinctive query-name token appears in the candidate's name."""
    cand = tokens(candidate_name)
    if not cand:
        return False
    return all(any(_word_match(q, c) for c in cand) for q in required_tokens(name_tokens))


def score_candidate(name_tokens: List[str], loc_tokens: Iterable[str],
                    candidate_name: str, candidate_url: str = "") -> Optional[float]:
    """None if not the restaurant; otherwise higher = better (closer name, matching area)."""
    if not name_matches(name_tokens, candidate_name):
        return None
    cand = set(tokens(candidate_name))
    req = set(required_tokens(name_tokens))
    extra = len(cand - req)                       # fewer unexplained words = closer name
    url_words = set(tokens(candidate_url.rsplit("/", 1)[-1].replace("-", " ")))
    loc_hits = len(set(loc_tokens) & url_words)   # right outlet / area
    return 10.0 * loc_hits - extra


def page_restaurant_name(html: str) -> Optional[str]:
    """Restaurant name as District's page states it (title is 'Name | Area, City | Book Table')."""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
        name = title.split("|")[0].strip()
        if name and name.lower() not in ("district", "dining"):
            return name
    m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', html, re.IGNORECASE)
    if m:
        return m.group(1).split("|")[0].strip()
    m = re.search(r'"@type"\s*:\s*"Restaurant"[^{}]*?"name"\s*:\s*"([^"]+)"', html)
    if m:
        return m.group(1)
    return None
