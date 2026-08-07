"""Scraper for 携程招聘 (job.ctrip.com).

携程招聘站 SPA 调用 POST /api/hrrecruit/getJobAd。
当请求 Accept 头包含 application/json 时，响应是 JSON（默认行为）；
不带 Accept 时返回 XML。我们用 JSON 路径。

condition 字段控制筛选，pager 字段控制分页。社招 category=1。
"""
from __future__ import annotations

import logging
import re
import time
import random
import html

from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent

from src.models import JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://job.ctrip.com/api/hrrecruit/getJobAd"
PAGE_SIZE = 50
MAX_PAGES = 30  # 50*30=1500 ceiling

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])

_TAG_RE = re.compile(r"<[^>]+>")


def _clean_html(text: str) -> str:
    if not text:
        return ""
    return _TAG_RE.sub("", html.unescape(text)).strip()


def scrape_ctrip() -> list[JobPosting]:
    """Scrape Ctrip social recruitment positions."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://job.ctrip.com",
            "Referer": "https://job.ctrip.com/",
        },
    )

    all_items: dict[str, dict] = {}
    page = 1
    while page <= MAX_PAGES:
        payload = {
            "condition": {
                "fromId": [],
                "keyword": "",
                "kind": [],
                "country": [],
                "city": [],
                "bucode": [],
                "jobFamilyCode": [],
                "jobFamilyGroupCode": [],
                "category": 1,
            },
            "pager": {"index": str(page), "size": str(PAGE_SIZE)},
            "head": {"language": "zh_CN", "version": "1"},
        }
        try:
            resp = session.post(API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("[ctrip] request failed at page %d: %s", page, e)
            break

        ret_value = data.get("retValue") or {}
        total = int(ret_value.get("total") or 0)
        items = ret_value.get("recruitJobAdList") or []

        if not items:
            break

        new_count = 0
        for it in items:
            jid = str(it.get("id") or "")
            if jid and jid not in all_items:
                all_items[jid] = it
                new_count += 1

        logger.info("[ctrip] page %d: got %d items, new=%d, total_count=%d",
                    page, len(items), new_count, total)

        if new_count == 0:
            break

        if page * PAGE_SIZE >= total:
            break

        page += 1
        time.sleep(random.uniform(0.5, 1.0))

    jobs: list[JobPosting] = []
    for it in all_items.values():
        jid = str(it.get("id") or "")
        title = it.get("jobTitle") or ""
        if not jid or not title:
            continue

        description = _clean_html(it.get("requirements") or "")
        duty = _clean_html(it.get("duty") or "")
        if duty:
            description = f"{description}\n\n职责:\n{duty}".strip()

        # ctrip SPA uses fromId (e.g. MJ036356) for detail route, not the UUID jobId
        from_id = it.get("fromId") or ""
        detail_path = f"/#/experienced/job-detail/{from_id}" if from_id else ""

        jobs.append(JobPosting(
            job_id=jid,
            platform="ctrip",
            title=title,
            company="携程",
            department=it.get("buName") or it.get("jobFamilyGroupName") or "",
            location=it.get("cityName") or "",
            description=description,
            requirements="",
            url=f"https://job.ctrip.com{detail_path}" if detail_path else "https://job.ctrip.com/#/experienced",
            publish_date=it.get("publishDate") or "",
            category=it.get("kindName") or "",
        ))

    session.close()
    logger.info("[ctrip] total jobs: %d", len(jobs))
    return jobs
