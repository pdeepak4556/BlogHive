FROM python:slim

RUN useradd deepak

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install itsdangerous==2.0.1

RUN mkdir bloghive migrations
RUN chown -R deepak:deepak /app

COPY bloghive/ bloghive/
COPY migrations/ migrations/
COPY run.py .

ENV FLASK_APP run:app

USER deepak

EXPOSE 80

CMD ["gunicorn", "-b", "0.0.0.0:80", "run:app"]