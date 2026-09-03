FROM python:3.11-slim

# Install LibreOffice, Fontconfig, and Devanagari Hindi Fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    wget \
    fontconfig \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-dejavu \
    fonts-liberation \
    fonts-samyak-deva \
    && rm -rf /var/lib/apt/lists/*

# Custom Google Fonts & Sanskrit Text Font download
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf -O /usr/share/fonts/truetype/custom/Poppins-ExtraBold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -O /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -O /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    wget -q https://github.com/chillu/sanskrit-font/raw/master/SanskritText.ttf -O /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    fc-cache -f -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
