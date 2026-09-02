"""Scraper for 科大讯飞 iFlytek (iflytek.zhiye.com - Beisen 北森招聘 SaaS).

POST https://iflytek.zhiye.com/api/Jobad/GetJobAdPageList
  body: { PageIndex, PageSize, KeyWord, SearchCondition, LangType }
"""
from __future__ import annotations

import logging
import time
import random

from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent

from src.models import JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://iflytek.zhiye.com/api/Jobad/GetJobAdPageList"
PAGE_SIZE = 20
MAX_PAGES = 50  # 20*50=1000 ceiling

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def scrape_iflytek() -> list[JobPosting]:
    """Scrape iFlytek social recruitment positions via Beisen API."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Origin": "https://iflytek.zhiye.com",
            "Referer": "https://iflytek.zhiye.com/jobs",
        },
    )

    all_items: dict[str, dict] = {}
    page = 1
    while page <= MAX_PAGES:
        payload = {
            "PageIndex": page,
            "PageSize": PAGE_SIZE,
            "KeyWord": "",
            "SearchCondition": None,
            "LangType": "zh_CN",
        }
        try:
            resp = session.post(API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("[iflytek] request failed at page %d: %s", page, e)
            break

        items = data.get("Data") or []
        # Beisen returns Count = total matches, Total is something else (always 0)
        total_count = int(data.get("Count") or data.get("Total") or 0)

        if not items:
            break

        new_count = 0
        for it in items:
            jid = str(it.get("Id") or it.get("JobAdId") or "")
            if jid and jid not in all_items:
                all_items[jid] = it
                new_count += 1

        logger.info("[iflytek] page %d: got %d items, new=%d, total_count=%d",
                    page, len(items), new_count, total_count)

        if new_count == 0:
            break
        if page * PAGE_SIZE >= total_count:
            break

        page += 1
        time.sleep(random.uniform(0.5, 1.0))

    jobs: list[JobPosting] = []
    for it in all_items.values():
        jid = str(it.get("Id") or it.get("JobAdId") or "")
        title = it.get("JobAdName") or ""
        if not jid or not title:
            continue

        # Beisen fields
        loc_names = it.get("LocNames") or []
        if isinstance(loc_names, list):
            location = ", ".join(str(x) for x in loc_names if x)
        else:
            location = str(loc_names or "")

        department = it.get("Org") or it.get("Category") or ""
        description = it.get("Duty") or ""
        requirement = it.get("Require") or ""
        publish_date = it.get("PostDate") or ""

        # Sanitize publish_date: beisen default "0001-01-01T00:00:00" means no date
        if isinstance(publish_date, str) and publish_date.startswith("0001-"):
            publish_date = ""

        # Detail URL captured from the real portal: clicking a job card's
        # "查看详情" opens https://iflytek.zhiye.com/{pageId}/detail?jobAdId={Id}
        # where Id is the GUID field (NOT the numeric JobAdId), and 4 is the
        # social-recruit page id. Verified rendering the correct job standalone.
        guid = str(it.get("Id") or "")
        detail_url = f"https://iflytek.zhiye.com/4/detail?jobAdId={guid}" if guid else "https://iflytek.zhiye.com/jobs"

        jobs.append(JobPosting(
            job_id=jid,
            platform="iflytek",
            title=title,
            company="科大讯飞",
            department=str(department) if department else "",
            location=location,
            description=description,
            requirements=requirement,
            url=detail_url,
            publish_date=str(publish_date) if publish_date else "",
        ))

    session.close()
    logger.info("[iflytek] total jobs: %d", len(jobs))
    return jobs
