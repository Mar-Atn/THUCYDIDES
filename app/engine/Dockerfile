FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy engine code into /app/engine/ so "python -m engine.main" works
COPY . ./engine/

CMD ["python", "-m", "engine.main"]
