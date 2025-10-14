# 🚀 Hybrid Workflow Implementation Progress

## ✅ Completed Components

### 1. LawListCrawler ✓
**File:** `tools/law_list_crawler.py`

**Features:**
- ✅ Pagination support (auto phân trang)
- ✅ Card detection và metadata extraction
- ✅ Topic-based filtering với relevance scoring
- ✅ Deduplication by doc_id
- ✅ Multi-source support (mst.gov.vn + extensible)

**Usage:**
```python
from tools.law_list_crawler import law_list_crawler

result = law_list_crawler.crawl_law_list(
    topic="Luật Khoa học công nghệ 2025",
    source='mst',
    max_pages=5,
    max_results=20
)

documents = result.data['documents']  # List[DocumentCard]
```

---

### 2. PDFDownloader ✓
**File:** `tools/pdf_downloader.py`

**Features:**
- ✅ SHA256 hash-based deduplication
- ✅ Metadata tracking (JSON database)
- ✅ Duplicate detection (by URL and hash)
- ✅ Batch download support
- ✅ Validation (file size, content type)
- ✅ Orphaned file cleanup

**Usage:**
```python
from tools.pdf_downloader import pdf_downloader

# Single PDF
result = pdf_downloader.download_pdf(
    url="https://example.com/law.pdf",
    doc_id="doc123"
)

# Multiple PDFs
result = pdf_downloader.download_multiple_pdfs(
    documents=document_list,
    max_downloads=10
)
```

---

### 3. EnhancedOpinionCrawler ✓
**File:** `tools/enhanced_opinion_crawler.py`

**Features:**
- ✅ FULL CONTENT extraction (not just title)
- ✅ Follow links to detail pages
- ✅ Multi-source detection (news, forum, blog, official, social)
- ✅ Noise filtering (ads, spam, copy-paste)
- ✅ Rich metadata collection:
  - Title, author, date
  - Full content (paragraphs joined)
  - Engagement (likes, comments, shares)
  - Tags, category
  - Content hash for dedup
- ✅ Content deduplication (hash-based)
- ✅ Source type detection

**Usage:**
```python
from tools.enhanced_opinion_crawler import enhanced_opinion_crawler

# Single opinion
opinion = enhanced_opinion_crawler.crawl_opinion_article(
    url="https://vnexpress.net/article-123",
    source="VNExpress"
)

# Multiple opinions
result = enhanced_opinion_crawler.crawl_multiple_opinions(
    urls=url_list,
    source="VNExpress",
    max_crawl=50
)
```

**Opinion Object:**
```python
@dataclass
class Opinion:
    opinion_id: str
    url: str
    title: str
    content: str  # FULL CONTENT!
    author: str
    date_published: datetime
    source: str
    source_type: str  # news/forum/blog/official/social
    likes_count: int
    comments_count: int
    shares_count: int
    tags: List[str]
    category: str
    summary: str
    content_hash: str
    screenshot_path: str  # Optional
    metadata: Dict
```

---

## 🔨 In Progress

### 4. NLP Analyzer (Enhanced) 🔨
**Status:** In progress

**Planned Features:**
- Sentiment analysis (positive/negative/neutral)
- Stance detection (support/oppose/neutral)
- Topic modeling (LDA or BERTopic)
- Entity recognition
- Text normalization

---

## 📋 TODO

### 5. Update Agents for Hybrid Workflow
**Files to modify:**
- `agents/dev.py` - Update PDF-related agents
- `agents/res.py` - Update search/scraper agents
- Create new agents if needed

### 6. Update Workflow Routing
**Files to modify:**
- `core/auto.py` - Add new task types and routing
- `core/types.py` - Add new TaskTypes
- `agents/manager.py` - Update workflow logic

### 7. Create Test Script
**File:** `test_hybrid_workflow.py`

---

## 🎯 Hybrid Workflow Flow

```
INPUT: Topic name
   ↓
1. SEARCH_LAW_LIST (pagination, card detection)
   Output: List[DocumentCard] with PDF URLs
   ↓
2. DOWNLOAD_PDFs (hash dedup, batch download)
   Output: List[PDF paths]
   ↓
3. EXTRACT_PDF_CONTENT (structured extraction)
   Output: Full text, keywords, metadata
   ↓
4. STORE_VECTOR_DB (embeddings, similarity search)
   Output: Vector collection
   ↓
5. SEARCH_OPINIONS (based on keywords)
   Output: List[URLs]
   ↓
6. CRAWL_OPINIONS_FULL_CONTENT (follow links, extract full)
   Output: List[Opinion] with full content
   ↓
7. NLP_ANALYSIS (sentiment + stance + topics)
   Output: Analyzed opinions with labels
   ↓
8. EXPORT (CSV + Vector DB)
   Output: CSV file with all data
```

---

## 📊 Data Structure

### DocumentCard (from LawListCrawler)
```python
{
    'doc_id': str,
    'title': str,
    'url': str,
    'pdf_url': str,
    'html_url': str,
    'date_published': str,
    'status': str,
    'summary': str,
    'metadata': dict
}
```

### Opinion (from EnhancedOpinionCrawler)
```python
{
    'opinion_id': str,
    'url': str,
    'title': str,
    'content': str,  # FULL!
    'author': str,
    'date_published': datetime,
    'source': str,
    'source_type': str,
    'likes_count': int,
    'comments_count': int,
    'shares_count': int,
    'tags': List[str],
    'category': str,
    'summary': str,
    'content_hash': str,
    'metadata': dict
}
```

---

## 🔜 Next Steps

1. ✅ Create NLP analyzer with stance detection
2. ⏳ Update agents to use new tools
3. ⏳ Update workflow routing
4. ⏳ Create comprehensive test
5. ⏳ Documentation

---

## 📝 Notes

- **Deduplication:** 3 levels
  1. PDF: SHA256 hash
  2. Opinion URLs: URL tracking
  3. Opinion Content: MD5 hash of title+content

- **Noise Filtering:** 
  - Ad patterns
  - Min content length (200 chars)
  - Max link count (< 10)
  - Source validation

- **Multi-source Ready:**
  - News: VNExpress, Tuổi Trẻ, etc.
  - Forum: Custom parsers
  - Blog: Generic parser
  - Official: .gov.vn sites
  - Social: API integration ready

---

**Last Updated:** 2025-10-14
**Status:** 60% Complete
