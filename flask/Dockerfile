# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Install required packages
RUN apt-get update -qq \
      && apt-get install -y --no-install-recommends \
         build-essential \
         python3-dev \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/*

# Copy only the application code
COPY . /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Environment variables to define volumes inside the container
# These paths serão mapeados para sua máquina host
ENV DATABASE_PATH=/app/database.db
ENV IMAGES_PATH=/app/static/img/images

# CMD para rodar a aplicação Flask
CMD ["python", "app.py"]
