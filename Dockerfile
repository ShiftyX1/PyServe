FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x run.py
RUN useradd --create-home --shell /bin/bash pyserve
RUN mkdir -p logs ssl static templates && \
    chown -R pyserve:pyserve /app && \
    chmod 755 /app/logs && \
    chmod 755 /app/ssl && \
    chmod 644 /app/ssl/* 2>/dev/null || true
USER pyserve
EXPOSE 8000 8443
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import socket, os; socket.create_connection(('localhost', int(os.environ.get('PYSERVE_PORT', '8000'))), timeout=3)" || exit 1
CMD ["python", "run.py", "--host", "0.0.0.0"]
