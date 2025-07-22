FROM python:3.10-slim

WORKDIR /app1

COPY . /app1

RUN pip install --no-cache-dir -r requirement.txt

EXPOSE 5000

CMD ["python", "app.py"]
