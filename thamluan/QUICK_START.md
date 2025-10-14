# 🚀 Quick Start - Article-Based Workflow

## ✅ Đã Fix Tất Cả Issues

### Vấn đề đã sửa:
1. ✅ Bỏ yêu cầu nhập URL - chỉ cần topic name
2. ✅ Fix lỗi `extract_keywords_from_text` - dùng đúng method
3. ✅ Fix infinite loop khi có error
4. ✅ Fix test script crash khi keywords = None

---

## 🎯 Cách Chạy (CỰC KỲ ĐƠN GIẢN)

```bash
cd D:\NhanTran\AutoData - Copy\thamluan
python test_new_workflow.py
```

**HOẶC:**

```bash
python main.py
# Nhập topic khi được hỏi: Dự thảo Luật trí tuệ nhân tạo 2025
```

**HOẶC:**

```bash
python main.py --project "Luật Đất đai 2025"
```

---

## 📝 Ví Dụ Topics

- ✅ `Dự thảo Luật trí tuệ nhân tạo 2025`
- ✅ `Luật Khoa học, công nghệ và đổi mới sáng tạo 2025`  
- ✅ `Luật Đất đai 2025`
- ✅ `Nghị định 68/2025`
- ✅ `Luật Giao thông đường bộ mới`

---

## 🔄 Workflow Flow

```
INPUT: Topic name only
   ↓
SEARCH_NEWS (tìm tin tức)
   ↓
SCRAPE_NEWS (crawl 5-20 articles)
   ↓
EXTRACT_KEYWORDS (từ news content)
   ↓
SEARCH_OPINIONS (dùng keywords)
   ↓
SCRAPE_ARTICLES (crawl opinions)
   ↓
ANALYZE_SENTIMENT
   ↓
EXPORT_CSV
   ↓
OUTPUT: CSV file + Vector DB
```

---

## 📊 Expected Output

```
📊 SUMMARY:
  - News Articles Found: 5-20
  - Keywords Extracted: 20-50
  - Opinion Articles Analyzed: 10-30
  - CSV Output: data/csv/{topic}_articles_{timestamp}.csv
  - Errors: 0-2 (acceptable)
```

---

## ⚠️ Known Issues & Solutions

### Issue: "No news articles found"
**Cause**: Topic name quá cụ thể hoặc không có tin tức
**Solution**: Thử topic name ngắn gọn hơn, ví dụ:
- ❌ "Dự thảo Luật trí tuệ nhân tạo 2025 mới nhất chi tiết"
- ✅ "Luật trí tuệ nhân tạo 2025"

### Issue: Scraped wrong URLs (mail.mst.gov.vn, etc.)
**Cause**: Parser lấy nhầm internal links
**Solution**: ✅ Đã fix với URL validation trong SearchAgent

### Issue: Keywords = 0
**Cause**: News content quá ít hoặc không có text
**Solution**: ✅ Workflow sẽ continue với default keywords

---

## 🐛 Debug

Check logs:
```bash
tail -f logs/autodata_*.log
```

Look for:
- `✅ Scraped X news articles`
- `✅ Extracted X keywords`
- `✅ Analyzed X articles with sentiment`

---

## 💪 Production Ready!

Workflow đã được test và fix tất cả critical bugs. 

**Ready to run!** 🚀
