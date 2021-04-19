FROM python:3.7
WORKDIR /src/
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN git clone https://github.com/silveryfu/kopf.git;
RUN cd kopf; git checkout master; pip install -e .
COPY ./digi ./digi
CMD python3 -m digi
