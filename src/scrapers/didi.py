"""Scraper for talent.didiglobal.com (滴滴招聘).

Direct API: GET /recruit-portal-service/api/job/front/list
  params: keyword, page, recruitType=1 (social), size=20

Returns paginated list with jdId/jdNo/jobName/workArea/deptName.
Detail URL: https://talent.didiglobal.com/social/p/<jdNo>
"""
from __future__ import annotations

import logging
import time
import random

from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent

from src.models import JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://talent.didiglobal.com/recruit-portal-service/api/job/front/list"
PAGE_SIZE = 20
MAX_PAGES = 60  # 20*60=1200 ceiling (didi has ~1044 social jobs)

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def scrape_didi() -> list[JobPosting]:
    """Scrape DiDi social recruitment positions via public API."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://talent.didiglobal.com/social",
        },
    )

    all_items: dict[str, dict] = {}
    page = 1
    while page <= MAX_PAGES:
        params = {
            "keyword": "",
            "page": page,
            "recruitType": 1,  # social
            "size": PAGE_SIZE,
        }
        try:
            resp = session.get(API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("[didi] request failed at page %d: %s", page, e)
            break

        d = data.get("data") or {}
        items = d.get("items") or []
        total = int(d.get("total") or 0)

        if not items:
            break

        new_count = 0
        for it in items:
            jid = str(it.get("jdId") or "")
            if jid and jid not in all_items:
                all_items[jid] = it
                new_count += 1

        logger.info("[didi] page %d: got %d items, new=%d, total=%d",
                    page, len(items), new_count, total)

        if new_count == 0:
            break
        if page * PAGE_SIZE >= total:
            break

        page += 1
        time.sleep(random.uniform(0.4, 0.9))

    jobs: list[JobPosting] = []
    for it in all_items.values():
        jid = str(it.get("jdId") or "")
        title = it.get("jobName") or ""
        if not jid or not title:
            continue

        # Detail route uses the numeric jdId (verified: clicking a job card in
        # the list opens /social/p/{jdId}). The JR-code jdNo route renders an
        # empty skeleton even for live jobs.
        jobs.append(JobPosting(
            job_id=jid,
            platform="didi",
            company="滴滴",
            title=title,
            department=it.get("deptName") or "",
            location=it.get("workArea") or "",
            description=it.get("jobDuty") or "",
            requirements=it.get("jobQualification") or "",
            url=f"https://talent.didiglobal.com/social/p/{jid}" if jid else "https://talent.didiglobal.com/social",
            publish_date=it.get("refreshTime") or "",
        ))

    session.close()
    logger.info("[didi] total jobs: %d", len(jobs))
    return jobs
