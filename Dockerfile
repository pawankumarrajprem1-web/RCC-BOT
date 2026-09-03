FROM python:3.10-slim

# LibreOffice और सभी जरूरी हिंदी/संस्कृत देवनागरी तथा स्टैंडर्ड फोंट्स इंस्टॉल करें
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fontconfig \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-extra \
    fonts-devanagari \
    fonts-samyak-deva \
    fonts-kalapi \
    fonts-gargi \
    fonts-liberation \
    fonts-dejavu \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड कॉपी करें
COPY . .

# पोर्ट एक्सपोज़ करें
EXPOSE 8080

# बॉट चालू करें
CMD ["python", "main.py"]
