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
    fonts-samyak-deva \
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
