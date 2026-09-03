FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# 1. सिस्टम डिपेंडेंसीज, LibreOffice, Java (javaldx error के लिए) और फोंट्स इंस्टॉल करें
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    default-jre-headless \
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

# 2. आपके सभी कस्टम फोंट्स (SanskritText, Poppins, Algerian, Cambria आदि) के लिंक्स
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    curl -L https://github.com/chillu/sanskrit-font/raw/master/SanskritText.ttf -o /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -o /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -o /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
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
