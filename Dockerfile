FROM python:3.11-slim

# Install LibreOffice, Font tools and standard Devanagari/Hindi packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    wget \
    unzip \
    fontconfig \
    fonts-dejavu \
    fonts-liberation \
    fonts-gargi \
    fonts-kalimati \
    fonts-indic \
    fonts-lohit-deva \
    fonts-samyak-deva \
    fonts-noto-ui-core \
    && rm -rf /var/lib/apt/lists/*

# Google Fonts repository se Poppins Fonts direct install karein
RUN mkdir -p /usr/share/fonts/truetype/poppins && \
    wget https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf -O /usr/share/fonts/truetype/poppins/Poppins-ExtraBold.ttf && \
    wget https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -O /usr/share/fonts/truetype/poppins/Poppins-Bold.ttf && \
    wget https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -O /usr/share/fonts/truetype/poppins/Poppins-Regular.ttf && \
    fc-cache -f -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
