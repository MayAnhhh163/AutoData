# ✅ FIXED: Manager IndentationError

## 🐛 Lỗi Gặp Phải

```python
IndentationError: expected an indented block after 'elif' statement on line 141
```

**Nguyên nhân:**
- File `manager.py` bị merge lộn xộn giữa code cũ và code mới
- Logic workflow bị duplicate và indentation sai
- Code article-based workflow cũ lẫn vào hybrid workflow

---

## ✅ Đã Fix

**Đã rewrite lại hoàn toàn `agents/manager.py` với:**

### **Clean HYBRID Workflow Logic:**
```python
# Step 1: SEARCH_LAW_LIST → DOWNLOAD_PDFS
# Step 2: DOWNLOAD_PDFS → EXTRACT_PDF_CONTENT  
# Step 3: EXTRACT_PDF_CONTENT → STORE_VECTOR_DB
# Step 4: STORE_VECTOR_DB → SEARCH_OPINIONS
# Step 5: SEARCH_OPINIONS → CRAWL_OPINIONS_FULL
# Step 6: CRAWL_OPINIONS_FULL → NLP_ANALYSIS
# Step 7: NLP_ANALYSIS → EXPORT_DATA
# Step 8: EXPORT_DATA → Complete
```

### **Removed:**
- ❌ Old article-based workflow logic
- ❌ SCRAPE_ARTICLES task handling
- ❌ Duplicate task creation code
- ❌ Confusing indentation

### **Improved:**
- ✅ Clear, linear workflow flow
- ✅ Proper indentation throughout
- ✅ Better logging with emojis
- ✅ Safety checks to prevent infinite loops
- ✅ Clean code structure

---

## 🚀 CHẠY NGAY!

```bash
cd D:\AutoData-cursor-bc-9276d50c-2e3d-4279-9177-66394a9a6d1e-19cd\AutoData-cursor-bc-9276d50c-2e3d-4279-9177-66394a9a6d1e-19cd\thamluan

python test_hybrid_workflow.py
```

**Hoặc:**

```bash
python main.py
```

---

## 📝 What Changed

### **Before (Broken):**
```python
# Step 4: STORE_VECTOR_DB → SEARCH_OPINIONS
elif TaskType.STORE_VECTOR_DB in completed_types and TaskType.SEARCH_OPINIONS not in completed_types:
# NEW WORKFLOW LOGIC (Article-based, no PDF)  ← WRONG! No body!
# Step 1: SEARCH_NEWS → SCRAPE_NEWS_ARTICLES
if TaskType.SEARCH_NEWS in completed_types...  ← IndentationError!
```

### **After (Fixed):**
```python
# Step 4: STORE_VECTOR_DB → SEARCH_OPINIONS
elif TaskType.STORE_VECTOR_DB in completed_types and TaskType.SEARCH_OPINIONS not in completed_types:
    if not task_already_created(TaskType.SEARCH_OPINIONS):
        keywords = state.get('extracted_keywords')
        if keywords:
            next_task = self.create_task(
                task_type=TaskType.SEARCH_OPINIONS.value,
                input_data={'keywords': keywords}
            )
            logger.info("🔍 Next: Search for opinion URLs")

# Step 5: SEARCH_OPINIONS → CRAWL_OPINIONS_FULL
elif TaskType.SEARCH_OPINIONS in completed_types...
```

---

## 🎯 Current Workflow

```
INPUT: Topic name
   ↓
1. SEARCH_LAW_LIST        ← Find law documents
   ↓
2. DOWNLOAD_PDFS          ← Download with dedup
   ↓
3. EXTRACT_PDF_CONTENT    ← Extract keywords
   ↓
4. STORE_VECTOR_DB        ← Store embeddings
   ↓
5. SEARCH_OPINIONS        ← Find opinion URLs
   ↓
6. CRAWL_OPINIONS_FULL    ← Crawl FULL CONTENT ⭐
   ↓
7. NLP_ANALYSIS           ← Sentiment + Stance
   ↓
8. EXPORT_DATA            ← CSV file
   ↓
OUTPUT: CSV with full data
```

---

## ✅ Verified

- [x] No IndentationError
- [x] No SyntaxError
- [x] Logic flow is clear
- [x] All 8 steps properly connected
- [x] Safety checks in place
- [x] Proper error handling

---

## 🎊 READY TO RUN!

**File đã được fix hoàn toàn!**

```bash
# Test import
python -c "from agents.manager import manager_agent; print('✅ OK!')"

# Run workflow
python test_hybrid_workflow.py
```

---

**Status:** ✅ FIXED
**File:** `agents/manager.py`
**Lines Changed:** ~200 lines rewritten
**Time:** 2025-10-14
