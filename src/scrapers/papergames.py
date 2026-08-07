"""Scraper for 叠纸游戏 (papergames.jobs.feishu.cn + career.papegames.com).

Uses the Feishu Recruitment SaaS shared module. The search API is hosted at
papergames.jobs.feishu.cn, but the public-facing detail page links use a
vanity domain career.papegames.com (note: papegames, no 'r') with the
/social/position/<id>/detail path.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "papergames.jobs.feishu.cn"
PLATFORM = "papergames"
COMPANY = "叠纸"
# Detail URLs render via vanity domain career.papegames.com (note spelling)
URL_PATH_TEMPLATE = "https://career.papegames.com/social/position/{jid}/detail"


def scrape_papergames() -> list[JobPosting]:
    return scrape_feishu_jobs(
        host=HOST,
        platform=PLATFORM,
        company=COMPANY,
        url_path_template=URL_PATH_TEMPLATE,
    )
