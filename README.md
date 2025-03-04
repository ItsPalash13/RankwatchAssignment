# Web Scraper Service

## Overview
This Web Scraper Service processes URLs by extracting text content, outbound links, and grammar errors. It uses RabbitMQ for job queuing and MongoDB for storage.

## Features
- Fetch webpage content using `requests` (fallback to Selenium for dynamic pages).
- Extract text using `newspaper3k`.
- Extract outbound links using `lxml`.
- Check grammar using `language_tool_python`.
- Uses RabbitMQ for job distribution.
- Stores results in MongoDB with status tracking.

## Tech Stack
- **Python**
- **MongoDB** (Data Storage)
- **RabbitMQ** (Task Queue)
- **Requests, Selenium** (Web Scraping)
- **Newspaper3k, lxml** (Text & Links Extraction)
- **LanguageTool** (Grammar Checking)

## Flow Diagram
![NoteGPT-Flowchart-1741069828919](https://github.com/user-attachments/assets/353d2d26-557b-48ac-9787-70988079b0cb)

## Setup & Installation
### 1. Clone the Repository
```sh
$ git clone https://github.com/ItsPalash13/RankwatchAssignment.git
$ cd RankwatchAssignment
```

### 2. Install Dependencies
```sh
$ pip install -r requirements.txt
```

### 3. Configure MongoDB & RabbitMQ
Set up MongoDB and RabbitMQ credentials in the script.

### 4. Start the Service
```sh
$ python scraper.py start_service
```

### 5. Add a URL to Process
```sh
$ python scraper.py add_url --url "https://example.com"
```

## Workflow
1. **Add URL** → Stores in MongoDB and pushes to RabbitMQ.
2. **Queue Consumption** → Service listens for URLs and processes them.
3. **Scraping & Processing**
   - Fetch content (Requests/Selenium fallback).
   - Extract text (Newspaper3k).
   - Extract outbound links (lxml).
   - Check grammar (LanguageTool).
4. **Save Results** → Update MongoDB with processed data or failure reason.

## Error Handling
- If fetching or extraction fails, status is updated to `failed` with reason in MongoDB.
- RabbitMQ ensures at-least-once delivery to prevent lost jobs.

## Example Output
```json
{
  "url": "https://example.com",
  "status": "processed",
  "content": "Extracted text...",
  "links": ["https://another.com", "https://site.com"],
  "grammar_errors": [{"offset": 10, "error": "Possible typo"}],
  "processing_time": 2.45
}
```

## License
This project is open-source and available under the MIT License.

---
Made with ❤️ by [Palash Krishna Vishwas](https://github.com/ItsPalash13)
