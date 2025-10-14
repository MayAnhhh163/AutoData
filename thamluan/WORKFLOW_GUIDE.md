# 📚 Hướng dẫn Workflow Mới (Article-Based)

## 🎯 Tổng Quan

Workflow mới **KHÔNG CẦN PDF** - thay vào đó sẽ:
1. ✅ Tìm tin tức về dự luật
2. ✅ Crawl nội dung tin tức
3. ✅ Extract keywords từ tin tức
4. ✅ Tìm ý kiến công chúng dựa trên keywords
5. ✅ Phân tích sentiment
6. ✅ Export CSV + Vector DB

---

## 🚀 Cách Chạy

### **Option 1: Chạy Test Script**
```bash
cd thamluan
python test_new_workflow.py
```

### **Option 2: Chạy từ main.py (KHÔNG CẦN URL!)**
```bash
cd thamluan
python main.py
```
Chỉ cần nhập **Tên dự luật/chủ đề** khi được hỏi:
- ví dụ: `Luật Khoa học, công nghệ và đổi mới sáng tạo 2025`
- ví dụ: `Luật Đất đai 2025`
- ví dụ: `Nghị định 68/2025 về trí tuệ nhân tạo`

### **Option 3: Command line với topic**
```bash
python main.py --project "Luật Đất đai 2025"
```

### **Option 4: Import trong code**
```python
from core.auto import run_workflow_async
import asyncio

async def main():
    # Chỉ cần topic name - KHÔNG CẦN URL!
    result = await run_workflow_async(
        project_name="Luật Khoa học, công nghệ và đổi mới sáng tạo 2025"
    )
    return result

asyncio.run(main())
```

---

## 🔄 Workflow Flow

```
START
  ↓
[SEARCH_NEWS]
  • Tìm tin tức về dự luật
  • Query: "{project_name}", "{project_name} nội dung", ...
  • Output: 30 URLs tin tức
  ↓
[SCRAPE_NEWS_ARTICLES]
  • Crawl top 20 tin tức
  • Extract: title, content, source
  • Output: news_articles[]
  ↓
[EXTRACT_KEYWORDS_FROM_NEWS]
  • Combine all news content
  • Extract keywords & key phrases
  • Output: ExtractedKeywords
  ↓
[SEARCH_OPINIONS]
  • Tìm ý kiến công chúng
  • Queries dựa trên keywords
  • Relevance scoring
  • Output: search_results[]
  ↓
[SCRAPE_ARTICLES]
  • Crawl opinion articles
  • Sentiment analysis
  • Output: analyzed_articles[]
  ↓
[EXPORT_DATA]
  • Export CSV
  • Save to Vector DB
  • Output: CSV file
  ↓
END
```

---

## 📊 Output Files

### **1. CSV File**
Location: `data/csv/{project_name}_articles_{timestamp}.csv`

Columns:
- url
- title
- content
- source
- sentiment (positive/negative/neutral)
- published_date
- author
- summary

### **2. Vector DB**
Collection: `{project_name}` (sanitized)
- News articles embedded
- Opinion articles embedded
- Queryable for similarity search

### **3. Logs**
Location: `logs/autodata_{timestamp}.log`

---

## 🔍 Kiểm Tra Kết Quả

### **Trong Code:**
```python
result = await run_workflow_async(...)

# Check news articles
print(f"News articles: {len(result['news_articles'])}")

# Check keywords
keywords = result['extracted_keywords']
print(f"Keywords: {keywords.main_keywords[:10]}")

# Check opinions
print(f"Opinions analyzed: {len(result['analyzed_articles'])}")

# Check CSV
print(f"CSV saved to: {result['csv_output_path']}")
```

### **Trong Logs:**
```bash
tail -f logs/autodata_*.log
```

Tìm các dòng:
- `✅ Scraped X news articles`
- `✅ Extracted X keywords`
- `✅ Analyzed X articles with sentiment`
- `✅ Exported X articles to CSV`

---

## ⚙️ Configuration

Edit `core/config.py` nếu cần:

```python
# Search settings
MAX_NEWS_ARTICLES = 20  # Số tin tức tối đa để crawl
MAX_OPINION_ARTICLES = 35  # Số opinion articles tối đa

# Relevance scoring
KEYWORD_TITLE_SCORE = 3  # Điểm cho keyword match trong title
KEYWORD_SNIPPET_SCORE = 1  # Điểm cho keyword match trong snippet
OPINION_WORD_BONUS = 2  # Bonus cho opinion words

# Timeout
REQUEST_TIMEOUT = 30  # seconds
RETRY_DELAY = 2  # seconds
```

---

## ❌ Troubleshooting

### **Lỗi: "No news articles found"**
**Giải pháp:**
- Kiểm tra internet connection
- Thử project name khác (cụ thể hơn)
- Check logs xem trang nào bị fail

### **Lỗi: "No keywords extracted"**
**Giải pháp:**
- Kiểm tra news_articles có content không
- Tăng số lượng news articles
- Check PDF extractor tool

### **Lỗi: "Max loop reached"**
**Giải pháp:**
- Check state persistence
- Verify task completion logic
- Review manager routing

### **CSV không có data**
**Giải pháp:**
- Check analyzed_articles trong state
- Verify scrape_articles_done = True
- Review export agent logs

---

## 📈 Performance Tips

1. **Tăng tốc độ:**
   - Giảm `MAX_NEWS_ARTICLES` xuống 10-15
   - Giảm `max_results_per_site` trong search

2. **Tăng chất lượng:**
   - Tăng `MAX_NEWS_ARTICLES` lên 30-40
   - Sử dụng more specific project names
   - Add custom opinion keywords

3. **Debug:**
   - Set `LOG_LEVEL = DEBUG` in config
   - Check `processed_urls` to avoid duplicates
   - Monitor relevance scores

---

## 🎨 Customization

### **Thêm News Source:**
Edit `tools/direct_news_search.py`:
```python
'custom_site': {
    'name': 'Custom Site',
    'search_url': 'https://example.com/search?q={query}',
    'parser': self._parse_custom_site
}
```

### **Thay đổi Search Queries:**
Edit `agents/res.py` → `NewsSearchAgent`:
```python
news_queries = [
    f"{topic}",
    f"{topic} YOUR_CUSTOM_QUERY",
    # ...
]
```

### **Custom Sentiment Analysis:**
Edit `agents/res.py` → `ArticleAnalyzerAgent.analyze_sentiment()`:
```python
def analyze_sentiment(self, text: str) -> str:
    # Your custom logic here
    return "positive" | "negative" | "neutral"
```

---

## 📞 Support

Nếu gặp vấn đề:
1. Check logs in `logs/`
2. Review state in debugger
3. Test individual agents
4. Check network connectivity

---

**Good luck! 🚀**
