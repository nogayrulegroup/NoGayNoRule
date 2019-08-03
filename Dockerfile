FROM python:3.7.4-slim-stretch

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000/tcp

CMD [ "gunicorn", "--bind=0.0.0.0:8000", "--workers=4", "main:app" ]
