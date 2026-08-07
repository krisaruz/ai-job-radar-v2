"""Scraper for vivo招聘 (hr.vivo.com).

POST https://hr.vivo.com/api/social/webSite/portal/jobList
  body: { page, page_size }

Returns list (not paginated wrapper) of jobs with title/desc/city/category.
"""
from __future__ import annotations

import logging
import time
import random

from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent

from src.models import JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://hr.vivo.com/api/social/webSite/portal/jobList"
PAGE_SIZE = 50
MAX_PAGES = 30

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def scrape_vivo() -> list[JobPosting]:
    """Scrape vivo social recruitment positions."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": "https://hr.vivo.com",
            "Referer": "https://hr.vivo.com/jobs",
        },
    )

    all_items: dict[str, dict] = {}
    page = 1
    while page <= MAX_PAGES:
        payload = {"page": page, "page_size": PAGE_SIZE}
        try:
            resp = session.post(API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("[vivo] request failed at page %d: %s", page, e)
            break

        items = data.get("data") or []
        if not items:
            break

        new_count = 0
        for it in items:
            jid = str(it.get("job_id") or "")
            if jid and jid not in all_items:
                all_items[jid] = it
                new_count += 1

        logger.info("[vivo] page %d: got %d items, new=%d",
                    page, len(items), new_count)

        if new_count == 0:
            break
        if len(items) < PAGE_SIZE:
            break

        page += 1
        time.sleep(random.uniform(0.4, 0.9))

    jobs: list[JobPosting] = []
    for it in all_items.values():
        jid = str(it.get("job_id") or "")
        title = it.get("job_title") or ""
        if not jid or not title:
            continue

        # job_location_list is list of {city, location, ...}
        loc_list = it.get("job_location_list") or []
        if isinstance(loc_list, list) and loc_list:
            cities = []
            for loc in loc_list:
                if isinstance(loc, dict):
                    c = loc.get("city") or ""
                    if c:
                        cities.append(c)
            location = ", ".join(cities)
        else:
            location = ""

        department = it.get("requirement_org_name") or ""
        category = it.get("job_category") or ""
        if category and not department:
            department = category

        description = it.get("job_desc") or ""

        # experience
        yoe_min = it.get("yoe_min")
        yoe_max = it.get("yoe_max")
        exp = ""
        if yoe_min is not None and yoe_min >= 0 and yoe_max is not None and yoe_max > 0:
            exp = f"{yoe_min}-{yoe_max}年"

        edu = it.get("degree_range_name") or ""

        url = f"https://hr.vivo.com/jobs?id={jid}"

        jobs.append(JobPosting(
            job_id=jid,
            platform="vivo",
            title=title,
            company="vivo",
            department=department,
            location=location,
            experience=exp,
            education=edu,
            description=description,
            requirements="",
            url=url,
        ))

    session.close()
    logger.info("[vivo] total jobs: %d", len(jobs))
    return jobs
