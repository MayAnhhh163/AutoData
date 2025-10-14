"""
Auto.py - Setup LangGraph workflow với nodes và edges (Async only).
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from core.types import AgentState, TaskType, create_initial_state
from agents import (
    manager_agent,
    # Hybrid workflow agents (RECOMMENDED)
    law_list_search_agent,
    pdf_download_agent,
    pdf_content_extractor_agent,
    vector_db_storage_agent,
    enhanced_opinion_search_agent,
    enhanced_opinion_crawler_agent,
    nlp_analysis_agent,
    hybrid_exporter_agent,
    # Article-based workflow agents
    news_search_agent,
    news_scraper_agent,
    keyword_extractor_agent,
    # Old PDF workflow agents (kept for compatibility)
    web_crawler_agent,
    pdf_handler_agent,
    content_extractor_agent,
    # Opinion search agents (legacy)
    search_agent,
    article_analyzer_agent,
    exporter_agent
)

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """Tạo LangGraph workflow cho AutoData system (async agents)."""
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("manager", manager_agent.execute)
    
    # Hybrid workflow nodes (RECOMMENDED - Full pipeline)
    workflow.add_node("law_list_search_agent", law_list_search_agent.execute)
    workflow.add_node("pdf_download_agent", pdf_download_agent.execute)
    workflow.add_node("pdf_content_extractor_agent", pdf_content_extractor_agent.execute)
    workflow.add_node("vector_db_storage_agent", vector_db_storage_agent.execute)
    workflow.add_node("enhanced_opinion_search_agent", enhanced_opinion_search_agent.execute)
    workflow.add_node("enhanced_opinion_crawler_agent", enhanced_opinion_crawler_agent.execute)
    workflow.add_node("nlp_analysis_agent", nlp_analysis_agent.execute)
    workflow.add_node("hybrid_exporter_agent", hybrid_exporter_agent.execute)
    
    # Article-based workflow nodes (simple)
    workflow.add_node("news_search_agent", news_search_agent.execute)
    workflow.add_node("news_scraper_agent", news_scraper_agent.execute)
    workflow.add_node("keyword_extractor_agent", keyword_extractor_agent.execute)
    
    # Old PDF workflow nodes (legacy)
    workflow.add_node("web_crawler", web_crawler_agent.execute)
    workflow.add_node("pdf_handler", pdf_handler_agent.execute)
    workflow.add_node("content_extractor", content_extractor_agent.execute)
    
    # Opinion search nodes (legacy)
    workflow.add_node("search_agent", search_agent.execute)
    workflow.add_node("article_analyzer", article_analyzer_agent.execute)
    workflow.add_node("exporter_agent", exporter_agent.execute)

    # Routing từ manager dựa vào task hiện tại
    def route_from_manager(state: AgentState) -> str:
        current_task = state.get('current_task')
        is_complete = state.get('is_complete', False)

        logger.info(
            f"🔀 Routing: current_task={current_task.task_type.value if current_task else 'None'}, is_complete={is_complete}")

        if not current_task:
            logger.info("❌ No current task, ending workflow")
            return END

        if is_complete:
            logger.info(" Workflow marked as complete, ending")
            return END

        task_type = current_task.task_type
        next_agent = {
            # Hybrid workflow routing (RECOMMENDED)
            TaskType.SEARCH_LAW_LIST: "law_list_search_agent",
            TaskType.DOWNLOAD_PDFS: "pdf_download_agent",
            TaskType.EXTRACT_PDF_CONTENT: "pdf_content_extractor_agent",
            TaskType.STORE_VECTOR_DB: "vector_db_storage_agent",
            TaskType.SEARCH_OPINIONS: "enhanced_opinion_search_agent",
            TaskType.CRAWL_OPINIONS_FULL: "enhanced_opinion_crawler_agent",
            TaskType.NLP_ANALYSIS: "nlp_analysis_agent",
            TaskType.EXPORT_DATA: "hybrid_exporter_agent",
            # Article-based workflow routing
            TaskType.SEARCH_NEWS: "news_search_agent",
            TaskType.SCRAPE_NEWS_ARTICLES: "news_scraper_agent",
            TaskType.EXTRACT_KEYWORDS_FROM_NEWS: "keyword_extractor_agent",
            # Old PDF workflow routing (legacy)
            TaskType.CRAWL_WEB: "web_crawler",
            TaskType.DOWNLOAD_PDF: "pdf_handler",
            TaskType.EXTRACT_CONTENT: "content_extractor",
            # Legacy opinion routing
            TaskType.SCRAPE_ARTICLES: "article_analyzer",
        }.get(task_type, END)

        logger.info(f" Routing to: {next_agent}")
        return next_agent

    # Check workflow continue
    def should_continue(state: AgentState) -> str:
        if state.get('is_complete') or len(state.get('errors', [])) > 5:
            return END
        return "manager"

    # Entry point
    workflow.set_entry_point("manager")

    # Edges
    workflow.add_conditional_edges(
        "manager",
        route_from_manager,
        {
            # Hybrid workflow edges (RECOMMENDED)
            "law_list_search_agent": "law_list_search_agent",
            "pdf_download_agent": "pdf_download_agent",
            "pdf_content_extractor_agent": "pdf_content_extractor_agent",
            "vector_db_storage_agent": "vector_db_storage_agent",
            "enhanced_opinion_search_agent": "enhanced_opinion_search_agent",
            "enhanced_opinion_crawler_agent": "enhanced_opinion_crawler_agent",
            "nlp_analysis_agent": "nlp_analysis_agent",
            "hybrid_exporter_agent": "hybrid_exporter_agent",
            # Article-based workflow edges
            "news_search_agent": "news_search_agent",
            "news_scraper_agent": "news_scraper_agent",
            "keyword_extractor_agent": "keyword_extractor_agent",
            # Old PDF workflow edges (legacy)
            "web_crawler": "web_crawler",
            "pdf_handler": "pdf_handler",
            "content_extractor": "content_extractor",
            # Legacy edges
            "search_agent": "search_agent",
            "article_analyzer": "article_analyzer",
            "exporter_agent": "exporter_agent",
            END: END
        }
    )

    # All nodes return to manager after completion
    all_nodes = [
        # Hybrid workflow nodes
        "law_list_search_agent", "pdf_download_agent", "pdf_content_extractor_agent",
        "vector_db_storage_agent", "enhanced_opinion_search_agent", 
        "enhanced_opinion_crawler_agent", "nlp_analysis_agent", "hybrid_exporter_agent",
        # Article-based nodes
        "news_search_agent", "news_scraper_agent", "keyword_extractor_agent",
        # Legacy nodes
        "web_crawler", "pdf_handler", "content_extractor",
        "search_agent", "article_analyzer", "exporter_agent"
    ]
    
    for node in all_nodes:
        workflow.add_conditional_edges(node, should_continue)

    return workflow


async def run_workflow_async(project_name: str, target_url: str = None) -> Dict[str, Any]:
    """
    Chạy workflow bất đồng bộ với project name (chủ đề).
    
    Args:
        project_name: Tên dự luật/chủ đề (BẮT BUỘC)
        target_url: URL tham khảo (KHÔNG BẮT BUỘC, có thể None)
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting AutoData Workflow (Article-Based)")
        logger.info("=" * 80)
        logger.info(f"Topic/Project: {project_name}")
        if target_url:
            logger.info(f"Reference URL: {target_url}")
        logger.info("=" * 80)

        initial_state = create_initial_state(project_name, target_url)
        workflow = create_workflow()
        app = workflow.compile(
            checkpointer=None,
            interrupt_before=None,
            interrupt_after=None,
            debug=False
        )
        # Configure with higher recursion limit
        config = {"recursion_limit": 100}

        logger.info("🚀 Executing workflow asynchronously...")
        final_state = await app.ainvoke(initial_state, config=config)

        report = manager_agent.generate_report(final_state)
        logger.info("=" * 80)
        logger.info("Workflow Report")
        logger.info("=" * 80)
        for key, value in report.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 80)

        return final_state

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        raise


# Export
__all__ = ["create_workflow", "run_workflow_async"]
