"""Scraper for 网易游戏 (IEG) 社招岗位.

网网易主体招聘站 hr.163.com 提供了 businessGroup 查询参数，仅拉取网易游戏事业群
(IEG-NO = 网易游戏-非外包, IEG-O = 网易游戏-外包) 的职位。复用 netease.py 的
API 调用模式，关键词在 hr.163.com 主体已配置时这里不重复搜全量，而是按 IEG 走全量。

Endpoint: POST https://hr.163.com/api/hr163/position/queryPage
  body: { keyword, currentPage, pageSize, businessGroup }
"""
from __future__ import annotations

import logging
import time
import random
from typing import Optional

from curl_cffi import requests as curl_requests
from fake_useragent import UserAgent

from src.models import JobPosting

logger = logging.getLogger(__name__)

API_URL = "https://hr.163.com/api/hr163/position/queryPage"

# 网易游戏 IEG 事业群代码（来自 hr.163.com/job-list.html 的 businessGroup 选项）
# IEG-NO: Internet Games - Non-Outsource, IEG-O: Internet Games - Outsource
IEG_BUSINESS_GROUPS = ["IEG-NO", "IEG-O"]

_ua = UserAgent(browsers=["chrome", "edge"], os=["windows", "macos"])


def scrape_netease_game() -> list[JobPosting]:
    """Scrape NetEase IEG (game) social recruitment positions."""
    session = curl_requests.Session(
        timeout=30,
        impersonate="chrome",
        headers={
            "User-Agent": _ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Referer": "https://hr.163.com/",
            "Origin": "https://hr.163.com",
        },
    )

    all_items: dict[str, dict] = {}
    for bg in IEG_BUSINESS_GROUPS:
        page = 1
        max_pages = 20  # 20 * 20 = 400 ceiling per businessGroup
        while page <= max_pages:
            payload = {
                "keyword": "",
                "currentPage": page,
                "pageSize": 20,
                "businessGroup": bg,
            }
            try:
                resp = session.post(API_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("[netease_game] request failed for %s page %d: %s", bg, page, e)
                break

            if data.get("code") != 200:
                logger.info("[netease_game] code=%s msg=%s", data.get("code"), data.get("msg"))
                break

            records = data.get("data", {}).get("list", [])
            if not records:
                break

            for item in records:
                jid = str(item.get("id", ""))
                if jid and jid not in all_items:
                    all_items[jid] = item

            total = data.get("data", {}).get("total", 0)
            if page * 20 >= total:
                break
            page += 1
            time.sleep(random.uniform(0.5, 1.2))

        logger.info("[netease_game] businessGroup=%s collected=%d", bg, len(all_items))

    jobs: list[JobPosting] = []
    for item in all_items.values():
        work_places = item.get("workPlaceNameList", [])
        location = ", ".join(work_places) if work_places else ""

        # skip 实习/校招 (recruitType code; hr.163.com uses postType)
        post_type = (item.get("firstPostTypeName", "") or "").strip()
        if "实习" in post_type or "校招" in post_type or "应届" in post_type:
            continue

        jid = str(item.get("id", ""))
        bee_url = item.get("beeUrl") or ""
        detail_url = bee_url if bee_url else f"https://hr.163.com/job-detail.html?id={jid}"

        job = JobPosting(
            job_id=jid,
            platform="netease_game",
            title=item.get("name", "") or "",
            company="网易游戏",
            department=item.get("firstDepName", "") or item.get("businessGroup", ""),
            location=location,
            experience=item.get("reqWorkYearsName", "") or "",
            education=item.get("reqEducationName", "") or "",
            description=item.get("description", "") or "",
            requirements=item.get("requirement", "") or "",
            url=detail_url,
            publish_date=item.get("updateTime", "") or "",
            category=post_type,
        )
        jobs.append(job)

    session.close()
    logger.info("[netease_game] total filtered jobs: %d", len(jobs))
    return jobs
