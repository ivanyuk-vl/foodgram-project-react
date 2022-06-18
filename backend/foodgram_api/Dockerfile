FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --upgrade pip --no-cache-dir
RUN pip3 install -r /app/requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram_api.wsgi:application", "--bind", "0:8000"]