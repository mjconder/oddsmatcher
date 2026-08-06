FROM python:3.12-slim

WORKDIR /app

# Install the test runner in its own layer so it stays cached until the
# manifest changes. Running the suite is all the container does, so it
# needs pytest and the package itself — not the ruff/mypy dev extras.
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir pytest

COPY . .
RUN pip install --no-cache-dir --no-deps -e .

# Default: run the test suite. `docker run --rm oddsmatcher` gates on green tests.
CMD ["pytest", "-q"]
