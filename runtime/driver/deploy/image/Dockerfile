FROM python:3.7
WORKDIR /src/
COPY *.py ./
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN git clone https://github.com/silveryfu/kopf.git;
RUN cd kopf; git checkout master; pip install -e .
#CMD sleep 3600 # debug
CMD python3 driver.py