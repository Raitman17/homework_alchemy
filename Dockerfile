FROM python:3.10.13

WORKDIR /homework

COPY . .
COPY requirements.txt .

RUN pip install -r requirements.txt

RUN chmod +x script.sh

ENTRYPOINT ["./script.sh"]
# CMD ["python3", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers=4", "app:app"]