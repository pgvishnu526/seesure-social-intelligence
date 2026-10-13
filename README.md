# SocialPulse: AI-Powered Social Media Intelligence Platform

## Project Overview

SocialPulse is an AI-powered platform that analyzes social media content screenshots to provide intelligent verification and risk assessment reports. Users upload images of social media posts, and the system provides comprehensive analysis including claim extraction, sentiment analysis, media authenticity checks, web research, and explainable risk scoring.

## Architecture

```
Frontend (HTML/CSS/JS) ↔ FastAPI Backend ↔ LangGraph Workflow
                                 ↓
                    [Content Analysis → Claim Extraction → Research → Risk Assessment]
                                 ↓
                        [AWS S3 / Local Storage]
```

## Features

- **Image Upload & Processing**: Drag-and-drop interface with image validation
- **OCR & Content Understanding**: Extract text and understand content structure
- **Claim Extraction**: Identify verifiable claims and entities
- **Sentiment Analysis**: Analyze emotional tone of content
- **Media Authenticity Analysis**: Detect potential manipulation indicators
- **Web Research**: Gather supporting/contradicting evidence from reliable sources
- **Risk Assessment**: Generate explainable risk scores (0-100)
- **Professional Reports**: Human-readable intelligence reports
- **Real-time Status**: Live progress tracking during analysis

## Tech Stack

### Frontend
- HTML5
- CSS3 
- Vanilla JavaScript
- No frameworks required

### Backend
- Python 3.8+
- FastAPI
- Uvicorn
- LangGraph for workflow orchestration

### AI & Services
- Google Gemini API (vision, text analysis)
- Web search for research
- AWS S3 (optional, with local fallback)

### Dependencies
- fastapi
- uvicorn
- python-multipart
- pydantic
- python-dotenv
- boto3
- google-generativeai
- langgraph
- langchain
- httpx
- pillow
- pandas
- requests

## Project Structure

```
socialpulse/
├── frontend/
│   ├── index.html          # Main UI
│   ├── style.css          # Styling
│   └── script.js          # Frontend logic
├── backend/
│   ├── main.py            # FastAPI application
│   ├── api/
│   │   ├── analyze.py     # Analysis endpoints
│   │   └── reports.py     # Report endpoints
│   ├── agents/
│   │   ├── content_agent.py    # Content understanding
│   │   ├── claim_agent.py      # Claim extraction
│   │   ├── research_agent.py   # Web research
│   │   ├── media_agent.py      # Media analysis
│   │   ├── risk_agent.py       # Risk assessment
│   │   └── report_agent.py     # Report generation
│   ├── graph/
│   │   ├── state.py       # LangGraph state
│   │   └── workflow.py    # Analysis workflow
│   ├── services/
│   │   ├── storage_service.py  # S3/Local storage
│   │   ├── vision_service.py   # OCR/Vision
│   │   ├── sentiment_service.py # Sentiment analysis
│   │   ├── research_service.py # Web research
│   │   └── media_service.py    # Media analysis
│   ├── models/
│   │   └── schemas.py     # Pydantic models
│   ├── utils/
│   │   ├── validation.py  # Input validation
│   │   └── logging.py     # Logging setup
│   └── data/              # Local storage fallback
├── .env.example           # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional AWS S3 (uses local storage if not provided)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=socialpulse-bucket

# Optional Research API
SEARCH_API_KEY=your_search_api_key

# Optional LangSmith
LANGSMITH_API_KEY=your_langsmith_key

# Demo Mode
DEMO_MODE=false
```

## Setup Instructions

### 1. Environment Setup
```bash
# Clone/create project directory
mkdir socialpulse
cd socialpulse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Gemini API Setup
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Add to `.env` file: `GEMINI_API_KEY=your_key`

### 3. AWS Setup (Optional)
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Create S3 bucket
aws s3 mb s3://socialpulse-bucket
```

### 4. Research API Setup (Optional)
- Get API key from search provider
- Add to `.env`: `SEARCH_API_KEY=your_key`

