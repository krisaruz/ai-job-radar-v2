"""Scraper for 智谱 AI (zhipu-ai.jobs.feishu.cn).

Uses the Feishu Recruitment SaaS shared module.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "zhipu-ai.jobs.feishu.cn"
PLATFORM = "zhipu"
COMPANY = "智谱"


def scrape_zhipu() -> list[JobPosting]:
    return scrape_feishu_jobs(host=HOST, platform=PLATFORM, company=COMPANY)
