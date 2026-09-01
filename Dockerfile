FROM python:3.12-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 net-tools \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY macchanger_pro.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[dev]

ENTRYPOINT ["macchanger-pro"]
CMD ["--help"]

