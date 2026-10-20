FROM python:3.12-alpine
RUN pip install --no-cache-dir pytest==8.4.2
WORKDIR /work
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
USER 65534:65534
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "/work"]
