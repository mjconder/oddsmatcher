FROM python:3.12-slim

WORKDIR /app

# Install the test runner first, before copying any source, so this layer
# stays cached until the pin changes. Pinned to match the dev extras and the
# CI tests job, so the container can't drift onto a different pytest.
RUN pip install --no-cache-dir pytest==8.2.2

COPY . .
RUN pip install --no-cache-dir --no-deps -e .

# Default: run the test suite. `docker run --rm oddsmatcher` gates on green tests.
CMD ["pytest", "-q"]
