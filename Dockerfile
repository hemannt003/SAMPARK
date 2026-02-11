FROM python:3.11-slim

# System deps for audio processing + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p /app/data/faiss_index

# Expose both FastAPI and Streamlit ports
EXPOSE 8000 8501

# Default: run FastAPI (override in docker-compose for Streamlit)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
