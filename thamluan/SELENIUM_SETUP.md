# 🔧 SELENIUM SETUP GUIDE

## 📦 Requirements

Law crawler hiện dùng **Selenium** để crawl dynamic content từ `duthaoonline.quochoi.vn`.

---

## ⚡ Quick Install

### **Bước 1: Install Selenium**
```bash
pip install selenium
```

### **Bước 2: Install ChromeDriver**

#### **Option A: Tự động (Khuyến nghị)**
```bash
pip install webdriver-manager
```

Sau đó update code:
```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
```

#### **Option B: Manual Download**
1. Check Chrome version: `chrome://version`
2. Download ChromeDriver: https://chromedriver.chromium.org/downloads
3. Put `chromedriver.exe` vào PATH hoặc cùng folder với code

---

## ✅ Verify Installation

```bash
# Test Selenium import
python -c "from selenium import webdriver; print('✅ Selenium OK!')"

# Test ChromeDriver
python test_law_crawler_selenium.py
```

---

## 🚀 Usage

### **Test Crawler:**
```bash
cd D:\AutoData...\thamluan
python test_law_crawler_selenium.py
```

### **Run Full Workflow:**
```bash
python test_hybrid_workflow.py
```

---

## 🎯 Features

### **Selenium Crawler:**
- ✅ **Headless mode** - Chạy ngầm, không mở browser
- ✅ **Dynamic content** - Xử lý JavaScript rendering
- ✅ **Wait for elements** - Tự động chờ content load
- ✅ **Similarity matching** - So sánh độ tương đồng với topic
- ✅ **Error handling** - Robust error catching

### **Configuration:**
```python
law_list_crawler.crawl_law_list(
    topic="Luật Khoa học",
    max_results=20,
    similarity_threshold=0.3  # 0.0 - 1.0
)
```

---

## 🐛 Troubleshooting

### **Error: "ChromeDriver not found"**
**Giải pháp:**
```bash
pip install webdriver-manager
```

### **Error: "WebDriverException"**
**Kiểm tra:**
- Chrome đã cài đặt chưa?
- ChromeDriver version khớp với Chrome version chưa?
- PATH đã có chromedriver chưa?

### **Error: "Timeout waiting for content"**
**Giải pháp:**
- Tăng timeout: `WebDriverWait(self.driver, 30)`
- Check internet connection
- Check website có accessible không

### **Crawler không tìm thấy documents:**
**Giải pháp:**
- Giảm `similarity_threshold` xuống (từ 0.7 → 0.3)
- Thử topic ngắn hơn: "Luật Khoa học" thay vì "Luật Khoa học..."
- Check logs để xem similarity scores

---

## 📊 Similarity Threshold Guide

| Threshold | Matching Behavior | Use Case |
|-----------|-------------------|----------|
| 0.9 - 1.0 | Very strict | Exact matches only |
| 0.7 - 0.9 | Strict | High confidence |
| 0.5 - 0.7 | Moderate | Balanced |
| 0.3 - 0.5 | **Loose (recommended)** | Better coverage |
| 0.0 - 0.3 | Very loose | May include noise |

**Default: 0.3** (good balance)

---

## 🎓 Selenium Basics

### **How it works:**
```python
# 1. Setup driver
driver = webdriver.Chrome(options=chrome_options)

# 2. Navigate
driver.get("https://example.com")

# 3. Wait for content
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "article"))
)

# 4. Find elements
articles = driver.find_elements(By.CLASS_NAME, "col-10")

# 5. Extract data
for article in articles:
    title = article.find_element(By.TAG_NAME, "h2").text
    url = article.find_element(By.TAG_NAME, "a").get_attribute("href")

# 6. Cleanup
driver.quit()
```

---

## 🔧 Advanced Options

### **Headless with options:**
```python
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")
```

### **With proxy:**
```python
chrome_options.add_argument('--proxy-server=http://proxy:port')
```

### **Custom user agent:**
```python
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0"
)
```

---

## 📚 Resources

- **Selenium Docs:** https://selenium-python.readthedocs.io/
- **ChromeDriver:** https://chromedriver.chromium.org/
- **WebDriver Manager:** https://github.com/SergeyPirogov/webdriver_manager

---

## ✅ Checklist

Trước khi chạy:
- [ ] Đã install `selenium`
- [ ] Đã install ChromeDriver (manual hoặc webdriver-manager)
- [ ] Chrome browser đã cài đặt
- [ ] Internet connection OK
- [ ] Test script chạy thành công

---

**Status:** ✅ READY
**Last Updated:** 2025-10-14
