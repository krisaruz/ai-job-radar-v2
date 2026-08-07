"""Scraper for 百川智能 Baichuan (cq6qe6bvfr6.jobs.feishu.cn/baichuanzhaopin).

Uses the Feishu Recruitment SaaS shared module.
"""
from __future__ import annotations

from src.models import JobPosting
from src.scrapers.feishu_common import scrape_feishu_jobs

HOST = "cq6qe6bvfr6.jobs.feishu.cn"
PLATFORM = "baichuan"
COMPANY = "百川智能"
# baichuan uses /baichuanzhaopin/position/<id>/detail (portal prefix in path)
URL_PATH_TEMPLATE = "/baichuanzhaopin/position/{jid}/detail"


def scrape_baichuan() -> list[JobPosting]:
    return scrape_feishu_jobs(
        host=HOST,
        platform=PLATFORM,
        company=COMPANY,
        url_path_template=URL_PATH_TEMPLATE,
    )
