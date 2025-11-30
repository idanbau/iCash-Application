FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install service dependencies
COPY dashboard-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install the shared library
COPY common /app/common
RUN pip install --no-cache-dir /app/common

# Copy the service source
COPY dashboard-service /app

EXPOSE 8002
ENV GUNICORN_CMD_ARGS="--access-logfile - --error-logfile - --log-level info"
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8002", "wsgi:app"]
