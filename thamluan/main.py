"""
Main.py - Entry point cho AutoData system (Async version).
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import config
from core.auto import run_workflow_async
from utils.logging import setup_logging
from utils.cli import parse_arguments


def main():
    """Main function"""

    # Setup logging
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("AutoData - HYBRID WORKFLOW (PDF + Opinion Crawler)")
    logger.info("=" * 80)
    logger.info("Pipeline: Law List → PDF → Extract → Opinions → NLP → Export")
    logger.info("=" * 80)

    # Parse arguments
    args = parse_arguments()

    # Display configuration if requested
    if args.show_config:
        config.display_config()
        return

    # Validate configuration
    if not config.validate_config():
        logger.error("Configuration validation failed. Please check your setup.")
        return

    # Get project name (chủ đề/tên dự luật) - BẮT BUỘC
    # URL là optional (không cần nữa với article-based workflow)
    project_name = args.project or input("\n📋 Nhập tên dự luật/chủ đề: ").strip()
    
    if not project_name:
        project_name = "Luật Khoa học, công nghệ và đổi mới sáng tạo 2025"  # Default
    

    if not project_name:
        project_name = "Luật Khoa học, công nghệ và đổi mới sáng tạo 2025"  # Default

    logger.info(f"Topic/Project: {project_name}")

    try:
        # Run workflow asynchronously (không cần URL)
        logger.info("Running workflow asynchronously...")
        final_state = asyncio.run(run_workflow_async(project_name))

        # Display results
        logger.info("=" * 80)
        logger.info(" Workflow completed successfully!")
        logger.info("=" * 80)

        # Show key results - HYBRID WORKFLOW
        logger.info("\n" + "=" * 80)
        logger.info("HYBRID WORKFLOW RESULTS")
        logger.info("=" * 80)
        
        # Phase 1: Law documents
        law_docs_count = len(final_state.get('law_documents', []))
        pdfs_count = len(final_state.get('pdf_paths', []))
        logger.info(f"\n📋 PHASE 1 - Law Documents:")
        logger.info(f"   Law Documents Found: {law_docs_count}")
        logger.info(f"   PDFs Downloaded: {pdfs_count}")
        
        keywords = final_state.get('extracted_keywords')
        if keywords and hasattr(keywords, 'main_keywords'):
            logger.info(f"   Keywords Extracted: {len(keywords.main_keywords)}")
        
        # Phase 2: Opinions
        opinion_urls_count = len(final_state.get('opinion_urls', []))
        opinions_raw_count = len(final_state.get('opinions_raw', []))
        logger.info(f"\n💬 PHASE 2 - Opinions:")
        logger.info(f"   Opinion URLs Found: {opinion_urls_count}")
        logger.info(f"   Opinions Crawled (Full Content): {opinions_raw_count}")
        
        # Phase 3: NLP
        analyzed_count = len(final_state.get('analyzed_opinions', []))
        logger.info(f"\n🧠 PHASE 3 - NLP Analysis:")
        logger.info(f"   Opinions Analyzed: {analyzed_count}")
        
        # Phase 4: Export
        logger.info(f"\n💾 PHASE 4 - Export:")
        if final_state.get('csv_output_path'):
            logger.info(f"   CSV Output: {final_state['csv_output_path']}")
        # Show key results
        news_count = len(final_state.get('news_articles', []))
        logger.info(f" News Articles Crawled: {news_count}")

        keywords = final_state.get('extracted_keywords')
        if keywords:
            logger.info(f" Keywords Extracted: {len(keywords.main_keywords)}")

        opinions_count = len(final_state.get('analyzed_articles', []))
        logger.info(f" Opinion Articles Analyzed: {opinions_count}")

        if final_state.get('csv_output_path'):
            logger.info(f" CSV Output: {final_state['csv_output_path']}")

        if final_state.get('vector_db_collection'):
            logger.info(f"   Vector DB Collection: {final_state['vector_db_collection']}")

        # Show errors if any
        errors = final_state.get('errors', [])
        if errors:
            logger.warning(f" Errors encountered: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error.get('message')}")

        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.info("\n Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f" Workflow failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
