FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean

COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 10000

CMD python manage.py collectstatic --noinput && \
    python manage.py migrate && \
    python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); U.objects.filter(username='yana').exists() or U.objects.create_superuser('yana', 'admin@example.com', 'helloworld123')" && \
    gunicorn CleaningApp.wsgi:application --bind 0.0.0.0:10000