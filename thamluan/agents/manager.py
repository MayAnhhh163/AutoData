"""
Manager Agent - Điều phối và quản lý workflow.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from agents.base import BaseAgent
from core.types import AgentState, AgentRole, TaskType
from prompts import load_prompt

logger = logging.getLogger(__name__)


class ManagerAgent(BaseAgent):
    """
    Manager Agent - Orchestrator của hệ thống.
    Nhiệm vụ:
    - Phân tích yêu cầu ban đầu
    - Phân công tasks cho các agents
    - Track progress
    - Quyết định next steps
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.MANAGER,
            name="Manager Agent",
            description="Orchestrates workflow and manages agent coordination"
        )
        self.system_prompt = load_prompt("manager_system.md")
        self.processed_urls = set()  # tránh duplicate URLs

    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute manager logic.
        """
        try:
            logger.info("=" * 60)
            logger.info("Manager Agent executing...")
            logger.info("=" * 60)

            if not state.get('current_task'):
                return await self._start_workflow(state)
            else:
                return await self._monitor_and_decide(state)

        except Exception as e:
            logger.error(f"Manager execution error: {str(e)}")
            return self.log_error(state, f"Manager execution failed: {str(e)}")

    async def _start_workflow(self, state: AgentState) -> AgentState:
        """
        Bắt đầu workflow mới - Article-based (không cần PDF).
        """
        logger.info("Starting new workflow (article-based)...")

        target_url = state.get('target_url')
        project_name = state['project_name']

        logger.info(f"Project/Topic: {project_name}")
        if target_url:
            logger.info(f"Reference URL: {target_url}")
        else:
            logger.info("Reference URL: Not provided (not required)")

        # Start with searching for news articles about the law
        task = self.create_task(
            task_type=TaskType.SEARCH_NEWS.value,
            input_data={'topic': project_name, 'reference_url': target_url}
        )

        state = self.update_state(state, {'current_task': task})
        from core.types import update_state_task
        state = update_state_task(state, task)

        logger.info(f" Created first task: {task.task_type.value}")
        return state

    async def _monitor_and_decide(self, state: AgentState) -> AgentState:
        """
        Monitor progress và quyết định next step.
        """
        current_task = state.get('current_task')
        task_history = state.get('task_history', [])

        if not current_task:
            logger.info("No current task, workflow may be complete")
            return state

        logger.info(f"Current task: {current_task.task_type.value} - {current_task.status.value}")

        completed_types = [
            task.task_type
            for task in task_history
            if task.status.value == 'completed'
        ]

        def task_already_created(task_type):
            return any(t.task_type == task_type for t in task_history) or \
                   (current_task and current_task.task_type == task_type)

        next_task = None

        # NEW WORKFLOW LOGIC (Article-based, no PDF)
        # Step 1: SEARCH_NEWS → SCRAPE_NEWS_ARTICLES
        if TaskType.SEARCH_NEWS in completed_types and TaskType.SCRAPE_NEWS_ARTICLES not in completed_types:
            if not task_already_created(TaskType.SCRAPE_NEWS_ARTICLES):
                search_results = state.get('search_results', [])
                if search_results:
                    urls_to_scrape = [r['url'] for r in search_results[:20]]  # Top 20 news articles
                    next_task = self.create_task(
                        task_type=TaskType.SCRAPE_NEWS_ARTICLES.value,
                        input_data={'urls_to_scrape': urls_to_scrape}
                    )
                    logger.info(f"📰 Next: Scrape {len(urls_to_scrape)} news articles")

        # Step 2: SCRAPE_NEWS_ARTICLES → EXTRACT_KEYWORDS_FROM_NEWS
        elif TaskType.SCRAPE_NEWS_ARTICLES in completed_types and TaskType.EXTRACT_KEYWORDS_FROM_NEWS not in completed_types:
            if not task_already_created(TaskType.EXTRACT_KEYWORDS_FROM_NEWS):
                news_articles = state.get('news_articles', [])
                if news_articles:
                    next_task = self.create_task(
                        task_type=TaskType.EXTRACT_KEYWORDS_FROM_NEWS.value,
                        input_data={'news_articles': news_articles}
                    )
                    logger.info(f"🔑 Next: Extract keywords from {len(news_articles)} articles")

        # Step 3: EXTRACT_KEYWORDS_FROM_NEWS → SEARCH_OPINIONS
        elif TaskType.EXTRACT_KEYWORDS_FROM_NEWS in completed_types and TaskType.SEARCH_OPINIONS not in completed_types:
            if not task_already_created(TaskType.SEARCH_OPINIONS):
                keywords = state.get('extracted_keywords')
                if keywords:
                    next_task = self.create_task(
                        task_type=TaskType.SEARCH_OPINIONS.value,
                        input_data={'keywords': keywords}
                    )
                    logger.info("🔍 Next: Search for public opinions")

        # Check if we just completed a SCRAPE_ARTICLES task - handle this FIRST
        if current_task.task_type == TaskType.SCRAPE_ARTICLES and current_task.status.value == 'completed':
            # ArticleAnalyzerAgent already set scrape_articles_done and updated analyzed_articles
            # Just log the completion
            analyzed_articles = state.get('analyzed_articles', [])
            new_articles = getattr(current_task, 'output_data', {}).get('articles', [])
            logger.info(f" Scrape task completed: {len(new_articles)} new articles in this batch")
            logger.info(f" Total articles in state: {len(analyzed_articles)}")

        # Check if a scrape task already exists
        scrape_task_exists = any(t.task_type == TaskType.SCRAPE_ARTICLES for t in task_history) or \
                             (current_task and current_task.task_type == TaskType.SCRAPE_ARTICLES)

        # Only create new scrape tasks if:
        # 1. SEARCH_OPINIONS is completed
        # 2. Scrape is not marked as done
        # 3. No scrape task exists yet
        if TaskType.SEARCH_OPINIONS in completed_types and \
                not state.get('scrape_articles_done', False) and \
                not scrape_task_exists:
            search_results = state.get('search_results', [])
            logger.info(f" Have {len(search_results)} search results to process")
            if search_results:
                # Lọc URLs đã scrape
                processed_urls = state.get('processed_urls', set())
                urls_to_scrape = [r['url'] for r in search_results if r['url'] not in processed_urls]
                if urls_to_scrape:
                    logger.info(f" Creating scrape task for {len(urls_to_scrape)} URLs")
                    next_task = self.create_task(
                        task_type=TaskType.SCRAPE_ARTICLES.value,
                        input_data={'urls_to_scrape': urls_to_scrape}
                    )
                    logger.info(f" Next: Scrape articles and analyze sentiment (next_task={next_task is not None})")
                else:
                    # No new URLs to scrape, mark as done
                    logger.info(" All URLs already processed, marking scrape as done")
                    state['scrape_articles_done'] = True
            else:
                # No search results at all
                logger.info(" No search results found, marking scrape as done")
                state['scrape_articles_done'] = True

        # Check if we should move to export - only if scrape is truly done
        # IMPORTANT: Only move to export when scrape_articles_done = True
        scrape_is_done = state.get('scrape_articles_done', False)
        logger.info(f" Checking export: scrape_is_done={scrape_is_done}, next_task={next_task is not None}")

        # Only consider moving to export if scrape is actually marked as done
        if scrape_is_done and TaskType.EXPORT_DATA not in completed_types:
            if not task_already_created(TaskType.EXPORT_DATA):
                analyzed_articles = state.get('analyzed_articles', [])
                if analyzed_articles:
                    next_task = self.create_task(
                        task_type=TaskType.EXPORT_DATA.value,
                        input_data={'analyzed_articles': analyzed_articles}
                    )
                    logger.info(" Next: Export to CSV")
                else:
                    # No articles to export, mark workflow as complete
                    logger.info(" No articles found to export, completing workflow")
                    state['is_complete'] = True

        elif TaskType.EXPORT_DATA in completed_types:
            logger.info(" Workflow completed successfully!")
            state['is_complete'] = True
            return state

        logger.info(
            f" End of Manager logic: next_task={next_task is not None}, is_complete={state.get('is_complete', False)}")

        if next_task:
            logger.info(f" Setting next task: {next_task.task_type.value} (status: {next_task.status.value})")
            state = self.update_state(state, {'current_task': next_task})
            from core.types import update_state_task
            state = update_state_task(state, next_task)
        else:
            # Safety check: if current scrape task is completed but no next task, prevent infinite loop
            if current_task and current_task.status.value == 'completed' and \
                    current_task.task_type == TaskType.SCRAPE_ARTICLES:
                # If scrape is done but no export task was created, check if we have articles to export
                analyzed_articles = state.get('analyzed_articles', [])
                if analyzed_articles and TaskType.EXPORT_DATA not in completed_types:
                    logger.warning("⚠️ Scrape completed with articles but export not created. Creating export task.")
                    next_task = self.create_task(
                        task_type=TaskType.EXPORT_DATA.value,
                        input_data={'analyzed_articles': analyzed_articles}
                    )
                    state = self.update_state(state, {'current_task': next_task})
                    from core.types import update_state_task
                    state = update_state_task(state, next_task)
                else:
                    logger.warning("⚠️ Scrape task completed but no articles found. Marking workflow complete.")
                    state['is_complete'] = True
            else:
                logger.info("  No new task to create, workflow continues with current task")

        logger.info(
            f" Manager returning state with current_task={state.get('current_task').task_type.value if state.get('current_task') else 'None'}")
        return state

    def generate_report(self, state: AgentState) -> Dict[str, Any]:
        """
        Tạo báo cáo tổng hợp về workflow.
        """
        task_history = state.get('task_history', [])
        completed_tasks = [t for t in task_history if t.status.value == 'completed']
        failed_tasks = [t for t in task_history if t.status.value == 'failed']

        report = {
            'project_name': state.get('project_name'),
            'started_at': state.get('started_at'),
            'completed_at': datetime.now() if state.get('is_complete') else None,
            'total_tasks': len(task_history),
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'errors_count': len(state.get('errors', [])),
            'warnings_count': len(state.get('warnings', [])),
            'pdf_processed': state.get('pdf_local_path') is not None,
            'keywords_extracted': state.get('extracted_keywords') is not None,
            'comments_collected': len(state.get('collected_comments', [])),
            'csv_exported': state.get('csv_output_path') is not None
        }
        return report

# Singleton instance
manager_agent = ManagerAgent()