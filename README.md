# Steel Browser API

Advanced web scraping API powered by Steel Browser on Railway. Performs Google searches with customizable filters and deep scrapes each result to extract full content.

## Features

- 🔍 **Advanced Google Search** with language, region, time, and type filters
- 🌐 **Multi-language support** (Italian, English, Spanish, French, German, Dutch, etc.)
- 📰 **News & Web Search** with time filters (hour, day, 3 days, week, month, year)
- 📊 **Deep Content Extraction** - titles, headings, paragraphs, full text, metadata
- 🚀 **Fast & Scalable** - Built with FastAPI and async/await
- 📖 **Auto-generated API docs** at `/docs`

## API Endpoints

### `GET /`
Root endpoint with API information

### `GET /health`
Health check endpoint

### `POST /search`
Main search and scrape endpoint

**Request Body:**
```json
{
  "query": "Juventus vs Inter formazioni probabili",
  "language": "it",
  "region": "it",
  "search_type": "news",
  "time_filter": "3days",
  "num_results": 5
}
```

**Parameters:**
- `query` (required): Search query string
- `language` (default: "it"): Language code (it, en, es, fr, de, nl, etc.)
- `region` (default: "it"): Region code (it, us, uk, de, fr, etc.)
- `search_type` (default: "web"): Either "web" or "news"
- `time_filter` (optional): hour, day, 3days, week, month, year
- `num_results` (default: 5): Number of results to scrape (1-20)

**Response:**
```json
{
  "query": "Juventus vs Inter formazioni probabili",
  "language": "it",
  "region": "it",
  "search_type": "news",
  "time_filter": "3days",
  "scraped_at": "2025-10-29T12:00:00",
  "total_results": 5,
  "results": [
    {
      "position": 1,
      "search_title": "...",
      "url": "https://...",
      "page_title": "...",
      "headings": ["...", "..."],
      "paragraphs": ["...", "..."],
      "main_text": "...",
      "metadata": {},
      "error": null,
      "scraped_at": "2025-10-29T12:00:00"
    }
  ]
}
```

## Local Development

### Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### Run Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access API
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deploy to Railway

1. Push code to GitHub repository
2. Create new project on Railway
3. Connect GitHub repository
4. Railway will auto-detect Dockerfile and deploy
5. Set environment variable: `STEEL_URL=https://your-steel-instance.railway.app`

## Usage Examples

### cURL
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bitcoin price 2025",
    "language": "en",
    "region": "us",
    "search_type": "news",
    "time_filter": "day",
    "num_results": 10
  }'
```

### Python
```python
import requests

response = requests.post('http://localhost:8000/search', json={
    'query': 'Juventus vs Inter formazioni',
    'language': 'it',
    'region': 'it',
    'search_type': 'news',
    'time_filter': '3days',
    'num_results': 5
})

data = response.json()
print(f"Found {data['total_results']} results")
```

### n8n HTTP Request Node
```json
{
  "method": "POST",
  "url": "https://your-api.railway.app/search",
  "body": {
    "query": "{{ $json.searchQuery }}",
    "language": "it",
    "region": "it",
    "search_type": "news",
    "time_filter": "3days",
    "num_results": 5
  }
}
```

## Architecture

- **FastAPI**: Modern async web framework
- **Playwright**: Browser automation
- **Steel Browser**: Managed browser instances on Railway
- **Pydantic**: Data validation and serialization

## Environment Variables

- `STEEL_URL`: Steel Browser instance URL (default: https://steel-browser-production-9a2a.up.railway.app)
- `PORT`: Server port (default: 8000)

## License

MIT

