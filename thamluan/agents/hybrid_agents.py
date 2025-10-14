"""
Hybrid Workflow Agents - Agents cho PDF + Opinion workflow
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from agents.base import BaseAgent
from core.types import AgentState, AgentRole, TaskType, ExtractedKeywords
from tools.law_list_crawler import law_list_crawler
from tools.pdf_downloader import pdf_downloader
from tools.enhanced_opinion_crawler import enhanced_opinion_crawler
from tools.nlp_analyzer import nlp_analyzer

logger = logging.getLogger(__name__)


class LawListSearchAgent(BaseAgent):
    """Agent tìm kiếm danh sách văn bản luật"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.SEARCH_AGENT,
            name="Law List Search Agent",
            description="Searches for law documents with pagination"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"📋 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.SEARCH_LAW_LIST:
                return state
            
            topic = current_task.input_data.get('topic', state['project_name'])
            
            logger.info(f"🔍 Searching law documents for: {topic}")
            
            # Crawl law list with pagination
            result = law_list_crawler.crawl_law_list(
                topic=topic,
                source='mst',
                max_pages=5,
                max_results=20
            )
            
            if not result.success:
                task = self.complete_task(current_task, {}, error=result.error)
                return self.log_error(state, result.error)
            
            documents = result.data['documents']
            logger.info(f"✅ Found {len(documents)} law documents")
            
            # Convert to dict
            docs_dict = [doc.to_dict() for doc in documents]
            
            task = self.complete_task(current_task, {
                'documents_count': len(documents)
            })
            
            state = self.update_state(state, {
                'current_task': task,
                'law_documents': docs_dict
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Law list search error: {str(e)}")
            return self.log_error(state, f"Law list search failed: {str(e)}")


class PDFDownloadAgent(BaseAgent):
    """Agent download PDFs với deduplication"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.PDF_HANDLER,
            name="PDF Download Agent",
            description="Downloads PDFs with hash deduplication"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"📥 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.DOWNLOAD_PDFS:
                return state
            
            law_documents = state.get('law_documents', [])
            if not law_documents:
                error_msg = "No law documents to download"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)
            
            # Filter documents that have PDF URLs
            docs_with_pdf = [doc for doc in law_documents if doc.get('pdf_url')]
            
            logger.info(f"📥 Downloading {len(docs_with_pdf)} PDFs...")
            
            # Download PDFs
            result = pdf_downloader.download_multiple_pdfs(
                documents=docs_with_pdf,
                max_downloads=10
            )
            
            if not result.success:
                task = self.complete_task(current_task, {}, error=result.error)
                return self.log_error(state, result.error)
            
            downloaded = result.data['downloaded']
            cached = result.data['cached']
            total = result.data['total']
            
            logger.info(f"✅ Downloaded: {len(downloaded)} | Cached: {len(cached)} | Total: {total}")
            
            # Store PDF paths
            pdf_paths = [item['path'] for item in (downloaded + cached)]
            
            task = self.complete_task(current_task, {
                'downloaded_count': len(downloaded),
                'cached_count': len(cached),
                'total_pdfs': total
            })
            
            state = self.update_state(state, {
                'current_task': task,
                'pdf_paths': pdf_paths,
                'pdf_download_info': result.data
            })
            
            return state
            
        except Exception as e:
            logger.error(f"PDF download error: {str(e)}")
            return self.log_error(state, f"PDF download failed: {str(e)}")


class EnhancedOpinionSearchAgent(BaseAgent):
    """Agent tìm kiếm opinions (URLs)"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.SEARCH_AGENT,
            name="Enhanced Opinion Search Agent",
            description="Searches for opinion articles URLs"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"🔍 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.SEARCH_OPINIONS:
                return state
            
            # Get keywords từ extracted_keywords
            extracted_keywords = state.get('extracted_keywords')
            if not extracted_keywords:
                error_msg = "No keywords for opinion search"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)
            
            project_name = state['project_name']
            
            # Generate search queries
            from tools.text_analyzer import text_analyzer_tool
            query_result = text_analyzer_tool.generate_search_queries(
                extracted_keywords,
                base_topic=project_name
            )
            
            if not query_result.success:
                task = self.complete_task(current_task, {}, error=query_result.error)
                return self.log_error(state, query_result.error)
            
            search_queries = query_result.data['queries'][:8]
            
            # Search on news sites
            logger.info(f"🔍 Searching opinions with {len(search_queries)} queries...")
            
            from tools.direct_news_search import direct_news_search_tool
            search_results = []
            
            for idx, query in enumerate(search_queries, 1):
                logger.info(f"📰 Query {idx}/{len(search_queries)}: '{query}'")
                result = direct_news_search_tool.search_all_sites(query, max_results_per_site=5)
                
                if result.success:
                    search_results.extend(result.data['results'])
                
                if len(search_results) >= 50:
                    break
            
            # Dedup and validate
            unique_results = []
            seen_urls = set()
            
            for result in search_results:
                url = result.get('url', '')
                if url and url not in seen_urls:
                    if url.startswith('http://') or url.startswith('https://'):
                        seen_urls.add(url)
                        unique_results.append(result)
            
            logger.info(f"✅ Found {len(unique_results)} unique opinion URLs")
            
            task = self.complete_task(current_task, {
                'urls_count': len(unique_results)
            })
            
            state = self.update_state(state, {
                'current_task': task,
                'search_queries': search_queries,
                'opinion_urls': unique_results[:30]  # Top 30
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Opinion search error: {str(e)}")
            return self.log_error(state, f"Opinion search failed: {str(e)}")


class EnhancedOpinionCrawlerAgent(BaseAgent):
    """Agent crawl FULL CONTENT của opinions"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.SCRAPER_AGENT,
            name="Enhanced Opinion Crawler Agent",
            description="Crawls FULL CONTENT of opinion articles"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"📰 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.CRAWL_OPINIONS_FULL:
                return state
            
            opinion_urls = state.get('opinion_urls', [])
            if not opinion_urls:
                error_msg = "No opinion URLs to crawl"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)
            
            # Extract URLs
            urls = [item['url'] for item in opinion_urls]
            
            logger.info(f"📰 Crawling FULL CONTENT of {len(urls)} opinions...")
            
            # Crawl opinions with FULL CONTENT
            result = enhanced_opinion_crawler.crawl_multiple_opinions(
                urls=urls,
                source="mixed",
                max_crawl=30
            )
            
            if not result.success:
                task = self.complete_task(current_task, {}, error=result.error)
                return self.log_error(state, result.error)
            
            opinions = result.data['opinions']
            
            # Convert to dict
            opinions_dict = [op.to_dict() for op in opinions]
            
            logger.info(f"✅ Crawled {len(opinions_dict)} opinions with full content")
            
            task = self.complete_task(current_task, {
                'opinions_count': len(opinions_dict)
            })
            
            state = self.update_state(state, {
                'current_task': task,
                'opinions_raw': opinions_dict
            })
            
            return state
            
        except Exception as e:
            logger.error(f"Opinion crawler error: {str(e)}")
            return self.log_error(state, f"Opinion crawling failed: {str(e)}")


class NLPAnalysisAgent(BaseAgent):
    """Agent phân tích NLP với Sentiment + Stance + Topics"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.CONTENT_EXTRACTOR,
            name="NLP Analysis Agent",
            description="Analyzes opinions with NLP (sentiment, stance, topics)"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"🧠 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.NLP_ANALYSIS:
                return state
            
            opinions_raw = state.get('opinions_raw', [])
            if not opinions_raw:
                error_msg = "No opinions to analyze"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)
            
            topic = state['project_name']
            
            logger.info(f"🧠 Analyzing {len(opinions_raw)} opinions with NLP...")
            
            analyzed_opinions = []
            
            for i, opinion in enumerate(opinions_raw, 1):
                logger.info(f"Analyzing opinion {i}/{len(opinions_raw)}")
                
                content = opinion.get('content', '')
                if not content or len(content) < 50:
                    continue
                
                # Full NLP analysis
                analysis = nlp_analyzer.analyze_full(
                    text=content,
                    topic=topic,
                    include_entities=(i == 1)  # Only first one
                )
                
                # Merge analysis với opinion
                analyzed = {**opinion, **analysis}
                analyzed_opinions.append(analyzed)
            
            logger.info(f"✅ NLP analysis complete: {len(analyzed_opinions)} opinions analyzed")
            
            # Statistics
            sentiments = {}
            stances = {}
            
            for op in analyzed_opinions:
                sent = op.get('sentiment', 'neutral')
                sentiments[sent] = sentiments.get(sent, 0) + 1
                
                stance = op.get('stance', {}).get('stance', 'neutral')
                stances[stance] = stances.get(stance, 0) + 1
            
            logger.info(f"📊 Sentiments: {sentiments}")
            logger.info(f"📊 Stances: {stances}")
            
            task = self.complete_task(current_task, {
                'analyzed_count': len(analyzed_opinions),
                'sentiments': sentiments,
                'stances': stances
            })
            
            state = self.update_state(state, {
                'current_task': task,
                'analyzed_opinions': analyzed_opinions
            })
            
            return state
            
        except Exception as e:
            logger.error(f"NLP analysis error: {str(e)}")
            return self.log_error(state, f"NLP analysis failed: {str(e)}")


class PDFContentExtractorAgent(BaseAgent):
    """Agent extract content từ multiple PDFs"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.CONTENT_EXTRACTOR,
            name="PDF Content Extractor Agent",
            description="Extracts content and keywords from PDFs"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"📄 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.EXTRACT_PDF_CONTENT:
                return state
            
            pdf_paths = current_task.input_data.get('pdf_paths', state.get('pdf_paths', []))
            if not pdf_paths:
                error_msg = "No PDF paths to extract"
                task = self.complete_task(current_task, {}, error=error_msg)
                return self.log_error(state, error_msg)
            
            logger.info(f"📄 Extracting content from {len(pdf_paths)} PDFs...")
            
            # Combine all PDF content
            from tools.pdf_extractor import pdf_extractor_tool
            all_text = []
            
            for i, pdf_path in enumerate(pdf_paths[:10], 1):  # Limit to 10 PDFs
                logger.info(f"Extracting PDF {i}/{min(len(pdf_paths), 10)}")
                
                # Extract all content
                result = pdf_extractor_tool.extract_all(pdf_path)
                
                if result.success:
                    text = result.data.get('text', '')
                    all_text.append(text)
            
            # Combine all text
            combined_text = "\n\n".join(all_text)
            
            logger.info(f"📝 Combined text: {len(combined_text)} characters")
            
            # Extract keywords từ combined text
            keywords_result = pdf_extractor_tool.extract_keywords(combined_text, max_keywords=50)
            phrases_result = pdf_extractor_tool.extract_key_phrases(combined_text, max_phrases=20)
            
            if keywords_result.success and phrases_result.success:
                keywords = keywords_result.data.get('keywords', [])
                key_phrases = phrases_result.data.get('key_phrases', [])
                
                extracted_keywords = ExtractedKeywords(
                    main_keywords=keywords[:20],
                    key_phrases=key_phrases[:20],
                    entities=[],
                    summary=f"Extracted from {len(pdf_paths)} PDFs"
                )
                
                logger.info(f"✅ Extracted {len(keywords)} keywords, {len(key_phrases)} phrases")
                
                task = self.complete_task(current_task, {
                    'keywords_count': len(keywords),
                    'phrases_count': len(key_phrases),
                    'total_chars': len(combined_text)
                })
                
                state = self.update_state(state, {
                    'current_task': task,
                    'extracted_keywords': extracted_keywords,
                    'pdf_combined_text': combined_text[:100000]  # Store first 100K chars
                })
            else:
                error_msg = keywords_result.error or phrases_result.error
                task = self.complete_task(current_task, {}, error=error_msg)
                state = self.log_error(state, error_msg)
            
            return state
            
        except Exception as e:
            logger.error(f"PDF content extraction error: {str(e)}")
            current_task = state.get('current_task')
            if current_task:
                task = self.complete_task(current_task, {}, error=str(e))
                state = self.update_state(state, {'current_task': task})
            return self.log_error(state, f"PDF extraction failed: {str(e)}")


class VectorDBStorageAgent(BaseAgent):
    """Agent lưu PDFs vào Vector DB"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.CONTENT_EXTRACTOR,
            name="Vector DB Storage Agent",
            description="Stores PDF content in Vector DB"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"💾 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.STORE_VECTOR_DB:
                return state
            
            pdf_text = state.get('pdf_combined_text', '')
            if not pdf_text:
                logger.warning("No PDF text to store, skipping Vector DB")
                task = self.complete_task(current_task, {'stored': False})
                state = self.update_state(state, {'current_task': task})
                return state
            
            project_name = state['project_name']
            collection_name = project_name.replace(' ', '_').replace(',', '')
            
            logger.info(f"💾 Storing PDF content in Vector DB: {collection_name}")
            
            # Store in Vector DB
            from tools.vector_db import vector_db_tool
            from sentence_transformers import SentenceTransformer
            
            # Generate embeddings
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            embeddings = model.encode([pdf_text[:10000]], convert_to_numpy=True)  # First 10K chars
            
            # Store
            result = vector_db_tool.add_documents(
                collection_name=collection_name,
                documents=[pdf_text[:10000]],
                embeddings=embeddings,
                metadatas=[{
                    'type': 'law_document',
                    'project': project_name,
                    'source': 'pdf'
                }],
                ids=['law_document_main']
            )
            
            if result.success:
                logger.info("✅ PDF content stored in Vector DB")
                
                task = self.complete_task(current_task, {
                    'collection_name': collection_name,
                    'stored': True
                })
                
                state = self.update_state(state, {
                    'current_task': task,
                    'vector_db_collection': collection_name
                })
            else:
                logger.warning(f"Vector DB storage failed: {result.error}")
                task = self.complete_task(current_task, {'stored': False})
                state = self.update_state(state, {'current_task': task})
            
            return state
            
        except Exception as e:
            logger.error(f"Vector DB storage error: {str(e)}")
            current_task = state.get('current_task')
            if current_task:
                task = self.complete_task(current_task, {}, error=str(e))
                state = self.update_state(state, {'current_task': task})
            return self.log_error(state, f"Vector DB storage failed: {str(e)}")


class HybridExporterAgent(BaseAgent):
    """Agent export analyzed opinions ra CSV"""
    
    def __init__(self):
        super().__init__(
            role=AgentRole.SCRAPER_AGENT,
            name="Hybrid Exporter Agent",
            description="Exports analyzed opinions to CSV"
        )
    
    async def execute(self, state: AgentState) -> AgentState:
        try:
            logger.info(f"💾 {self.name} executing...")
            
            current_task = state.get('current_task')
            if not current_task or current_task.task_type != TaskType.EXPORT_DATA:
                return state
            
            analyzed_opinions = state.get('analyzed_opinions', [])
            if not analyzed_opinions:
                logger.warning("No analyzed opinions to export")
                task = self.complete_task(current_task, {'exported': False})
                state = self.update_state(state, {
                    'current_task': task,
                    'is_complete': True
                })
                return state
            
            logger.info(f"💾 Exporting {len(analyzed_opinions)} analyzed opinions...")
            
            # Export to CSV
            from tools.csv_exporter import csv_exporter_tool
            
            project_name = state['project_name'].replace(' ', '_').replace(',', '')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{project_name}_opinions_{timestamp}.csv"
            
            result = csv_exporter_tool.export_dict_list(analyzed_opinions, filename)
            
            if result.success:
                csv_path = result.data['filepath']
                logger.info(f"✅ Exported to: {csv_path}")
                
                task = self.complete_task(current_task, {
                    'csv_path': csv_path,
                    'opinions_count': len(analyzed_opinions)
                })
                
                state = self.update_state(state, {
                    'current_task': task,
                    'csv_output_path': csv_path,
                    'is_complete': True
                })
            else:
                task = self.complete_task(current_task, {}, error=result.error)
                state = self.update_state(state, {
                    'current_task': task,
                    'is_complete': True
                })
                state = self.log_error(state, result.error)
            
            return state
            
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
            current_task = state.get('current_task')
            if current_task:
                task = self.complete_task(current_task, {}, error=str(e))
                state = self.update_state(state, {
                    'current_task': task,
                    'is_complete': True
                })
            return self.log_error(state, f"Export failed: {str(e)}")


# Singleton instances
law_list_search_agent = LawListSearchAgent()
pdf_download_agent = PDFDownloadAgent()
pdf_content_extractor_agent = PDFContentExtractorAgent()
vector_db_storage_agent = VectorDBStorageAgent()
enhanced_opinion_search_agent = EnhancedOpinionSearchAgent()
enhanced_opinion_crawler_agent = EnhancedOpinionCrawlerAgent()
nlp_analysis_agent = NLPAnalysisAgent()
hybrid_exporter_agent = HybridExporterAgent()
