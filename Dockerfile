FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"

# Default: run the test suite. `docker run --rm oddsmatcher` gates on green tests.
CMD ["pytest", "-q"]
