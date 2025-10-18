FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --upgrade typing_extensions pydantic
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