## Running the Application

### Start Backend
```bash
cd backend
python main.py
```
Backend runs on: http://localhost:8000

### Start Frontend
Open `frontend/index.html` in a web browser or serve with:
```bash
cd frontend
python -m http.server 8080
```
Frontend runs on: http://localhost:8080

## API Documentation

### Endpoints

#### `GET /api/health`
Check service health
```json
{"status": "healthy", "timestamp": "2026-10-13T..."}
```

#### `POST /api/analyze`
Upload image for analysis
- **Content-Type**: `multipart/form-data`
- **Body**: `image` file (PNG/JPG/JPEG/WEBP, max 10MB)

**Response**:
```json
{
  "analysis_id": "SP-2026-000001",
  "status": "processing"
}
```

#### `GET /api/analyze/{analysis_id}`
Check analysis status
```json
{
  "analysis_id": "SP-2026-000001",
  "status": "completed",
  "progress": 100,
  "report_url": "/api/report/SP-2026-000001"
}
```

**Status Values**:
- `received` → `validating` → `uploaded` → `extracting` → `analyzing` → `researching` → `verifying` → `generating_report` → `completed` / `failed`

#### `GET /api/report/{analysis_id}`
Get final analysis report
```json
{
  "analysis_id": "SP-2026-000001",
  "content": {...},
  "claim": {...},
  "sentiment": {...},
  "media_analysis": {...},
  "research": {...},
  "risk_assessment": {...},
  "report": {...}
}
```

## Demo Mode

When external APIs are unavailable, enable demo mode:
```bash
DEMO_MODE=true
```

Demo mode provides:
- Sample OCR results
- Mock research data (clearly labeled)
- Deterministic risk scores
- All outputs marked as "DEMO DATA"

## Example Workflow

1. **Upload**: User uploads screenshot of social media post
2. **Validation**: System validates image format and size
3. **Storage**: Image stored in S3 or local directory
4. **OCR**: Extract text using Gemini Vision API
5. **Content Analysis**: Understand content structure and topics
6. **Claim Extraction**: Identify main verifiable claims
7. **Parallel Analysis**:
   - Sentiment analysis of text
   - Media authenticity assessment
   - Web research for claim verification
8. **Risk Assessment**: Calculate explainable risk score
9. **Report Generation**: Create professional intelligence report
10. **Display**: Show results in frontend dashboard

## Security Notes

- All API keys stored in environment variables
- File uploads validated for type, size, and content
- AWS credentials never exposed to frontend
- Input sanitization for all user data
- Safe handling of external research content
- Private S3 bucket with least privilege access

## Limitations

- Image analysis limited to visible content
- Media authenticity detection based on available indicators
- Research quality depends on available sources
- Risk scoring is AI-assisted, not scientifically validated
- Currently supports image input only (no video/audio)

## Future Enhancements

- Video content analysis
- Social platform API integration
- Advanced deepfake detection
- Multi-language support
- User authentication and history
- Batch processing
- Real-time monitoring feeds
- Custom risk scoring models
- Integration with threat intelligence feeds

## Testing

```bash
# Test complete workflow
python -m pytest tests/

# Manual testing
curl -X POST "http://localhost:8000/api/analyze" \
  -F "image=@test_image.png"
```

## Troubleshooting

### Common Issues

1. **"Gemini API Error"**: Check API key in `.env`
2. **"Storage Error"**: Verify AWS credentials or check local permissions
3. **"Analysis Failed"**: Check logs in `backend/logs/`
4. **"Research Unavailable"**: Research API key missing (non-critical)

### Logs
Check `backend/logs/socialpulse.log` for detailed error information.

## Contributing

This is a prototype. For production deployment:
1. Add proper authentication
2. Implement rate limiting
3. Add comprehensive testing
4. Set up monitoring and alerting
5. Add database for persistence
6. Implement caching layer
7. Add API documentation with OpenAPI