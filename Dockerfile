FROM python:3.9.7-slim

ENV WORKDIR=/app

WORKDIR $WORKDIR

# EXPOSE 8000

# RUN pip install --upgrade pip
COPY ./requirements.txt $WORKDIR/requirements.txt
RUN pip install -r requirements.txt
COPY ./main_app $WORKDIR

CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker"]
