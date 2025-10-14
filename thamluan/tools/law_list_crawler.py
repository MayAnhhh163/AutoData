"""
Law List Crawler - Crawl danh sách dự thảo luật với pagination
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
import logging
from dataclasses import dataclass
from datetime import datetime
import hashlib

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class DocumentCard:
    """Thông tin về một văn bản luật từ danh sách"""
    doc_id: str  # Unique ID (từ URL hoặc hash)
    title: str
    url: str  # URL chi tiết
    pdf_url: Optional[str]  # URL PDF nếu có
    html_url: Optional[str]  # URL HTML nếu có
    date_published: Optional[str]
    status: Optional[str]  # "Dự thảo", "Đang lấy ý kiến", "Đã ban hành"
    summary: Optional[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'html_url': self.html_url,
            'date_published': self.date_published,
            'status': self.status,
            'summary': self.summary,
            'metadata': self.metadata
        }


class LawListCrawler:
    """
    Crawler danh sách dự thảo luật với các tính năng:
    - Pagination tự động
    - Card detection và metadata extraction
    - Topic filtering
    - Deduplication
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        })
        self.seen_docs = set()  # Track doc_ids đã thấy
        
        # Các trang danh sách dự thảo luật
        self.law_sites = {
            'mst': {
                'name': 'Bộ KH&CN',
                'list_url': 'https://mst.gov.vn/van-ban-phap-luat/du-thao',
                'search_url': 'https://mst.gov.vn/tra-cuu/Pages/timkiem.aspx?keyword={query}',
                'parser': self._parse_mst_list
            },
            # Có thể thêm các nguồn khác
        }
    
    def crawl_law_list(
        self, 
        topic: str,
        source: str = 'mst',
        max_pages: int = 5,
        max_results: int = 50
    ) -> ToolResult:
        """
        Crawl danh sách văn bản luật theo topic
        
        Args:
            topic: Chủ đề tìm kiếm
            source: Nguồn crawl ('mst', ...)
            max_pages: Số trang tối đa
            max_results: Số kết quả tối đa
            
        Returns:
            ToolResult với list DocumentCards
        """
        try:
            logger.info(f"Crawling law list for topic: {topic}")
            
            if source not in self.law_sites:
                return ToolResult(
                    success=False,
                    error=f"Unknown source: {source}"
                )
            
            site_info = self.law_sites[source]
            documents = []
            
            # Crawl với pagination
            for page in range(1, max_pages + 1):
                logger.info(f"Crawling page {page}/{max_pages}...")
                
                page_docs = self._crawl_page(site_info, topic, page)
                
                if not page_docs:
                    logger.info(f"No more results at page {page}, stopping")
                    break
                
                # Filter theo topic relevance
                relevant_docs = self._filter_by_topic(page_docs, topic)
                documents.extend(relevant_docs)
                
                logger.info(f"  → Found {len(relevant_docs)} relevant documents")
                
                if len(documents) >= max_results:
                    documents = documents[:max_results]
                    break
            
            # Deduplication
            unique_docs = self._deduplicate_documents(documents)
            
            logger.info(f"✅ Total: {len(unique_docs)} unique documents")
            
            return ToolResult(
                success=True,
                data={
                    'documents': unique_docs,
                    'count': len(unique_docs),
                    'source': source
                }
            )
            
        except Exception as e:
            logger.error(f"Law list crawl error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to crawl law list: {str(e)}"
            )
    
    def _crawl_page(
        self,
        site_info: Dict,
        topic: str,
        page: int
    ) -> List[DocumentCard]:
        """Crawl một trang danh sách"""
        try:
            # Build URL với query và page number
            if '{query}' in site_info.get('search_url', ''):
                url = site_info['search_url'].format(query=quote_plus(topic))
                if page > 1:
                    url += f"&page={page}"
            else:
                url = site_info['list_url']
                if page > 1:
                    url += f"?page={page}"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Parse documents
            parser = site_info['parser']
            documents = parser(soup, site_info['name'])
            
            return documents
            
        except Exception as e:
            logger.error(f"Error crawling page {page}: {str(e)}")
            return []
    
    def _parse_mst_list(self, soup: BeautifulSoup, source: str) -> List[DocumentCard]:
        """Parse danh sách từ mst.gov.vn"""
        documents = []
        
        # Tìm các card/item văn bản
        # Thử nhiều selectors khác nhau
        items = (
            soup.find_all('div', class_='item') or
            soup.find_all('div', class_='document-item') or
            soup.find_all('li', class_='search-result') or
            soup.find_all('article')
        )
        
        for item in items:
            try:
                # Extract title và link
                title_elem = (
                    item.find('h3') or 
                    item.find('h2') or 
                    item.find('a', class_='title') or
                    item.find('a')
                )
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                if not url or not title:
                    continue
                
                # Make absolute URL
                url = urljoin('https://mst.gov.vn', url)
                
                # Generate doc_id từ URL
                doc_id = hashlib.md5(url.encode()).hexdigest()[:16]
                
                # Extract PDF/HTML links
                pdf_url = None
                html_url = None
                
                # Tìm link PDF
                pdf_link = item.find('a', href=lambda x: x and '.pdf' in x.lower())
                if pdf_link:
                    pdf_url = urljoin('https://mst.gov.vn', pdf_link['href'])
                
                # Extract date
                date_published = None
                date_elem = (
                    item.find('span', class_='date') or
                    item.find('time') or
                    item.find('span', class_='publish-date')
                )
                if date_elem:
                    date_published = date_elem.get_text(strip=True)
                
                # Extract summary
                summary = None
                summary_elem = (
                    item.find('p', class_='summary') or
                    item.find('div', class_='description') or
                    item.find('p')
                )
                if summary_elem:
                    summary = summary_elem.get_text(strip=True)
                
                # Extract status
                status = None
                status_elem = item.find('span', class_='status')
                if status_elem:
                    status = status_elem.get_text(strip=True)
                
                doc = DocumentCard(
                    doc_id=doc_id,
                    title=title,
                    url=url,
                    pdf_url=pdf_url,
                    html_url=html_url if not pdf_url else None,
                    date_published=date_published,
                    status=status,
                    summary=summary,
                    metadata={'source': source}
                )
                
                documents.append(doc)
                
            except Exception as e:
                logger.warning(f"Error parsing document item: {str(e)}")
                continue
        
        return documents
    
    def _filter_by_topic(
        self,
        documents: List[DocumentCard],
        topic: str
    ) -> List[DocumentCard]:
        """Lọc documents theo độ liên quan với topic"""
        topic_lower = topic.lower()
        topic_keywords = set(topic_lower.split())
        
        relevant_docs = []
        
        for doc in documents:
            # Calculate relevance score
            title_lower = doc.title.lower()
            summary_lower = (doc.summary or '').lower()
            combined = title_lower + ' ' + summary_lower
            
            # Count keyword matches
            score = sum(1 for kw in topic_keywords if kw in combined)
            
            # Bonus nếu match trong title
            if any(kw in title_lower for kw in topic_keywords):
                score += 2
            
            # Keep if có ít nhất 1 keyword match
            if score > 0:
                doc.metadata['relevance_score'] = score
                relevant_docs.append(doc)
        
        # Sort by relevance score
        relevant_docs.sort(key=lambda x: x.metadata.get('relevance_score', 0), reverse=True)
        
        return relevant_docs
    
    def _deduplicate_documents(
        self,
        documents: List[DocumentCard]
    ) -> List[DocumentCard]:
        """Remove duplicate documents"""
        seen = set()
        unique = []
        
        for doc in documents:
            if doc.doc_id not in seen:
                seen.add(doc.doc_id)
                unique.append(doc)
        
        return unique


# Singleton instance
law_list_crawler = LawListCrawler()
