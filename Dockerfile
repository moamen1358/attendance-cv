FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04

ENV PYTHON_VERSION=3.12 \
    DEBIAN_FRONTEND=noninteractive

# Install Python 3.12 and system dependencies
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    ca-certificates \
    build-essential \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update --fix-missing \
    && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    && ln -sf /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && python3 -m ensurepip --upgrade \
    && ln -s /usr/local/bin/pip3 /usr/bin/pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Fix for blinker distutils issue and install dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python3 -m pip install --no-cache-dir --ignore-installed blinker \
    && (for i in {1..5}; do python3 -m pip install --no-cache-dir --ignore-installed blinker --timeout=300 -r requirements.txt && break || sleep 15; done) \
    && python3 -m pip uninstall -y onnxruntime-gpu \
    && python3 -m pip install --no-cache-dir onnxruntime-gpu==1.20.1 \
    && which streamlit \
    && streamlit --version

# Ensure pip's bin directory is in PATH
ENV PATH="/usr/local/bin:${PATH}"

COPY . .

# Set CUDA environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
ENV PATH=/usr/local/cuda/bin:$PATH

EXPOSE 8501

# Copy and set up startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
