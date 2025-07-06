FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x run.py
RUN useradd --create-home --shell /bin/bash pyserve
RUN mkdir -p logs ssl static templates && \
    chown -R pyserve:pyserve /app && \
    chmod 755 /app/logs
USER pyserve
EXPOSE 8000 8443
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket; socket.create_connection(('localhost', 8000), timeout=3)" || exit 1
CMD ["python", "run.py", "-c", "config.docker.yaml"]
