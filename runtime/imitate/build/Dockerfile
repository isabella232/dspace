FROM python:3.7
WORKDIR /src/
COPY *.py ./
COPY requirements.txt ./
RUN pip install -r requirements.txt
#CMD sleep 3600 # debug
CMD python3 handler.py