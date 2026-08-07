"""Scraper for 面壁智能 ModelBest (modelbest.jobs.feishu.cn).

Uses the Feishu Recruitment SaaS shared module.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "modelbest.jobs.feishu.cn"
PLATFORM = "modelbest"
COMPANY = "面壁智能"
# modelbest uses /career/position/<id>/detail
URL_PATH_TEMPLATE = "/career/position/{jid}/detail"


def scrape_modelbest() -> list[JobPosting]:
    return scrape_feishu_jobs(
        host=HOST,
        platform=PLATFORM,
        company=COMPANY,
        url_path_template=URL_PATH_TEMPLATE,
    )
