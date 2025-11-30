FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install service dependencies first for better cache reuse
COPY api-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Bring in the shared package and install it
COPY common /app/common
RUN pip install --no-cache-dir /app/common

# Copy the service source
COPY api-service /app

EXPOSE 8001

COPY api-service/entrypoint.sh /app/entrypoint.sh
# Normalize line endings
RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
