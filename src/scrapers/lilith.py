"""Scraper for 莉莉丝游戏 (lilithgames.jobs.feishu.cn).

Uses the Feishu Recruitment SaaS shared module.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "lilithgames.jobs.feishu.cn"
PLATFORM = "lilith"
COMPANY = "莉莉丝"
# lilith uses /career/position/<id>/detail (not /index/position/)
URL_PATH_TEMPLATE = "/career/position/{jid}/detail"


def scrape_lilith() -> list[JobPosting]:
    return scrape_feishu_jobs(
        host=HOST,
        platform=PLATFORM,
        company=COMPANY,
        url_path_template=URL_PATH_TEMPLATE,
    )
