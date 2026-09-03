FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. सिस्टम डिपेंडेंसीज, LibreOffice, Fontconfig और यूनिकोड/हिंदी फोंट्स इंस्टॉल करें
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    curl \
    fontconfig \
    ca-certificates \
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

# 2. आपके सभी फोंट्स और उनकी पूरी फैमिली (Regular, Bold, Italic) के डायरेक्ट लिंक्स
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    # Sanskrit Text Family
    curl -L https://github.com/chillu/sanskrit-font/raw/master/SanskritText.ttf -o /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    # Poppins Family (Regular & Bold)
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -o /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -o /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Italic.ttf -o /usr/share/fonts/truetype/custom/Poppins-Italic.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-BoldItalic.ttf -o /usr/share/fonts/truetype/custom/Poppins-BoldItalic.ttf && \
    # Monotype Corsiva Family
    curl -L https://github.com/google/fonts/raw/main/ofl/monotypecorsiva/MonotypeCorsiva.ttf -o /usr/share/fonts/truetype/custom/MonotypeCorsiva.ttf && \
    # Bodoni MT Condensed Family
    curl -L https://github.com/google/fonts/raw/main/ofl/bodoni/BodoniMT-Condensed.ttf -o /usr/share/fonts/truetype/custom/BodoniMT-Condensed.ttf && \
    # Cambria Family (Regular, Bold, Italic)
    curl -L https://github.com/google/fonts/raw/main/ofl/cambria/Cambria.ttf -o /usr/share/fonts/truetype/custom/Cambria.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/cambria/Cambria-Bold.ttf -o /usr/share/fonts/truetype/custom/Cambria-Bold.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/cambria/Cambria-Italic.ttf -o /usr/share/fonts/truetype/custom/Cambria-Italic.ttf && \
    # Arial Unicode MS Family
    curl -L https://github.com/google/fonts/raw/main/ofl/arialunicodems/ArialUnicodeMS.ttf -o /usr/share/fonts/truetype/custom/ArialUnicodeMS.ttf && \
    # Algerian Family
    curl -L https://github.com/google/fonts/raw/main/ofl/algerian/Algerian.ttf -o /usr/share/fonts/truetype/custom/Algerian.ttf && \
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
