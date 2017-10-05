FROM python:alpine

RUN apk add --no-cache gcc g++ make libffi-dev openssl-dev && \
    pip install python-telegram-bot requests block-io

COPY run.py /

CMD ["python", "run.py"]
