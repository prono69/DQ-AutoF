FROM python:3.12-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /DQTheFileDonorBot

# Copy requirements first so this layer is cached unless deps change
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the bot's source code
COPY . .

CMD ["python3", "bot.py"]