FROM python:3.11-slim
WORKDIR /app

# Систем сангуудыг шинэчлэх (libgl1-mesa-glx-ийн оронд libgl1 ашиглав)
RUN apt-get update && apt-get install -y \
    build-essential \
    unar \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libadwaita-1-0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright-ийн Chromium-ийг суулгах
RUN playwright install chromium

# Радар зургуудыг контейнер доторх /app/visuals руу хуулах
# Энэ нь доторх скрипт /app/visuals/... гэж хандах боломжийг олгоно
COPY visuals/ /app/visuals/

COPY parser/main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
