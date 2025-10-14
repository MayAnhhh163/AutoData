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
from .hybrid_agents import (
    law_list_search_agent,
    pdf_download_agent,
    pdf_content_extractor_agent,
    vector_db_storage_agent,
    enhanced_opinion_search_agent,
    enhanced_opinion_crawler_agent,
    nlp_analysis_agent,
    hybrid_exporter_agent
)

__all__ = [
    "BaseAgent",
    "manager_agent",
    # Hybrid workflow agents (RECOMMENDED)
    "law_list_search_agent",
    "pdf_download_agent",
    "pdf_content_extractor_agent",
    "vector_db_storage_agent",
    "enhanced_opinion_search_agent",
    "enhanced_opinion_crawler_agent",
    "nlp_analysis_agent",
    "hybrid_exporter_agent",
    # Article-based workflow agents
    "news_search_agent",
    "news_scraper_agent",
    "keyword_extractor_agent",
    # Old PDF workflow agents (legacy)
    "web_crawler_agent",
    "pdf_handler_agent",
    "content_extractor_agent",
    # Opinion search agents (legacy)
    "search_agent",
    "article_analyzer_agent",
    "scraper_agent",
    "exporter_agent",
]