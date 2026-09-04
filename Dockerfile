FROM python:3.10-slim

# LibreOffice, fontconfig और हिंदी के बेसिक फॉन्ट्स इंस्टॉल करें
RUN apt-get update && apt-get install -y \
    libreoffice \
    fontconfig \
    fonts-noto-devanagari \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# आपके लोकल 'fonts' फोल्डर से सारे कस्टम फॉन्ट्स को सर्वर की सिस्टम फॉन्ट डायरेक्टरी में कॉपी करें
COPY fonts/ /usr/share/fonts/truetype/custom_fonts/

# Linux सर्वर को नए फॉन्ट्स की जानकारी देने के लिए फॉन्ट कैश रीफ्रेश करें
RUN fc-cache -f -v

# Python requirements इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड और टेम्पलेट फाइलें कॉपी करें
COPY . .

# पोर्ट एक्सपोज़ करें
EXPOSE 8080

# बॉट चालू करें
CMD ["python", "main.py"]
