FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV DEBUG=False

RUN useradd -u 1001 appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

USER appuser
EXPOSE 8000
CMD ["python", "service.py"]
