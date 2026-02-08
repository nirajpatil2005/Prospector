# Intelligent Company Researcher

A powerful two-stage company research platform that combines deep web scraping (LinkedIn + Company Websites) with LLM-based analysis (Gemini/Groq) to provide comprehensive market intelligence.

## Features

- **Strict Domain Filtering**: AI-driven discovery ensures only official company homepages are analyzed.
- **Deep LinkedIn Integration**: Uses Apify to scrape detailed company profiles (Firmographics, Specialties, Follower Counts).
- **Internal Scraping Engine**: Custom `crawl_best` microservice for deep website content extraction.
- **LLM Analysis**: Synthesizes data from multiple sources to generate strategic insights, financial estimates, and relevance scoring.
- **Real-time Streaming**: Frontend receives live updates via Server-Sent Events (SSE).
- **Tabular Data View**: Detailed comparison tables for financial and operational metrics.

## Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher (for Frontend)
- **API Keys**:
    - `GEMINI_API_KEY`: Google Gemini API (for analysis)
    - `APIFY_API_TOKEN`: Apify Console (for LinkedIn scraping)
    - `GROQ_API_KEY` (Optional): Fallback LLM

## Project Structure

- `app/`: FastAPI Backend (Main Logic)
- `frontend/`: Next.js/React Frontend
- `crawl_best/`: Internal Scraping Microservice (Crawler + Insighter)
- `run_internal_scraper.py`: Fallback adapter for the internal scraper.

## Installation & Setup

### 1. Backend Setup

1.  **Clone/Navigate** to the project root.
2.  **Create Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```
4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```ini
    GEMINI_API_KEY=your_gemini_key
    APIFY_API_TOKEN=your_apify_token
    GROQ_API_KEY=your_groq_key_optional
    ```

### 2. Internal Scraper Setup (Optional but Recommended)

The internal scraper (`crawl_best`) can run as a separate microservice.
*Note: The main backend has a fallback to run this automatically if the service is not active.*

To run it manually:
```bash
cd crawl_best/crawling_scrap
python main.py
```
*This will start services on ports 8000 (Insighter) and 8001 (Crawler).*

### 3. Frontend Setup

1.  **Navigate to frontend**:
    ```bash
    cd frontend
    ```
2.  **Install Dependencies**:
    ```bash
    npm install
    # or
    yarn install
    ```

## Running the Application

### Start the Backend
The main application runs on port **8002** to avoid conflicts.

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002
```

### Start the Frontend

```bash
cd frontend
npm run dev
```

Access the application at: `http://localhost:3000`

## Internal Architecture

1.  **Discovery**: User query -> LLM identifies target companies and URLs.
2.  **Data Collection (Parallel)**:
    - **LinkedIn**: Apify Actor (`dev_fusion/linkedin-company-scraper`) fetches profile data.
    - **Website**: `crawl_best` (or fallback script) crawls the official homepage.
3.  **Synthesis**: Data from both sources is normalized and sent to the LLM (Gemini 2.0 Flash) for analysis.
4.  **Presentation**: Results are streamed to the React frontend.
