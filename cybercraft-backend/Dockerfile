FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs backups server_files media staticfiles

EXPOSE 8000

CMD ["python", "manage.py", "migrate", "&&", "daphne", "-b", "0.0.0.0", "-p", "8000", "cybercraft_backend.asgi:application"]