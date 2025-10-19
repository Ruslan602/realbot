FROM python:3.11-slim

WORKDIR /app
COPY . /app

# 1️⃣ pip va asosiy vositalarni yangilash
RUN python -m pip install --upgrade pip setuptools wheel

# 2️⃣ typing_extensions va pydanticni oldindan yangilash
RUN pip install --upgrade typing_extensions pydantic

# 3️⃣ Loyihadagi kutubxonalarni o‘rnatish
RUN pip install --no-cache-dir -r requirements.txt

# 4️⃣ Botni ishga tushirish
CMD ["python", "bot.py"]
