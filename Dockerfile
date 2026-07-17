# ============================================================
# PlantCare-AI — Dockerfile for Hugging Face Spaces
# ============================================================

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install CPU-only PyTorch first (much smaller than CUDA version, fits Railway free tier)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir timm fastapi uvicorn python-multipart Pillow huggingface_hub python-dotenv gtts requests

# Copy application source code
COPY . .

# Create required directories
RUN mkdir -p uploads output_audio

# Expose port 7860 (Hugging Face Spaces standard)
EXPOSE 7860

# Run the FastAPI app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
