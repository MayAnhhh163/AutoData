"""
CLI module - Parse command-line arguments.
"""

import argparse
from typing import Any


def parse_arguments() -> Any:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="AutoData - AI Article-Based Crawler (No PDF Required)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default topic
  python main.py

  # Run with custom topic (KHÔNG CẦN URL!)
  python main.py --project "Luật Đất đai 2025"

  # Show configuration
  python main.py --show-config
  
Workflow:
  1. Tìm tin tức về dự luật
  2. Crawl nội dung tin tức
  3. Extract keywords
  4. Tìm ý kiến công chúng
  5. Phân tích sentiment
  6. Export CSV
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        help='[DEPRECATED] URL is no longer required - workflow is article-based'
    )

    parser.add_argument(
        '--project',
        type=str,
        help='Tên dự luật/chủ đề (ví dụ: "Luật Đất đai 2025")'
    )

    parser.add_argument(
        '--async',
        dest='async_mode',
        action='store_true',
        help='Run workflow in async mode (default: sync)'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Display current configuration and exit'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--no-selenium',
        action='store_true',
        help='Disable Selenium for web crawling (use requests only)'
    )

    parser.add_argument(
        '--max-comments',
        type=int,
        help='Maximum number of comments to collect per source'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for results (default: ./data)'
    )

    args = parser.parse_args()

    return args


# Export
__all__ = ["parse_arguments"]