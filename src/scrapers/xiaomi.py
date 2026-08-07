"""Scraper for 小米 Xiaomi (hr.xiaomi.com).

GET https://hr.xiaomi.com/website/api/agent/searchJobPage
  params: keyword, cityZhNames, pageSize, pageNum

Returns paginated JSON list with title/city/desc/requirement.
"""
from __future__ import annotations

import logging
import time
import random

from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent

from src.models import JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://hr.xiaomi.com/website/api/agent/searchJobPage"
PAGE_SIZE = 20
MAX_PAGES = 50  # 20*50=1000 ceiling

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def scrape_xiaomi() -> list[JobPosting]:
    """Scrape Xiaomi social recruitment positions."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://hr.xiaomi.com/social",
        },
    )

    all_items: dict[str, dict] = {}
    page = 1
    while page <= MAX_PAGES:
        params = {
            "keyword": "",
            "cityZhNames": "",
            "pageSize": PAGE_SIZE,
            "pageNum": page,
        }
        try:
            resp = session.get(API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("[xiaomi] request failed at page %d: %s", page, e)
            break

        d = data.get("data") or {}
        items = d.get("list") or []

        if not items:
            break

        new_count = 0
        for it in items:
            jid = str(it.get("id") or "")
            if jid and jid not in all_items:
                all_items[jid] = it
                new_count += 1

        logger.info("[xiaomi] page %d: got %d items, new=%d",
                    page, len(items), new_count)

        if new_count == 0:
            break
        if len(items) < PAGE_SIZE:
            break

        page += 1
        time.sleep(random.uniform(0.4, 0.9))

    jobs: list[JobPosting] = []
    for it in all_items.values():
        jid = str(it.get("id") or "")
        title = it.get("title") or ""
        if not jid or not title:
            continue

        city_list = it.get("cityZhNames") or []
        if isinstance(city_list, list):
            location = ", ".join(str(c) for c in city_list if c)
        else:
            location = str(city_list or "")

        department = it.get("levelOneDeptName") or ""
        description = it.get("description") or ""
        requirement = it.get("requirement") or ""

        # filter to social recruitment only (type=1 social, type=2 campus/顶尖应届, type=3 intern)
        jtype = it.get("type")
        if jtype is not None and jtype != 1:
            continue

        # Build detail URL - xiaomi uses /job/view/<id>
        url = f"https://hr.xiaomi.com/job/view/{jid}"

        jobs.append(JobPosting(
            job_id=jid,
            platform="xiaomi",
            title=title,
            company="小米",
            department=department,
            location=location,
            description=description,
            requirements=requirement,
            url=url,
        ))

    session.close()
    logger.info("[xiaomi] total jobs: %d", len(jobs))
    return jobs
