FROM python:3.7
COPY *.py /src/
RUN pip install kopf
#CMD sleep 3600 # debug
CMD kopf run /src/handlers.py --verbose