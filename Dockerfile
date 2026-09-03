FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. सिस्टम डिपेंडेंसीज, LibreOffice, Fontconfig और सारे स्टैंडर्ड फोंट्स इंस्टॉल करें
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    curl \
    fontconfig \
    cabextract \
    xfonts-utils \
    fontforge \
    && echo "msttcorefonts msttcorefonts/accepted-mshula select true" | debconf-set-selections \
    && apt-get install -y --no-install-recommends ttf-mscorefonts-installer \
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

# 2. आपके द्वारा उपयोग किए गए विशेष फोंट्स (Monotype Corsiva, SanskritText, Bodoni, Algerian आदि) के लिए कस्टम फोल्डर और डाउनलोड सेटअप
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    curl -L https://github.com/chillu/sanskrit-font/raw/master/SanskritText.ttf -o /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -o /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -o /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    fc-cache -f -v

# 3. वर्किंग directory सेट करें
WORKDIR /app

# 4. पाइथन रिक्वायरमेंट्स इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. प्रोजेक्ट की बाकी फाइलें कॉपी करें
COPY . .

# 6. पोर्ट और रन कमांड
EXPOSE 8080
CMD ["python", "main.py"]
