FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables should be passed at runtime
# Environment variables should be passed at runtime
# Render provides PORT variable, but our keep_alive uses 8080 by default.
# Either way, for this simple bot script containing the thread, we just run python bot.py
CMD ["python", "bot.py"]
