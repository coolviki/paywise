"""Per-platform dine-out search with status reporting and retry.

Why this exists: the providers' `_search_parallel` merges per-platform results
and silently `continue`s past any platform whose search raised (rate limit,
timeout, bad JSON). A platform that failed then looks identical to one that has
no offers - e.g. EazyDiner vanishing from a combined search while a search for
EazyDiner alone finds 9 offers.

Here every platform is searched on its own, with its own timeout, retried once
when it errors / times out / comes back empty, and its outcome is reported.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .base import PLATFORM_INFO, Platform, RestaurantOffer

logger = logging.getLogger(__name__)

STATUS_OK = "ok"
STATUS_NO_OFFERS = "no_offers"
STATUS_TIMED_OUT = "timed_out"
STATUS_ERROR = "error"


@dataclass
class PlatformOutcome:
    platform: Platform
    status: str = STATUS_ERROR
    offers: List[RestaurantOffer] = field(default_factory=list)
    attempts: int = 0
    error: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    seconds: float = 0.0

    @property
    def display_name(self) -> str:
        return PLATFORM_INFO.get(self.platform, {}).get("display_name", self.platform.value)

    def as_status(self) -> dict:
        d = {"status": self.status, "offers": len(self.offers), "attempts": self.attempts,
             "seconds": round(self.seconds, 1)}
        if self.error:
            d["error"] = self.error
        return d


@dataclass
class MultiPlatformResult:
    outcomes: Dict[Platform, PlatformOutcome]

    @property
    def offers(self) -> List[RestaurantOffer]:
        return [o for out in self.outcomes.values() for o in out.offers]

    @property
    def sources(self) -> List[str]:
        return list(dict.fromkeys(s for out in self.outcomes.values() for s in out.sources))

    @property
    def missing(self) -> List[PlatformOutcome]:
        return [o for o in self.outcomes.values() if o.status != STATUS_OK]

    def status_note(self) -> Optional[str]:
        """Human-readable warning listing platforms without results, or None."""
        parts = []
        for out in self.missing:
            if out.status == STATUS_NO_OFFERS:
                parts.append(f"{out.display_name}: no offers found")
            elif out.status == STATUS_TIMED_OUT:
                parts.append(f"{out.display_name}: timed out")
            else:
                parts.append(f"{out.display_name}: search failed")
        if not parts:
            return None
        return ("Results may be incomplete - " + "; ".join(parts)
                + f" (after {max(o.attempts for o in self.missing)} attempt(s)).")

    def summary(self) -> Optional[str]:
        summaries = [o.summary for o in self.outcomes.values() if o.summary]
        note = self.status_note()
        text = " | ".join(summaries) if summaries else None
        if note:
            text = f"{text} | {note}" if text else note
        return text


def _platform_value(offer: RestaurantOffer) -> str:
    p = offer.platform
    return p.value if hasattr(p, "value") else str(p)


async def _search_one(provider, restaurant: str, city: str, platform: Platform,
                      deadline: float, per_attempt_timeout: float, max_attempts: int,
                      retry_delay: float) -> PlatformOutcome:
    out = PlatformOutcome(platform=platform)
    started = time.monotonic()

    for attempt in range(1, max_attempts + 1):
        remaining = deadline - time.monotonic()
        if remaining < 3:  # not enough time left for a meaningful attempt
            break
        out.attempts = attempt
        try:
            result = await asyncio.wait_for(
                provider.search_restaurant_offers(restaurant_name=restaurant, city=city, platforms=[platform]),
                timeout=min(per_attempt_timeout, remaining),
            )
            # Providers can mislabel offers; keep only this platform's.
            offers = [o for o in result.offers if _platform_value(o) == platform.value]
            if offers:
                out.status, out.offers, out.error = STATUS_OK, offers, None
                out.sources, out.summary = list(result.sources or []), result.summary
                break
            out.status, out.error = STATUS_NO_OFFERS, None
            logger.info(f"[PLATFORM-SEARCH] {platform.value}: 0 offers (attempt {attempt})")
        except asyncio.TimeoutError:
            out.status, out.error = STATUS_TIMED_OUT, None
            logger.warning(f"[PLATFORM-SEARCH] {platform.value}: timed out (attempt {attempt})")
        except Exception as e:  # noqa: BLE001 - report, never drop silently
            out.status, out.error = STATUS_ERROR, f"{type(e).__name__}: {str(e)[:120]}"
            logger.warning(f"[PLATFORM-SEARCH] {platform.value}: {out.error} (attempt {attempt})")

        if attempt < max_attempts:
            await asyncio.sleep(retry_delay * attempt)

    out.seconds = time.monotonic() - started
    return out


async def search_platforms_with_status(
    provider,
    restaurant: str,
    city: str,
    platforms: List[Platform],
    total_timeout: float = 75.0,
    per_attempt_timeout: float = 40.0,
    max_attempts: int = 2,
    retry_delay: float = 1.5,
) -> MultiPlatformResult:
    """Search each platform independently (concurrently), retrying failures/empties."""
    deadline = time.monotonic() + total_timeout
    outcomes = await asyncio.gather(*[
        _search_one(provider, restaurant, city, p, deadline, per_attempt_timeout, max_attempts, retry_delay)
        for p in platforms
    ])
    result = MultiPlatformResult(outcomes={o.platform: o for o in outcomes})
    logger.info("[PLATFORM-SEARCH] %s, %s -> %s", restaurant, city,
                {p.value: o.as_status() for p, o in result.outcomes.items()})
    return result
