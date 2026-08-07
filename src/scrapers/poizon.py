"""Scraper for 得物 Poizon (poizon.jobs.feishu.cn/578078).

Uses the Feishu Recruitment SaaS shared module.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "poizon.jobs.feishu.cn"
PLATFORM = "poizon"
COMPANY = "得物"


def scrape_poizon() -> list[JobPosting]:
    return scrape_feishu_jobs(host=HOST, platform=PLATFORM, company=COMPANY)
