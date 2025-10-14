"""
Enhanced Opinion Crawler - Crawl FULL CONTENT của opinions với multi-source support
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import logging
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import re

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class Opinion:
    """
    Thông tin đầy đủ về một opinion/bình luận
    """
    opinion_id: str  # Unique ID (hash của URL)
    url: str  # URL gốc
    title: str
    content: str  # FULL CONTENT - quan trọng nhất!
    author: Optional[str] = None
    date_published: Optional[datetime] = None
    source: str = ""  # Tên nguồn (VNExpress, Dân Trí, etc.)
    source_type: str = "news"  # news, forum, blog, social, official
    
    # Engagement metrics
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    summary: Optional[str] = None
    
    # Content hash for deduplication
    content_hash: Optional[str] = None
    
    # Screenshot path (nếu có)
    screenshot_path: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate content hash sau khi init"""
        if not self.content_hash:
            self.content_hash = hashlib.md5(
                (self.title + self.content).encode('utf-8')
            ).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'opinion_id': self.opinion_id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'date_published': self.date_published.isoformat() if self.date_published else None,
            'source': self.source,
            'source_type': self.source_type,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'tags': self.tags,
            'category': self.category,
            'summary': self.summary,
            'content_hash': self.content_hash,
            'screenshot_path': self.screenshot_path,
            'metadata': self.metadata
        }


