FROM apache/superset:4.1.2
USER root
COPY requirements.txt /tmp/tourism-superset-requirements.txt
RUN pip install --no-cache-dir -r /tmp/tourism-superset-requirements.txt
USER superset
