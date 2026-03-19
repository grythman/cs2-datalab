FROM python:3.10-slim

# 1. Системийн хамааралтай сангуудыг суулгах
# libgl1-mesa-glx-ийг libgl1-ээр сольсон
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 2. Ажлын хавтас үүсгэх
WORKDIR /app

# 3. Python сангуудыг суулгах
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    matplotlib \
    pandas \
    numpy \
    pillow \
    "moviepy<2.0.0" gTTS \
    moviepy \
    edge_tts

# 4. Кодоо хуулах
COPY . .

# 5. Ажиллуулах порт
EXPOSE 8001

# 6. Серверийг асаах
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
