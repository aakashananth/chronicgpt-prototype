# Health Metrics LLM Prototype

A Python project that uses Ultrahuman ring-like health data to detect anomalies and generate LLM-powered explanations for health metric patterns.

## Phase 1 Overview

This is **Phase 1** of the Health Metrics LLM Prototype project. The current implementation focuses on:

- Fetching health metrics data from the UltraHuman API
- Detecting anomalies using rolling baseline comparisons
- Generating natural language explanations using Azure OpenAI
- Storing enriched data locally in Parquet format

## Architecture (Phase 1)

The current architecture follows this data flow:

```
UltraHuman API → pandas DataFrame → Anomaly Detection → Azure OpenAI → Parquet Output
```

**Components:**
- **UltraHuman Client** (`src/ultrahuman_client.py`): Fetches health metrics from the UltraHuman Partner API
- **Anomaly Detection** (`src/anomaly_detection.py`): Detects anomalies using 7-day rolling medians and threshold-based flags
- **LLM Explainer** (`src/llm_explainer.py`): Generates explanations using Azure OpenAI
- **Pipeline** (`src/pipeline.py`): Orchestrates the entire flow
- **CLI Entrypoint** (`src/run_pipeline.py`): Command-line interface for running the pipeline

## Requirements

- Python 3.10+

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Set the following environment variables:

```env
# UltraHuman API Configuration
ULTRAHUMAN_API_BASE_URL=https://partner.ultrahuman.com
ULTRAHUMAN_API_KEY=your_api_key_here
ULTRAHUMAN_EMAIL=your_email@example.com

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Local Storage Configuration
LOCAL_DATA_DIR=data
```

### 4. Run the Pipeline

```bash
python -m src.run_pipeline
```

This will:
- Fetch the last 14 days of health metrics
- Detect anomalies
- Generate an LLM explanation for recent anomalies
- Save enriched data to `data/daily_metrics_enriched.parquet`
- Print results to the console

## Project Structure

```
health-metrics-llm-prototype/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── ultrahuman_client.py   # UltraHuman API client
│   ├── anomaly_detection.py   # Anomaly detection logic
│   ├── llm_explainer.py       # Azure OpenAI integration
│   ├── pipeline.py            # Main pipeline orchestration
│   ├── run_pipeline.py        # CLI entrypoint
│   ├── api.py                 # FastAPI application
│   ├── redis_cache.py         # Redis caching client
│   ├── memory_cache.py        # In-memory cache fallback
│   ├── parquet_loader.py      # Parquet file loader
│   └── azure_storage_client.py # Azure Blob Storage client
├── frontend/                  # Next.js 14 frontend application
│   ├── app/                  # App Router pages
│   ├── lib/                  # API client and utilities
│   └── package.json
├── data/
│   ├── .gitkeep
│   └── sample_ultrahuman_export.json  # Sample data for testing
├── notebooks/
│   └── 01_explore_ultrahuman_data.ipynb
├── .env.example               # Environment variable template
├── .gitignore
├── requirements.txt
├── run_api.py                # FastAPI server entrypoint
└── README.md
```

## API Endpoints

The FastAPI application provides several endpoints for running the pipeline and retrieving cached results:

- `POST /pipeline/run`: Run the full daily pipeline (fetches all dates in range)
- `POST /pipeline/run_incremental`: Run the incremental pipeline (only processes new dates)
- `GET /pipeline/metrics`: Get cached metrics
- `GET /pipeline/anomalies`: Get cached anomalies
- `GET /pipeline/explanation`: Get cached LLM explanation
- `GET /pipeline/blob-path`: Get cached blob path

### Incremental Pipeline Endpoint

The `/pipeline/run_incremental` endpoint is designed for scheduled execution (e.g., every 5-10 minutes) to automatically ingest new health metrics data as it becomes available.

#### What it does

- **Idempotent operation**: The endpoint checks which dates already exist in Azure Blob Storage under `curated/daily_metrics/patient_id={patient_id}/` and only fetches and processes missing dates within the specified `days_back` window.
- **Efficient processing**: Only new dates are fetched from the Ultrahuman API, transformed, analyzed for anomalies, and uploaded to storage.
- **Automatic caching**: Results are automatically cached in Redis (if configured) and in-memory cache, making them immediately available via the GET endpoints.

#### Recommended Schedule

- **Every 5-10 minutes**: Since the Ultrahuman API provides daily aggregated metrics, the main benefit of frequent runs is to ensure "today's" daily metrics are picked up as soon as they become available.
- The endpoint is safe to run frequently because it skips dates that have already been processed.

#### Example Usage

**Using curl:**

```bash
curl -X POST "https://<your-api>.azurewebsites.net/pipeline/run_incremental?days_back=14"
```

**Using GitHub Actions (example workflow):**

```yaml
name: Incremental Pipeline

on:
  schedule:
    # Run every 10 minutes
    - cron: '*/10 * * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  run-incremental:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Incremental Pipeline
        run: |
          curl -X POST "${{ secrets.API_BASE_URL }}/pipeline/run_incremental?days_back=14"
```

**Using Azure Logic Apps or Vercel Cron:**

Configure your scheduler to make a POST request to `/pipeline/run_incremental?days_back=14` at your desired interval.

## Frontend Application

A modern Next.js 14 frontend application is available in the `frontend/` directory.

### Running the Frontend

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Configure environment variables:

```bash
cp .env.local.example .env.local
```

Update `.env.local` with your API base URL (defaults to Azure App Service URL).

4. Run the development server:

```bash
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

See `frontend/README.md` for more details.

## Future Phases

Future phases of this project will add:

- **Azure Data Lake**: For scalable data storage
- **Azure Data Explorer**: For advanced analytics and querying
- **Azure Cache for Redis**: For caching and performance optimization (✅ Implemented)
- **FastAPI Backend**: RESTful API for serving health insights (✅ Implemented)
- **React Web App**: User interface for viewing health metrics and explanations (✅ Implemented)

## Important Disclaimer

⚠️ **This is NOT a medical device and does NOT provide medical advice.**

This project is for informational and educational purposes only. The health metrics analysis and explanations generated by this system are not intended to:

- Diagnose, treat, cure, or prevent any disease or medical condition
- Replace professional medical advice, diagnosis, or treatment
- Be used as a substitute for consultation with qualified healthcare professionals

**Always consult with a qualified healthcare professional** for any health concerns or before making decisions about your health based on information from this system.

## License

TBD
