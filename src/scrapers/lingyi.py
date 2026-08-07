"""Scraper for 零一万物 01.AI (01ai.jobs.feishu.cn).

Uses the Feishu Recruitment SaaS shared module.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "01ai.jobs.feishu.cn"
PLATFORM = "lingyi"
COMPANY = "零一万物"


def scrape_lingyi() -> list[JobPosting]:
    return scrape_feishu_jobs(host=HOST, platform=PLATFORM, company=COMPANY)
