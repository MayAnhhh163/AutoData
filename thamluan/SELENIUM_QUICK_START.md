# 🚀 SELENIUM CRAWLER - QUICK START

## ⚡ 3 BƯỚC SETUP (30 GIÂY)

### **Bước 1: Install Dependencies**
```bash
# Windows
install_selenium.bat

# Linux/Mac
pip install selenium webdriver-manager
```

### **Bước 2: Test Crawler**
```bash
python test_law_crawler_selenium.py
```

**Expected output:**
```
📋 Testing topic: 'Luật Khoa học'
✅ SUCCESS: Found 8 documents

📚 Documents:
  1. Dự thảo Luật Khoa học công nghệ 2025
     Similarity: 85.3%
```

### **Bước 3: Run Full Workflow**
```bash
python test_hybrid_workflow.py
```

---

## ✅ DONE!

Law crawler giờ dùng **Selenium** để crawl từ `duthaoonline.quochoi.vn`:
- ✅ Handle JavaScript
- ✅ Dynamic content
- ✅ Similarity matching (threshold 0.3)
- ✅ Headless mode

---

## 🎯 Key Changes

### **Source Changed:**
```
Before: mst.gov.vn
After:  duthaoonline.quochoi.vn ← Better structure!
```

### **Technology:**
```
Before: requests + BeautifulSoup
After:  Selenium + Chrome headless ← Can handle JS!
```

### **Matching:**
```
New: Similarity threshold (0.3 recommended)
→ Better filtering based on topic relevance
```

---

## 📝 If You Get Errors

### **"ChromeDriver not found"**
```bash
pip install webdriver-manager
```
→ Auto downloads correct ChromeDriver

### **"No documents matched"**
→ Lower threshold or use shorter keywords:
```python
# In agents/hybrid_agents.py, line 47
similarity_threshold=0.2  # Lower = more results
```

### **"Timeout"**
→ Check internet, wait longer, or verify site accessible

---

## 📚 Documentation

- `SELENIUM_SETUP.md` - Detailed setup guide
- `SELENIUM_CRAWLER_UPDATE.md` - What changed
- `test_law_crawler_selenium.py` - Test script

---

## 🎊 READY!

```bash
python test_hybrid_workflow.py
```

Workflow sẽ tự động:
1. ✅ Crawl law list (Selenium) ← NEW!
2. ✅ Download PDFs
3. ✅ Extract keywords
4. ✅ Search opinions
5. ✅ Crawl full content
6. ✅ NLP analysis
7. ✅ Export CSV

---

**Time to test:** ~3-4 minutes
**Output:** CSV with full content + NLP labels

**GO!** 🚀
