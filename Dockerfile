# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV BRUIN_INSTALL_DIR=/usr/local/bin

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Bruin CLI
RUN curl -LsSf https://getbruin.com/install/cli | sh -s -- -b $BRUIN_INSTALL_DIR

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Initialize a git repository to satisfy Bruin's requirement for a git root
RUN git init

# Set default port for local usage (Cloud Run will override this automatically)
ENV PORT=8501

# Run streamlit with the port defined by the environment variable
CMD streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0
