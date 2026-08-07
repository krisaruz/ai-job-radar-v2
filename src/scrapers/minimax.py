"""Scraper for MiniMax 稀宇科技 (vrfi1sk8a0.jobs.feishu.cn/379481).

Uses the Feishu Recruitment SaaS shared module. The portal is hosted on
a custom subdomain with a portal id path prefix.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "vrfi1sk8a0.jobs.feishu.cn"
PLATFORM = "minimax"
COMPANY = "MiniMax"


def scrape_minimax() -> list[JobPosting]:
    return scrape_feishu_jobs(host=HOST, platform=PLATFORM, company=COMPANY)
