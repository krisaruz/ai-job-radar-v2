"""Scraper for OPPO招聘 (career.oppo.com).

POST https://career.oppo.com/ats-candidate-api/open-api/position/queryPositionList
  body: { pageNum, pageSize, publishName, workCityCodeList, jobTypeList, recruitTypeList, shareId }

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

API_URL = "https://career.oppo.com/ats-candidate-api/open-api/position/queryPositionList"
PAGE_SIZE = 20
MAX_PAGES = 30  # 20*30=600 ceiling

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def scrape_oppo() -> list[JobPosting]:
    """Scrape OPPO social recruitment positions."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": "https://career.oppo.com",
            "Referer": "https://career.oppo.com/recruitment",
        },
    )

    all_items: dict[str, dict] = {}
    page = 1
    while page <= MAX_PAGES:
        payload = {
            "pageNum": page,
            "pageSize": PAGE_SIZE,
            "publishName": "",
            "workCityCodeList": [],
            "jobTypeList": [],
            "recruitTypeList": [],
            "shareId": "",
        }
        try:
            resp = session.post(API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("[oppo] request failed at page %d: %s", page, e)
            break

        d = data.get("data") or {}
        items = d.get("list") or []
        total_str = d.get("total") or "0"
        total = int(total_str) if isinstance(total_str, str) else int(total_str or 0)

        if not items:
            break

        new_count = 0
        for it in items:
            jid = str(it.get("positionId") or "")
            if jid and jid not in all_items:
                all_items[jid] = it
                new_count += 1

        logger.info("[oppo] page %d: got %d items, new=%d, total=%d",
                    page, len(items), new_count, total)

        if new_count == 0:
            break
        if page * PAGE_SIZE >= total:
            break

        page += 1
        time.sleep(random.uniform(0.4, 0.9))

    jobs: list[JobPosting] = []
    for it in all_items.values():
        jid = str(it.get("positionId") or "")
        title = it.get("publishName") or it.get("jobName") or ""
        if not jid or not title:
            continue

        location = it.get("workCityName") or ""
        department = it.get("jobType") or ""

        min_years = it.get("minWorkYears")
        max_years = it.get("maxWorkYears")
        exp = ""
        if min_years is not None and max_years is not None:
            exp = f"{min_years}-{max_years}年"

        edu = it.get("educationRequire") or ""
        # translate edu code
        edu_map = {
            "UNDERGRADUATE-AND-ABOVE": "本科及以上",
            "MASTER-AND-ABOVE": "硕士及以上",
            "DOCTOR-AND-ABOVE": "博士及以上",
        }
        edu_text = edu_map.get(edu, edu)

        description = it.get("jobDuty") or ""
        requirement = it.get("jobRequire") or ""

        url = f"https://career.oppo.com/recruitment?id={jid}"

        jobs.append(JobPosting(
            job_id=jid,
            platform="oppo",
            title=title,
            company="OPPO",
            department=department,
            location=location,
            experience=exp,
            education=edu_text,
            description=description,
            requirements=requirement,
            url=url,
        ))

    session.close()
    logger.info("[oppo] total jobs: %d", len(jobs))
    return jobs
