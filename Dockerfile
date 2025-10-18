FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Upgrade pip/setuptools/wheel first (ko'p dependency muammolarni bartaraf etadi)
RUN python -m pip install --upgrade pip setuptools wheel

# Agar dependency resolution xatolik bersa, legacy resolver bilan sinab ko'ramiz
RUN pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt

CMD ["python", "bot.py"]
