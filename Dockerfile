FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV PYTHON_VERSION=3.11 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Python 3.11 and system dependencies, remove problematic packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    ca-certificates \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    git \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-distutils \
    && apt-get remove -y python3-blinker \
    && ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python get-pip.py \
    && rm get-pip.py \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with blinker conflict resolution
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python3 -m pip install --no-cache-dir --force-reinstall blinker>=1.6.2 \
    && python3 -m pip install --no-cache-dir --timeout=600 -r requirements.txt

# Copy models directory (these are large and don't change often)
COPY models/ /app/models/
COPY insightface/ /app/insightface/

# Copy the rest of the application
COPY src/ /app/src/
COPY *.py /app/
COPY *.db /app/
COPY *.crt /app/
COPY *.key /app/
COPY store/ /app/store/

# Create necessary directories and set permissions
RUN mkdir -p /app/store /app/uploads /app/logs \
    && chmod +x /app/src/*.py || true

# Set environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
ENV PATH=/usr/local/cuda/bin:$PATH
ENV PYTHONPATH=/app/src:/app
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200

# Set CUDA environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
ENV PATH=/usr/local/cuda/bin:$PATH
ENV PYTHONPATH=/app/src:/app
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200

# Create a startup script for better error handling
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Face Recognition App..."\n\
echo "🔍 Checking GPU availability..."\n\
nvidia-smi || echo "⚠️ GPU not available, will use CPU"\n\
echo "🧠 Checking models..."\n\
ls -la /app/models/ | head -5\n\
echo "⚙️ Starting Streamlit app..."\n\
cd /app\n\
exec python -m streamlit run src/login.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false' > /app/start.sh \
    && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

CMD ["/app/start.sh"]
