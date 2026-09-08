FROM python:3.10-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        gcc \
        python3-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /DQTheFileDonorBot

COPY requirements.txt .
RUN pip3 install --no-cache-dir -U pip && \
    pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "bot.py"]