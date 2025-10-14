"""
Law List Crawler (Selenium version) - Crawl danh sách dự thảo luật
Crawl từ: https://duthaoonline.quochoi.vn/du-thao
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import logging
import time

from core.types import ToolResult
from core.config import config

logger = logging.getLogger(__name__)


@dataclass
class DocumentCard:
    """Thông tin về một văn bản luật"""
    doc_id: str
    title: str
    url: str
    pdf_url: Optional[str]
    html_url: Optional[str]
    date_published: Optional[str]
    status: Optional[str]
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
    Crawl danh sách dự thảo luật từ duthaoonline.quochoi.vn
    Sử dụng Selenium để xử lý JavaScript dynamic content
    """
    
    def __init__(self):
        self.base_url = "https://duthaoonline.quochoi.vn/du-thao"
        self.driver = None
    
    def _setup_driver(self):
        """Setup Chrome driver với headless mode"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Chạy ngầm
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            logger.info("✅ Chrome driver initialized (headless mode)")
            
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise
    
    def _cleanup_driver(self):
        """Đóng driver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Chrome driver closed")
            except Exception as e:
                logger.warning(f"Error closing driver: {str(e)}")
    
    def _calculate_similarity(self, a: str, b: str) -> float:
        """
        Tính độ tương đồng giữa 2 chuỗi
        Return: float 0.0 - 1.0
        """
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def _extract_pdf_url_from_detail_page(self, detail_url: str) -> Optional[str]:
        """
        Truy cập vào trang chi tiết để lấy PDF URL (nếu có)
        """
        try:
            self.driver.get(detail_url)
            time.sleep(2)  # Wait for page load
            
            # Tìm link PDF (có thể có class 'btn-download' hoặc href chứa .pdf)
            pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute('href')
                logger.info(f"  → Found PDF: {pdf_url}")
                return pdf_url
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting PDF from {detail_url}: {str(e)}")
            return None
    
    def crawl_law_list(
        self,
        topic: str,
        source: str = 'duthaoonline',
        max_pages: int = 5,
        max_results: int = 30,
        similarity_threshold: float = 0.3
    ) -> ToolResult:
        """
        Crawl danh sách dự thảo luật từ duthaoonline.quochoi.vn
        
        Args:
            topic: Chủ đề/từ khóa tìm kiếm
            source: Nguồn (mặc định 'duthaoonline')
            max_pages: Số trang tối đa (hiện tại chỉ 1 trang)
            max_results: Số kết quả tối đa
            similarity_threshold: Ngưỡng độ tương đồng (0.0-1.0)
        
        Returns:
            ToolResult với list DocumentCard
        """
        try:
            logger.info(f"🔍 Crawling law list for topic: '{topic}'")
            logger.info(f"📍 Source: {self.base_url}")
            logger.info(f"🎯 Similarity threshold: {similarity_threshold}")
            
            # Setup driver
            self._setup_driver()
            
            # Navigate to page
            logger.info(f"🌐 Loading page: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for content to load (wait for .col-10 elements)
            logger.info("⏳ Waiting for content to load...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "col-10"))
                )
                time.sleep(3)  # Extra wait for JS rendering
                logger.info("✅ Page loaded successfully")
                
            except TimeoutException:
                logger.error("❌ Timeout waiting for content")
                self._cleanup_driver()
                return ToolResult(
                    success=False,
                    error="Timeout: Page did not load in time"
                )
            
            # Find all article elements
            articles = self.driver.find_elements(By.CLASS_NAME, "col-10")
            logger.info(f"📄 Found {len(articles)} articles on page")
            
            if not articles:
                self._cleanup_driver()
                return ToolResult(
                    success=False,
                    error="No articles found on page"
                )
            
            # Process each article
            documents = []
            processed_urls = set()
            
            for idx, article in enumerate(articles, 1):
                try:
                    # Find link and title
                    link_elem = article.find_element(By.CLASS_NAME, "d-inline-block")
                    url = link_elem.get_attribute("href")
                    
                    title_elem = article.find_element(By.TAG_NAME, "h2")
                    title = title_elem.text.strip()
                    
                    if not url or not title:
                        logger.debug(f"  Article {idx}: Missing URL or title, skipping")
                        continue
                    
                    # Check duplicate
                    if url in processed_urls:
                        logger.debug(f"  Article {idx}: Duplicate URL, skipping")
                        continue
                    
                    # Calculate similarity
                    similarity = self._calculate_similarity(topic, title)
                    
                    logger.info(f"📰 Article {idx}/{len(articles)}:")
                    logger.info(f"   Title: {title[:80]}...")
                    logger.info(f"   Similarity: {similarity:.2%}")
                    
                    # Check if meets threshold
                    if similarity >= similarity_threshold:
                        logger.info(f"   ✅ MATCH! (threshold: {similarity_threshold})")
                        
                        # Create document ID
                        doc_id = hashlib.md5(url.encode()).hexdigest()[:16]
                        
                        # Try to extract PDF URL (optional, costs time)
                        pdf_url = None
                        # Uncomment if you want to extract PDF:
                        # if len(documents) < 5:  # Only for first 5 to save time
                        #     pdf_url = self._extract_pdf_url_from_detail_page(url)
                        
                        # Create DocumentCard
                        doc = DocumentCard(
                            doc_id=doc_id,
                            title=title,
                            url=url,
                            pdf_url=pdf_url,
                            html_url=url,
                            date_published=None,  # Can be extracted if needed
                            status="Dự thảo",
                            summary=None,
                            metadata={
                                "source": "duthaoonline.quochoi.vn",
                                "similarity": round(similarity, 3),
                                "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                        )
                        
                        documents.append(doc)
                        processed_urls.add(url)
                        
                        logger.info(f"   💾 Saved: {len(documents)}/{max_results}")
                        
                        # Check if reached max
                        if len(documents) >= max_results:
                            logger.info(f"🎯 Reached max results: {max_results}")
                            break
                    else:
                        logger.info(f"   ❌ Below threshold, skipping")
                
                except Exception as e:
                    logger.warning(f"⚠️ Error processing article {idx}: {str(e)}")
                    continue
            
            # Cleanup
            self._cleanup_driver()
            
            # Check results
            if not documents:
                logger.warning(f"⚠️ No documents matched topic '{topic}' (threshold: {similarity_threshold})")
                logger.warning(f"💡 Try lowering similarity_threshold or use different keywords")
                return ToolResult(
                    success=False,
                    error=f"No documents matched topic '{topic}' with threshold {similarity_threshold}"
                )
            
            logger.info(f"✅ Crawl complete: {len(documents)} documents found")
            
            return ToolResult(
                success=True,
                data={
                    "documents": documents,  # List of DocumentCard objects
                    "count": len(documents),
                    "source": "duthaoonline.quochoi.vn",
                    "topic": topic,
                    "similarity_threshold": similarity_threshold
                },
                message=f"Found {len(documents)} law documents"
            )
        
        except Exception as e:
            logger.error(f"❌ Crawl error: {str(e)}")
            self._cleanup_driver()
            return ToolResult(
                success=False,
                error=f"Crawl failed: {str(e)}"
            )


# Singleton instance
law_list_crawler = LawListCrawler()
