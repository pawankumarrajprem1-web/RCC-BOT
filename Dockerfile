FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. सिस्टम डिपेंडेंसीज, LibreOffice Writer/Impress, Java और यूनिकोड फोंट्स इंस्टॉल करें
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    default-jre-headless \
    wget \
    curl \
    fontconfig \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-dejavu \
    fonts-liberation \
    fonts-samyak-deva \
    && rm -rf /var/lib/apt/lists/*

# 2. आपके सभी फोंट्स (SanskritText, Poppins, Monotype Corsiva, Bodoni MT Condensed, Cambria, Algerian, Arial Unicode MS) और उनकी पूरी फैमिली के लिंक्स
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    # Sanskrit Text Family
    wget -q https://github.com/chillu/sanskrit-font/raw/master/SanskritText.ttf -O /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    # Poppins Family (Regular, Bold, ExtraBold)
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -O /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -O /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf -O /usr/share/fonts/truetype/custom/Poppins-ExtraBold.ttf && \
    # Devanagari Support
    wget -q https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari-Bold.ttf -O /usr/share/fonts/truetype/custom/NotoSansDevanagari-Bold.ttf && \
    # Monotype Corsiva
    wget -q https://github.com/google/fonts/raw/main/ofl/monotypecorsiva/MonotypeCorsiva.ttf -O /usr/share/fonts/truetype/custom/MonotypeCorsiva.ttf && \
    # Bodoni MT Condensed
    wget -q https://github.com/google/fonts/raw/main/ofl/bodoni/BodoniMT-Condensed.ttf -O /usr/share/fonts/truetype/custom/BodoniMT-Condensed.ttf && \
    # Cambria Family
    wget -q https://github.com/google/fonts/raw/main/ofl/cambria/Cambria.ttf -O /usr/share/fonts/truetype/custom/Cambria.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/cambria/Cambria-Bold.ttf -O /usr/share/fonts/truetype/custom/Cambria-Bold.ttf && \
    # Algerian
    wget -q https://github.com/google/fonts/raw/main/ofl/algerian/Algerian.ttf -O /usr/share/fonts/truetype/custom/Algerian.ttf && \
    # Arial Unicode MS
    wget -q https://github.com/google/fonts/raw/main/ofl/arialunicodems/ArialUnicodeMS.ttf -O /usr/share/fonts/truetype/custom/ArialUnicodeMS.ttf && \
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
