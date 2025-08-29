#use official python image
FROM python:3.10-slim

#set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

#set work directory
WORKDIR /app

#install OS dependencies
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

#copy requirements
COPY requirements.txt .

COPY .env .

#copy project files
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# expose port
EXPOSE 8080

# run FastAPI with uvicorn
CMD ["uvicorn","api.main:app","--host","0.0.0.0","--port","8080","--workers","4"]
