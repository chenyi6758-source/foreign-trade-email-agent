from __future__ import annotations

import email.utils
import xml.etree.ElementTree as ET
from datetime import datetime

import httpx

from app.config import Settings
from app.db import get_db


def _text(item: ET.Element, tag: str) -> str:
    child = item.find(tag)
    return "".join(child.itertext()).strip() if child is not None else ""


def _parse_date(value: str) -> str | None:
    if not value:
        return None
    try:
        return email.utils.parsedate_to_datetime(value).isoformat()
    except Exception:
        return None


def _score_item(title: str, summary: str, settings: Settings) -> tuple[int, list[str], str]:
    text = f"{title} {summary}".lower()
    found = [keyword for keyword in settings.keywords if keyword and keyword in text]
    market = ""
    for candidate in settings.markets:
        if candidate.lower() in text:
            market = candidate
            break
    score = len(found) * 10 + (20 if market else 0)
    return min(score, 100), found, market


async def refresh_intel(settings: Settings) -> dict:
    inserted = 0
    skipped = 0
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for feed in settings.feed_urls:
            try:
                response = await client.get(feed)
                response.raise_for_status()
                root = ET.fromstring(response.text)
                items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

                with get_db() as conn:
                    for item in items[:40]:
                        title = _text(item, "title") or _text(item, "{http://www.w3.org/2005/Atom}title")
                        link = _text(item, "link")
                        if not link:
                            link_node = item.find("{http://www.w3.org/2005/Atom}link")
                            link = link_node.attrib.get("href", "") if link_node is not None else ""
                        summary = (
                            _text(item, "description")
                            or _text(item, "summary")
                            or _text(item, "{http://www.w3.org/2005/Atom}summary")
                        )
                        published = _parse_date(_text(item, "pubDate") or _text(item, "updated"))
                        if not title or not link:
                            skipped += 1
                            continue
                        score, keywords, market = _score_item(title, summary, settings)
                        try:
                            conn.execute(
                                """
                                INSERT INTO intel_items(source, title, url, summary, market, keywords, relevance_score, published_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (feed, title, link, summary[:1000], market, ",".join(keywords), score, published),
                            )
                            inserted += 1
                        except Exception:
                            skipped += 1
            except Exception as exc:
                errors.append(f"{feed}: {exc}")

    return {"inserted": inserted, "skipped": skipped, "errors": errors, "refreshed_at": datetime.utcnow().isoformat()}
