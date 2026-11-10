"""District lookup must return the RIGHT restaurant's page.

Reproduces the reported bug: asking for SOCIAL in Connaught Place returned
Themis Barbecue House's offers, because every CP restaurant's URL ends in
'-connaught-place-new-delhi' and the old matcher counted those area words.
The fake District site below mirrors the real listing (checked on district.in):
Dr. Zombie and Themis are listed before Connaught Place SOCIAL.
"""
import asyncio

import httpx
import pytest

from app.services.llm_search.district_scraper import DistrictScraper
from app.services.llm_search.restaurant_match import name_matches, page_restaurant_name, split_query

BASE = "https://www.district.in"
RESTAURANTS = {
    "dr-zombie-connaught-place-new-delhi": ("Dr. Zombie", "FLAT 55% OFF"),
    "themis-barbecue-house-1-connaught-place-new-delhi": ("Themis Barbecue House", "FLAT 30% OFF"),
    "connaught-place-social-connaught-place-new-delhi": ("Connaught Place SOCIAL", "FLAT ₹175 OFF"),
    "saket-social-saket-new-delhi": ("Saket Social", "FLAT 20% OFF"),
    "drama-connaught-place-new-delhi": ("Drama", "FLAT 40% OFF"),
}


def page(name, offer):
    filler = "<div>" + ("x" * 3000) + "</div>"
    offers = '\\"allOffers\\":[{\\"offerTitle\\":\\"' + offer + '\\",\\"title\\":\\"on total bill\\"}],\\"bankOffers\\":[]'
    return (f"<html><head><title>{name} | Connaught Place, New Delhi | Book Table</title></head>"
            f"<body><h1>{name}</h1>{filler}<script>{offers}</script></body></html>")


def listing():
    links = "".join(f'<a href="/dining/ncr/{slug}">{name}</a><span>Connaught Place, New Delhi</span>'
                    for slug, (name, _) in RESTAURANTS.items())
    return f"<html><body>{links}</body></html>"


def make_scraper(redirect_unknown_to=None):
    requested = []

    def handler(request: httpx.Request):
        path = request.url.path
        requested.append(path)
        if path in ("/dining/ncr", "/dining/ncr/restaurants"):
            return httpx.Response(200, text=listing())
        slug = path.rsplit("/", 1)[-1]
        if slug in RESTAURANTS:
            return httpx.Response(200, text=page(*RESTAURANTS[slug]))
        if redirect_unknown_to:  # District serving some other restaurant for an unknown slug
            return httpx.Response(200, text=page(*RESTAURANTS[redirect_unknown_to]))
        return httpx.Response(404, text="not found")

    s = DistrictScraper()
    s._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    return s, requested


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


@pytest.mark.parametrize("restaurant,city", [
    ("Social", "Connaught Place"),
    ("Social", "Connaught Place, New Delhi"),
    ("Social Connaught Place", "Delhi"),
    ("Social, CP", "New Delhi"),
    ("CP Social", "Delhi"),
    ("Connaught Place Social", "New Delhi"),
    ("SOCIAL", "cp"),
])
def test_bug_social_cp_returns_social_not_themis(restaurant, city):
    scraper, _ = make_scraper()
    offers = run(scraper.get_offers(restaurant, city))
    assert offers, (restaurant, city)
    assert {o.matched_restaurant for o in offers} == {"Connaught Place SOCIAL"}
    assert any("175" in o.discount_text for o in offers)
    assert all("themis" not in (o.platform_url or "") for o in offers)


def test_area_words_alone_never_match():
    # Old matcher: "connaught" + "place" = 2/3 words -> first CP restaurant won
    name, loc = split_query("Social Connaught Place", "Delhi")
    assert name == ["social"] and {"connaught", "place"} <= loc
    assert not name_matches(name, "Themis Barbecue House")
    assert not name_matches(name, "Dr. Zombie")
    assert name_matches(name, "Connaught Place SOCIAL")


def test_wrong_page_is_rejected_even_if_url_guess_lands_on_it():
    # Restaurant not in listing; District serves Themis for any unknown slug
    scraper, _ = make_scraper(redirect_unknown_to="themis-barbecue-house-1-connaught-place-new-delhi")
    offers = run(scraper.get_offers("Ministry of Beer", "Connaught Place"))
    assert offers == []


def test_spelling_variant_and_other_restaurants_still_found():
    scraper, _ = make_scraper()
    offers = run(scraper.get_offers("Themis Barbeque House", "CP"))  # barbeque vs barbecue
    assert {o.matched_restaurant for o in offers} == {"Themis Barbecue House"}
    offers = run(scraper.get_offers("Dr Zombie", "Connaught Place, Delhi"))
    assert {o.matched_restaurant for o in offers} == {"Dr. Zombie"}


def test_right_outlet_of_a_chain_is_preferred_by_area():
    scraper, _ = make_scraper()
    offers = run(scraper.get_offers("Social", "Saket, New Delhi"))
    assert {o.matched_restaurant for o in offers} == {"Saket Social"}


def test_page_name_comes_from_title():
    html = "<title>Drama | Connaught Place, New Delhi | Book Table</title>"
    assert page_restaurant_name(html) == "Drama"
