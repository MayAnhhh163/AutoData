"""
Tools package for AutoData system.
Chứa tất cả các tools để agents sử dụng.
"""

# Hybrid workflow tools (NEW)
from .law_list_crawler import law_list_crawler, LawListCrawler
from .pdf_downloader import pdf_downloader, PDFDownloader
from .enhanced_opinion_crawler import enhanced_opinion_crawler, EnhancedOpinionCrawler
from .nlp_analyzer import nlp_analyzer, NLPAnalyzer

# Existing tools
from .web_crawler import WebCrawlerTool
from .pdf_handler import PDFHandlerTool
from .pdf_extractor import PDFExtractorTool
from .search_engine import SearchEngineTool
from .comment_scraper import CommentScraperTool
from .csv_exporter import CSVExporterTool
from .text_analyzer import TextAnalyzerTool
from .vector_db import VectorDBTool
from .article_scraper import ArticleScraperTool, article_scraper_tool
from .sentiment_analyzer import SentimentAnalyzerTool, sentiment_analyzer_tool
from .legal_pdf_finder import LegalPDFFinderTool, legal_pdf_finder_tool

# Initialize existing tools
web_crawler_tool = WebCrawlerTool()
pdf_handler_tool = PDFHandlerTool()
pdf_extractor_tool = PDFExtractorTool()
search_engine_tool = SearchEngineTool()
comment_scraper_tool = CommentScraperTool()
csv_exporter_tool = CSVExporterTool()
text_analyzer_tool = TextAnalyzerTool()
vector_db_tool = VectorDBTool()
legal_pdf_finder_tool = LegalPDFFinderTool()