FROM python:3.7
COPY . /src
RUN pip install kopf
CMD kopf run /src/handlers.py --verbose