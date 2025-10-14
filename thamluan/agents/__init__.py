"""
Agents package for AutoData system.
"""
from .base import BaseAgent
from .manager import manager_agent
from .dev import web_crawler_agent, pdf_handler_agent, content_extractor_agent
from .res import (
    news_search_agent,
    news_scraper_agent,
    keyword_extractor_agent,
    search_agent,
    article_analyzer_agent,
    scraper_agent,
    exporter_agent
)

__all__ = [
    "BaseAgent",
    "manager_agent",
    # New workflow agents
    "news_search_agent",
    "news_scraper_agent",
    "keyword_extractor_agent",
    # Old PDF workflow agents
    "web_crawler_agent",
    "pdf_handler_agent",
    "content_extractor_agent",
    # Opinion search agents
    "search_agent",
    "article_analyzer_agent",
    "scraper_agent",
    "exporter_agent",
]