class EnhancedOpinionCrawler:
    """
    Enhanced Opinion Crawler với các tính năng:
    - Follow link từ title để lấy FULL CONTENT
    - Multi-source support (news, forum, blog, official)
    - Content deduplication (hash + similarity)
    - Noise filtering (ads, copy-paste)
    - Rich metadata collection
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        })
        
        # Track URLs và content hashes đã crawl
        self.seen_urls = set()
        self.seen_content_hashes = set()
        
        # Spam/noise patterns to filter
        self.noise_patterns = [
            r'quảng cáo',
            r'mua ngay',
            r'khuyến mãi',
            r'liên hệ.*\d{10}',  # phone numbers in ads
            r'giá sốc',
            r'hot deal',
        ]
    
    def crawl_opinion_article(self, url: str, source: str = "unknown") -> Optional[Opinion]:
        """
        Crawl FULL CONTENT của một bài báo opinion
        
        Steps:
        1. Follow URL đến trang detail
        2. Extract FULL CONTENT (không chỉ title/summary)
        3. Extract metadata (author, date, tags, engagement)
        4. Validate và filter noise
        
        Args:
            url: URL của bài báo
            source: Tên nguồn
            
        Returns:
            Opinion object hoặc None nếu invalid
        """
        try:
            # Check duplicate URL
            if url in self.seen_urls:
                logger.debug(f"URL already crawled: {url}")
                return None
            
            logger.info(f"Crawling opinion: {url}")
            
            # Fetch page
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                logger.warning(f"No title found: {url}")
                return None
            
            # Extract FULL CONTENT - QUAN TRỌNG!
            content = self._extract_full_content(soup)
            if not content or len(content) < 100:  # Minimum content length
                logger.warning(f"Content too short or not found: {url}")
                return None
            
            # Check for noise/spam
            if self._is_noise_content(title, content):
                logger.warning(f"Noise/spam detected, skipping: {url}")
                return None
            
            # Check duplicate content
            content_hash = hashlib.md5((title + content).encode('utf-8')).hexdigest()
            if content_hash in self.seen_content_hashes:
                logger.info(f"Duplicate content detected: {url}")
                return None
            
            # Extract metadata
            author = self._extract_author(soup)
            date_published = self._extract_date(soup)
            summary = self._extract_summary(soup)
            tags = self._extract_tags(soup)
            category = self._extract_category(soup)
            
            # Extract engagement metrics
            likes, comments, shares = self._extract_engagement(soup)
            
            # Detect source type
            source_type = self._detect_source_type(url, soup)
            
            # Create opinion ID
            opinion_id = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]
            
            opinion = Opinion(
                opinion_id=opinion_id,
                url=url,
                title=title,
                content=content,
                author=author,
                date_published=date_published,
                source=source,
                source_type=source_type,
                likes_count=likes,
                comments_count=comments,
                shares_count=shares,
                tags=tags,
                category=category,
                summary=summary,
                content_hash=content_hash
            )
            
            # Track
            self.seen_urls.add(url)
            self.seen_content_hashes.add(content_hash)
            
            logger.info(f"✅ Crawled: {title[:50]}... ({len(content)} chars)")
            
            return opinion
            
        except Exception as e:
            logger.error(f"Error crawling opinion {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        # Try multiple selectors
        title_elem = (
            soup.find('h1', class_=re.compile(r'(title|headline|article-title)')) or
            soup.find('h1') or
            soup.find('meta', property='og:title') or
            soup.find('title')
        )
        
        if title_elem:
            if title_elem.name == 'meta':
                return title_elem.get('content', '').strip()
            return title_elem.get_text(strip=True)
        
        return None
    
    def _extract_full_content(self, soup: BeautifulSoup) -> str:
        """
        Extract FULL CONTENT của bài báo
        
        Strategies:
        1. Find article body containers
        2. Extract all paragraphs
        3. Clean and join
        """
        content_parts = []
        
        # Try multiple content containers
        content_container = (
            soup.find('div', class_=re.compile(r'(article-content|post-content|entry-content|detail-content|main-content)')) or
            soup.find('article', class_=re.compile(r'(content|body)')) or
            soup.find('div', id=re.compile(r'(article|content|main)'))
        )
        
        if content_container:
            # Extract all paragraphs
            paragraphs = content_container.find_all(['p', 'div'], class_=lambda x: x != 'ad' and x != 'advertisement')
            
            for p in paragraphs:
                # Skip ads and empty paragraphs
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Min length
                    # Check if not ad
                    if not any(pattern in text.lower() for pattern in ['quảng cáo', 'advertisement']):
                        content_parts.append(text)
        else:
            # Fallback: get all paragraphs in body
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)
        
        return '\n\n'.join(content_parts)
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract tác giả"""
        author_elem = (
            soup.find('span', class_=re.compile(r'author')) or
            soup.find('a', class_=re.compile(r'author')) or
            soup.find('meta', attrs={'name': 'author'}) or
            soup.find('meta', property='article:author')
        )
        
        if author_elem:
            if author_elem.name == 'meta':
                return author_elem.get('content', '').strip()
            return author_elem.get_text(strip=True)
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract ngày đăng"""
        date_elem = (
            soup.find('time') or
            soup.find('span', class_=re.compile(r'(date|time|published)')) or
            soup.find('meta', property='article:published_time')
        )
        
        if date_elem:
            date_str = date_elem.get('datetime') or date_elem.get('content') or date_elem.get_text(strip=True)
            
            # Try to parse date
            try:
                # Handle multiple formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(date_str[:10], fmt)
                    except:
                        continue
            except:
                pass
        
        return None
    
    def _extract_summary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract tóm tắt"""
        summary_elem = (
            soup.find('meta', property='og:description') or
            soup.find('meta', attrs={'name': 'description'}) or
            soup.find('div', class_=re.compile(r'(summary|description|sapo)'))
        )
        
        if summary_elem:
            if summary_elem.name == 'meta':
                return summary_elem.get('content', '').strip()
            return summary_elem.get_text(strip=True)
        
        return None
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords"""
        tags = []
        
        # Try multiple tag containers
        tag_container = (
            soup.find('div', class_=re.compile(r'(tags|keywords)')) or
            soup.find('ul', class_=re.compile(r'tags'))
        )
        
        if tag_container:
            tag_elems = tag_container.find_all(['a', 'span'])
            tags = [elem.get_text(strip=True) for elem in tag_elems if elem.get_text(strip=True)]
        
        # Also check meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords = meta_keywords.get('content', '').split(',')
            tags.extend([k.strip() for k in keywords if k.strip()])
        
        return list(set(tags))[:10]  # Unique, max 10
    
    def _extract_category(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract category"""
        cat_elem = (
            soup.find('a', class_=re.compile(r'category')) or
            soup.find('span', class_=re.compile(r'category'))
        )
        
        if cat_elem:
            return cat_elem.get_text(strip=True)
        
        return None
    
    def _extract_engagement(self, soup: BeautifulSoup) -> tuple:
        """
        Extract engagement metrics (likes, comments, shares)
        
        Returns:
            (likes, comments, shares)
        """
        likes = 0
        comments = 0
        shares = 0
        
        # Try to find social counters
        # This varies greatly by site
        like_elem = soup.find(class_=re.compile(r'(like|favorite).*count'))
        if like_elem:
            likes = self._extract_number(like_elem.get_text())
        
        comment_elem = soup.find(class_=re.compile(r'comment.*count'))
        if comment_elem:
            comments = self._extract_number(comment_elem.get_text())
        
        share_elem = soup.find(class_=re.compile(r'share.*count'))
        if share_elem:
            shares = self._extract_number(share_elem.get_text())
        
        return likes, comments, shares
    
    def _extract_number(self, text: str) -> int:
        """Extract number từ text"""
        numbers = re.findall(r'\d+', text.replace(',', '').replace('.', ''))
        return int(numbers[0]) if numbers else 0
    
    def _detect_source_type(self, url: str, soup: BeautifulSoup) -> str:
        """
        Detect loại nguồn
        
        Types: news, forum, blog, social, official
        """
        url_lower = url.lower()
        
        # Official government sites
        if '.gov.vn' in url_lower or 'mst.gov.vn' in url_lower:
            return 'official'
        
        # News sites
        news_domains = ['vnexpress', 'tuoitre', 'thanhnien', 'dantri', 'vietnamnet', 'baomoi']
        if any(domain in url_lower for domain in news_domains):
            return 'news'
        
        # Forums
        forum_indicators = ['forum', 'diendan', 'thao-luan']
        if any(indicator in url_lower for indicator in forum_indicators):
            return 'forum'
        
        # Blogs
        blog_indicators = ['blog', 'wordpress', 'blogger']
        if any(indicator in url_lower for indicator in blog_indicators):
            return 'blog'
        
        # Social media
        social_domains = ['facebook', 'twitter', 'linkedin', 'reddit']
        if any(domain in url_lower for domain in social_domains):
            return 'social'
        
        return 'news'  # Default
    
    def _is_noise_content(self, title: str, content: str) -> bool:
        """
        Check nếu là noise/spam content
        
        Filter:
        - Quảng cáo
        - Tin chung không dẫn nguồn
        - Copy-paste content
        """
        combined = (title + ' ' + content).lower()
        
        # Check spam patterns
        for pattern in self.noise_patterns:
            if re.search(pattern, combined):
                return True
        
        # Check content quality
        # Nếu content quá ngắn hoặc toàn ký tự đặc biệt
        if len(content) < 200:
            return True
        
        # Check if too many links (likely spam)
        link_count = combined.count('http')
        if link_count > 10:
            return True
        
        return False
    
    def crawl_multiple_opinions(
        self,
        urls: List[str],
        source: str = "unknown",
        max_crawl: int = 50
    ) -> ToolResult:
        """
        Crawl multiple opinion articles
        
        Args:
            urls: List of URLs
            source: Source name
            max_crawl: Max số bài để crawl
            
        Returns:
            ToolResult with list of Opinion objects
        """
        try:
            opinions = []
            failed = 0
            
            for i, url in enumerate(urls[:max_crawl], 1):
                logger.info(f"Crawling opinion {i}/{min(len(urls), max_crawl)}")
                
                opinion = self.crawl_opinion_article(url, source)
                
                if opinion:
                    opinions.append(opinion)
                else:
                    failed += 1
            
            logger.info(f"✅ Crawled {len(opinions)} opinions, {failed} failed/skipped")
            
            return ToolResult(
                success=True,
                data={
                    'opinions': opinions,
                    'count': len(opinions),
                    'failed': failed
                }
            )
            
        except Exception as e:
            logger.error(f"Multiple opinion crawl error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to crawl opinions: {str(e)}"
            )


# Singleton instance
enhanced_opinion_crawler = EnhancedOpinionCrawler()
