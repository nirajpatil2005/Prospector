# 🕷️ Scrapy Web Crawler – Command & Setup Guide

This repository contains a **production-ready Scrapy crawler setup**.  
This README focuses **only on commands, file changes, and workflow**, so anyone can quickly understand and work on it.

---

## 📌 What is Scrapy?

**Scrapy** is a Python framework for:
- Crawling websites
- Extracting structured data
- Managing requests asynchronously
- Exporting data to JSON / CSV / databases

Scrapy is preferred for production crawlers because it provides:
- Request scheduling
- Auto-throttling & retries
- Pipelines for cleaning & storage
- Built-in CLI tools

---

## 🧠 How Scrapy Works (High Level)

```
Start URL
   ↓
Spider sends request
   ↓
Downloader fetches page
   ↓
Spider parses response
   ↓
Items extracted
   ↓
Pipelines clean/store data
```

---

## 🛠️ Environment Setup

### 1️⃣ Create Virtual Environment
```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**Linux / macOS**
```bash
source venv/bin/activate
```

---

### 2️⃣ Install Scrapy
```bash
pip install scrapy
```

Verify installation:
```bash
scrapy version
```

---

## 📁 Create Scrapy Project

### 3️⃣ Start Project
```bash
scrapy startproject web_crawler
cd web_crawler
```

Project structure:
```
web_crawler/
├── scrapy.cfg
└── web_crawler/
    ├── items.py
    ├── pipelines.py
    ├── settings.py
    └── spiders/
```

---

## 🕷️ Create a Spider

### 4️⃣ Generate Spider
```bash
scrapy genspider example example.com
```

---

## 🔧 Required File Changes (Production-Ready)

### 5️⃣ settings.py
```python
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS = 8
LOG_LEVEL = "INFO"
```

---

### 6️⃣ items.py
```python
import scrapy

class PageItem(scrapy.Item):
    page_type = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    meta_description = scrapy.Field()
    h1 = scrapy.Field()
    h2 = scrapy.Field()
    paragraphs = scrapy.Field()
```

---

### 7️⃣ pipelines.py
```python
class CleanPipeline:
    def process_item(self, item, spider):
        for key in ["h2", "paragraphs"]:
            if key in item and item[key]:
                item[key] = [x.strip() for x in item[key] if x.strip()]
        return item
```

Enable pipeline in settings.py:
```python
ITEM_PIPELINES = {
    "web_crawler.pipelines.CleanPipeline": 300,
}
```

---

## ▶️ Running the Crawler

```bash
scrapy crawl example
scrapy crawl example -O output.json
scrapy crawl example -O output.csv
scrapy crawl example -L INFO
```

---

## 🏭 Production Best Practices

✔ Respect robots.txt  
✔ Use reasonable delays  
✔ Filter invalid links  
✔ Clean data using pipelines  
✔ Export structured output  

---

## 📦 Useful Commands Summary

```bash
scrapy startproject project_name
scrapy genspider spider_name domain.com
scrapy crawl spider_name
scrapy crawl spider_name -O data.json
scrapy crawl spider_name -L INFO
```

---

### ✔ End of README
