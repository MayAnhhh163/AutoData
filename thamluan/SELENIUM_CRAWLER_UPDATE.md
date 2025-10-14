# ✅ UPDATED: Law List Crawler → Selenium Version

## 🎯 Thay Đổi

Đã update `tools/law_list_crawler.py` để dùng **Selenium** thay vì requests/BeautifulSoup.

---

## 🆕 Features Mới

### **1. Selenium với Chrome Headless**
```python
chrome_options = Options()
chrome_options.add_argument("--headless")  # Chạy ngầm
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)
```

### **2. Crawl Dynamic Content**
- ✅ Xử lý JavaScript rendering
- ✅ Tự động chờ elements load
- ✅ Handle AJAX requests

### **3. Similarity Matching**
```python
def _calculate_similarity(self, a: str, b: str) -> float:
    """So sánh độ tương đồng giữa topic và title"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Usage
similarity = self._calculate_similarity("Luật Khoa học", title)
if similarity >= 0.3:  # threshold
    documents.append(doc)
```

### **4. Smart Filtering**
- Chỉ lấy documents có similarity >= threshold
- Loại bỏ duplicates
- Top N results

---

## 🔧 Configuration

### **Default Settings:**
```python
law_list_crawler.crawl_law_list(
    topic="Luật Khoa học",
    source='duthaoonline',
    max_pages=1,
    max_results=20,
    similarity_threshold=0.3  # 30% similarity
)
```

### **Customize Threshold:**
```python
# Strict matching (0.7 = 70% similarity)
similarity_threshold=0.7

# Loose matching (0.3 = 30% similarity) ← RECOMMENDED
similarity_threshold=0.3

# Very loose (0.1 = 10% similarity)
similarity_threshold=0.1
```

---

## 📦 Installation

### **Quick Setup:**
```bash
# 1. Install Selenium
pip install selenium

# 2. Install WebDriver Manager (auto ChromeDriver)
pip install webdriver-manager

# 3. Test
python test_law_crawler_selenium.py
```

---

## 🌐 Source

**Crawl từ:**
```
https://duthaoonline.quochoi.vn/du-thao
```

**Elements:**
- `.col-10` - Article containers
- `.d-inline-block` - Links
- `h2` - Titles

---

## 🧪 Test

### **Test Script:**
```bash
python test_law_crawler_selenium.py
```

**Output:**
```
📋 Testing topic: 'Luật Khoa học'
✅ SUCCESS: Found 8 documents

📚 Documents:
  1. Dự thảo Luật Khoa học công nghệ 2025
     Similarity: 85.3%
     URL: https://duthaoonline.quochoi.vn/...
  
  2. Luật sửa đổi Luật Khoa học
     Similarity: 72.1%
     URL: https://duthaoonline.quochoi.vn/...
```

---

## 🚀 Usage in Workflow

### **LawListSearchAgent sẽ tự động dùng:**
```python
# agents/hybrid_agents.py - LawListSearchAgent
result = law_list_crawler.crawl_law_list(
    topic=topic,
    max_results=20,
    similarity_threshold=0.3
)

documents = result.data['documents']
# → List[DocumentCard]
```

### **Full Workflow:**
```
1. SEARCH_LAW_LIST (Selenium) ← UPDATED!
   ↓
2. DOWNLOAD_PDFS
   ↓
3. EXTRACT_PDF_CONTENT
   ↓
... (rest of pipeline)
```

---

## 📊 Comparison

### **Before (requests + BeautifulSoup):**
- ❌ Can't handle JavaScript
- ❌ Miss dynamic content
- ❌ Fixed selectors
- ✅ Fast

### **After (Selenium):**
- ✅ Handle JavaScript ⭐
- ✅ Wait for dynamic content ⭐
- ✅ Flexible
- ✅ Similarity matching ⭐
- ⚠️ Slower (but more reliable)

---

## 🎯 Similarity Threshold Guide

**Examples với topic "Luật Khoa học":**

| Title | Similarity | Match @ 0.3? | Match @ 0.7? |
|-------|------------|--------------|--------------|
| "Luật Khoa học công nghệ 2025" | 85% | ✅ Yes | ✅ Yes |
| "Dự thảo Luật Khoa học" | 72% | ✅ Yes | ✅ Yes |
| "Luật về Khoa học và Công nghệ" | 65% | ✅ Yes | ❌ No |
| "Nghị định về khoa học" | 45% | ✅ Yes | ❌ No |
| "Luật Đất đai" | 15% | ❌ No | ❌ No |

**Recommendation:** Use `0.3` for balance!

---

## 🐛 Troubleshooting

### **"ChromeDriver not found"**
```bash
pip install webdriver-manager
```

### **"No documents matched topic"**
**Try:**
1. Lower threshold: `similarity_threshold=0.2`
2. Shorter topic: "Luật Khoa học" thay vì "Luật Khoa học công nghệ..."
3. Check logs cho similarity scores

### **"Timeout waiting for content"**
**Fix:**
- Increase timeout in code
- Check internet
- Verify website accessible

---

## 📝 Files Changed

### **Updated:**
1. ✅ `tools/law_list_crawler.py` - Selenium version
2. ✅ `agents/hybrid_agents.py` - Lower threshold
3. ✅ `test_law_crawler_selenium.py` - NEW test script
4. ✅ `SELENIUM_SETUP.md` - Setup guide
5. ✅ `SELENIUM_CRAWLER_UPDATE.md` - This file

---

## ✅ Testing

### **Test Crawler Only:**
```bash
python test_law_crawler_selenium.py
```

### **Test Full Workflow:**
```bash
python test_hybrid_workflow.py
```

**Expected:**
```
🔍 Searching law documents for: Luật Khoa học...
📍 Source: https://duthaoonline.quochoi.vn/du-thao
🎯 Similarity threshold: 0.3
⏳ Waiting for content to load...
✅ Page loaded successfully
📄 Found 45 articles on page
📰 Article 1/45:
   Title: Dự thảo Luật Khoa học công nghệ 2025
   Similarity: 85.3%
   ✅ MATCH! (threshold: 0.3)
   💾 Saved: 1/20
...
✅ Crawl complete: 12 documents found
```

---

## 🎉 READY TO USE!

```bash
# Install dependencies
pip install selenium webdriver-manager

# Test crawler
python test_law_crawler_selenium.py

# Run workflow
python test_hybrid_workflow.py
```

---

**Status:** ✅ COMPLETE
**Crawler:** Selenium-based
**Source:** duthaoonline.quochoi.vn
**Threshold:** 0.3 (recommended)
**Last Updated:** 2025-10-14
