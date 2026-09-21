# --- STAGE 1: Builder ---
FROM python:3.12-slim-bookworm AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        gcc \
        python3-dev \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir --user -r requirements.txt


# --- STAGE 2: Runner ---
FROM python:3.12-slim-bookworm AS runner

# Install git only if your python code executes git commands at runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /DQTheFileDonorBot

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

CMD ["python3", "bot.py"]
