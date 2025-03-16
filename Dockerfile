FROM arm64v8/python:3.12-slim

RUN pip install pymongo

COPY . /app
WORKDIR /app

EXPOSE 3000 5001

CMD ["python", "main.py"]
