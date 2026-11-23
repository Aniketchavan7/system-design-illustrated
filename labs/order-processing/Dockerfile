FROM python:3.12-slim
WORKDIR /lab
RUN pip install --no-cache-dir pika==1.3.2 psycopg[binary]==3.2.9
COPY lab.py .
ENTRYPOINT ["python", "-u", "lab.py"]
