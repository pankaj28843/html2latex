FROM python:2.7-slim

ENV PYTHONUNBUFFERED 1

# 1. Update the package index and install minimal tools required for adding sources
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    gnupg2 \
    dirmngr \
 && rm -rf /var/lib/apt/lists/*

# 2. Enable deb-src for building from source if needed (Debian-based)
RUN echo 'deb-src http://deb.debian.org/debian buster main' >> /etc/apt/sources.list

# 3. Now install any build dependencies for lxml
RUN apt-get update \
&& apt-get install -y --no-install-recommends \
    git \
    libenchant1c2a \
 && apt-get build-dep -y --no-install-recommends \
    lxml \
 && rm -rf /var/lib/apt/lists/*

# 4. Ensure pip is upgraded to a version known to work with Python 2.7
RUN pip install --no-cache-dir --upgrade pip==20.3.4

# Set up a working directory
WORKDIR /app

# 5. Copy requirements to leverage Docker layer caching if they change
COPY requirements/ /app/requirements/
COPY requirements.txt /app/requirements.txt

# 6. Install your dev requirements
RUN pip install --no-cache-dir -r /app/requirements/dev.txt

# 7. Copy the rest of your project
COPY . /app

# Expose the Flask port
EXPOSE 15005

# Default command to run your Flask app
CMD ["/bin/bash", "-c", "cd /app && python setup.py develop && python demo-app/app.py"]
