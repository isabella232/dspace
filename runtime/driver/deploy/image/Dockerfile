FROM python:3.7
WORKDIR /src/

RUN pip install digi
RUN git clone https://github.com/silveryfu/kopf.git;
RUN cd kopf; git checkout master; pip install -e .

COPY . .
RUN (ls thirdparty.txt >> /dev/null 2>&1 && pip install -r thirdparty.txt) || true
#RUN pip install -r requirements.txt

CMD python3 handler.py
