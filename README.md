# NetHandover AI

NetHandover AI is an intelligent telecom analytics platform for predicting handover failures, analyzing coverage quality, and monitoring QoS in mobile networks. The project combines machine learning, KPI analysis, and a knowledge-based conversational assistant to help network engineers detect issues, optimize performance, and make faster operational decisions.

## Overview

This project is designed to support mobile network monitoring and optimization by providing:

- coverage prediction and analysis,
- QoS and handover quality assessment,
- AI-powered explanations from a telecom knowledge base,
- a web dashboard for interactive exploration and decision support.

It is built for telecom operators, engineers, and researchers who want actionable insights from network data and predictive models.

## Features

- Coverage prediction using trained machine learning models
- QoS degradation and quality analysis
- Handover-related insights and network troubleshooting support
- RAG-based conversational assistant powered by telecom knowledge documents
- Interactive dashboard for network metrics and predictions
- FastAPI backend and React frontend architecture

## Tech Stack

### Backend
- Python
- FastAPI
- Pydantic
- scikit-learn
- ChromaDB
- Sentence Transformers
- Google Gemini API

### Frontend
- React
- Vite
- Tailwind CSS
- Recharts

## Project Structure

```text
.
├── app/
│   ├── config.py
│   ├── coverage_service.py
│   ├── qos_service.py
│   ├── rag_service.py
│   ├── main.py
│   ├── models/
│   ├── routers/
│   └── utils/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── knowledge_base/
├── models/
├── output/
├── data/
├── chroma_db/
├── run_backend.py
├── requirements.txt
├── .env
├── README.md
└── ...
```

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+
- Node.js 18+
- npm
- A valid Gemini API key

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <project-folder>
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure environment variables

Create a `.env` file in the project root with the following values:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=models/gemini-flash-latest
APP_ENV=development
DEBUG=True
```

## Run the Project

### Start the backend

```bash
python run_backend.py
```

The API will be available at:

- http://localhost:8001
- Swagger docs: http://localhost:8001/docs

### Start the frontend

```bash
cd frontend
npm run dev
```

The frontend will run at:

- http://localhost:5173

## Main API Areas

The backend exposes endpoints for:

- coverage prediction,
- QoS prediction,
- network data processing,
- AI chat and assistant queries.

## Use Cases

- identify weak coverage zones,
- detect degradation trends in mobile networks,
- estimate QoS outcomes for different network conditions,
- answer telecom troubleshooting questions with contextual AI support.

## License

This project is currently distributed for academic . 

## Contributing

Contributions are welcome. You can open issues, suggest improvements, and submit pull requests.

## Contact

For questions or collaboration, contact me.
