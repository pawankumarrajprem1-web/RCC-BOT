FROM python:3.11-slim


# Install LibreOffice, Fontconfig, and robust Hindi/Devanagari Fonts from Debian repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    fontconfig \
    fonts-noto \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-noto-extra \
    fonts-dejavu \
    fonts-liberation \
    fonts-samyak-deva \FROM python:3.11-slim

# नॉन-इंटरैक्टिव मोड सेट करें ताकि msfonts का एग्रीमेंट अपने आप स्वीकार हो सके
ENV DEBIAN_FRONTEND=noninteractive

# 1. सिस्टम डिपेंडेंसीज, LibreOffice, curl और सभी मुख्य MS Word / Devanagari फोंट्स इंस्टॉल करें
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

# 2. कस्टम फोल्डर बनाएं और curl के जरिए Poppins व SanskritText फोंट्स डाउनलोड करें (एरर-फ्री तरीका)
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf -o /usr/share/fonts/truetype/custom/Poppins-ExtraBold.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf -o /usr/share/fonts/truetype/custom/Poppins-Bold.ttf && \
    curl -L https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf -o /usr/share/fonts/truetype/custom/Poppins-Regular.ttf && \
    curl -L https://github.com/chillu/sanskrit-font/raw/master/SanskritText.ttf -o /usr/share/fonts/truetype/custom/SanskritText.ttf && \
    fc-cache -f -v

# 3. वर्किंग directory सेट करें
WORKDIR /app

# 4. पाइथन रिक्वायरमेंट्स इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. प्रोजेक्ट की बाकी फाइलें कॉपी करें
COPY . .

# 6. पोर्ट ओपन करें और ऐप रन करें
EXPOSE 8080

CMD ["python", "main.py"]
    fonts-nakula \
    fonts-lohit-deva \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create custom font directory inside container
RUN mkdir -p /usr/share/fonts/truetype/custom

# Copy fonts directly from your local project folder to the container
# (Make sure you have a folder named 'fonts' in your project root containing these .ttf files)
COPY fonts/ /usr/share/fonts/truetype/custom/

# Refresh system font cache
RUN fc-cache -f -v

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
