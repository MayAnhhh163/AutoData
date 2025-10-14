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

        # Start with HYBRID workflow: search law list first
        task = self.create_task(
            task_type=TaskType.SEARCH_LAW_LIST.value,
            input_data={'topic': project_name, 'reference_url': target_url}
        )

        state = self.update_state(state, {'current_task': task})
        from core.types import update_state_task
        state = update_state_task(state, task)

        logger.info(f"✅ Created first task: {task.task_type.value}")
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

        # HYBRID WORKFLOW LOGIC (Full pipeline with PDF)
        # Step 1: SEARCH_LAW_LIST → DOWNLOAD_PDFS
        if TaskType.SEARCH_LAW_LIST in completed_types and TaskType.DOWNLOAD_PDFS not in completed_types:
            if not task_already_created(TaskType.DOWNLOAD_PDFS):
                law_documents = state.get('law_documents', [])
                if law_documents:
                    next_task = self.create_task(
                        task_type=TaskType.DOWNLOAD_PDFS.value,
                        input_data={'law_documents': law_documents}
                    )
                    logger.info(f"📥 Next: Download {len(law_documents)} PDFs")

        # Step 2: DOWNLOAD_PDFS → EXTRACT_PDF_CONTENT
        elif TaskType.DOWNLOAD_PDFS in completed_types and TaskType.EXTRACT_PDF_CONTENT not in completed_types:
            if not task_already_created(TaskType.EXTRACT_PDF_CONTENT):
                pdf_paths = state.get('pdf_paths', [])
                if pdf_paths:
                    next_task = self.create_task(
                        task_type=TaskType.EXTRACT_PDF_CONTENT.value,
                        input_data={'pdf_paths': pdf_paths}
                    )
                    logger.info(f"📄 Next: Extract content from {len(pdf_paths)} PDFs")

        # Step 3: EXTRACT_PDF_CONTENT → STORE_VECTOR_DB
        elif TaskType.EXTRACT_PDF_CONTENT in completed_types and TaskType.STORE_VECTOR_DB not in completed_types:
            if not task_already_created(TaskType.STORE_VECTOR_DB):
                extracted_keywords = state.get('extracted_keywords')
                if extracted_keywords:
                    next_task = self.create_task(
                        task_type=TaskType.STORE_VECTOR_DB.value,
                        input_data={'extracted_keywords': extracted_keywords}
                    )
                    logger.info("💾 Next: Store PDFs in Vector DB")

        # Step 4: STORE_VECTOR_DB → SEARCH_OPINIONS
        elif TaskType.STORE_VECTOR_DB in completed_types and TaskType.SEARCH_OPINIONS not in completed_types:
            if not task_already_created(TaskType.SEARCH_OPINIONS):
                keywords = state.get('extracted_keywords')
                if keywords:
                    next_task = self.create_task(
                        task_type=TaskType.SEARCH_OPINIONS.value,
                        input_data={'keywords': keywords}
                    )
                    logger.info("🔍 Next: Search for opinion URLs")

        # Step 5: SEARCH_OPINIONS → CRAWL_OPINIONS_FULL
        elif TaskType.SEARCH_OPINIONS in completed_types and TaskType.CRAWL_OPINIONS_FULL not in completed_types:
            if not task_already_created(TaskType.CRAWL_OPINIONS_FULL):
                opinion_urls = state.get('opinion_urls', [])
                if opinion_urls:
                    next_task = self.create_task(
                        task_type=TaskType.CRAWL_OPINIONS_FULL.value,
                        input_data={'opinion_urls': opinion_urls}
                    )
                    logger.info(f"📰 Next: Crawl FULL CONTENT of {len(opinion_urls)} opinions")

        # Step 6: CRAWL_OPINIONS_FULL → NLP_ANALYSIS
        elif TaskType.CRAWL_OPINIONS_FULL in completed_types and TaskType.NLP_ANALYSIS not in completed_types:
            if not task_already_created(TaskType.NLP_ANALYSIS):
                opinions_raw = state.get('opinions_raw', [])
                if opinions_raw:
                    next_task = self.create_task(
                        task_type=TaskType.NLP_ANALYSIS.value,
                        input_data={'opinions_raw': opinions_raw}
                    )
                    logger.info(f"🧠 Next: NLP analysis of {len(opinions_raw)} opinions")

        # Step 7: NLP_ANALYSIS → EXPORT_DATA
        elif TaskType.NLP_ANALYSIS in completed_types and TaskType.EXPORT_DATA not in completed_types:
            if not task_already_created(TaskType.EXPORT_DATA):
                analyzed_opinions = state.get('analyzed_opinions', [])
                if analyzed_opinions:
                    next_task = self.create_task(
                        task_type=TaskType.EXPORT_DATA.value,
                        input_data={'analyzed_opinions': analyzed_opinions}
                    )
                    logger.info(f"💾 Next: Export {len(analyzed_opinions)} analyzed opinions")

        # Step 8: EXPORT_DATA → Complete
        elif TaskType.EXPORT_DATA in completed_types:
            logger.info("✅ Workflow completed successfully!")
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
            # Safety check: if task is completed but no next task, check for missing steps
            if current_task and current_task.status.value == 'completed':
                logger.warning("⚠️ Current task completed but no next task created")
                logger.warning(f"⚠️ Task: {current_task.task_type.value}")
                logger.warning("⚠️ Marking workflow as complete to avoid infinite loop")
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