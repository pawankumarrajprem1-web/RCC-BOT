FROM python:3.11-slim

# Install LibreOffice, Fontconfig, and robust Hindi/Devanagari Fonts from Debian repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    wget \
    fontconfig \
    fonts-noto \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-extra \
    fonts-dejavu \
    fonts-liberation \
    fonts-samyak-deva \
    fonts-nakula \
    fonts-lohit-deva \
    && rm -rf /var/lib/apt/lists/*

# Custom Google Fonts (Corrected Raw URLs) & Cache Refresh
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    wget -q https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-ExtraBold.ttf -O /usr/share/fonts/truetype/custom/Poppins-ExtraBold.ttf && \
    wget -q https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf -O /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
    wget -q https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf -O /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    wget -q https://raw.githubusercontent.com/chillu/sanskrit-font/master/SanskritText.ttf -O /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    fc-cache -f -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
