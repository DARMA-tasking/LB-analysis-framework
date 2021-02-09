FROM python:3.8-slim-buster

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y git xvfb

COPY src /lbaf/src
COPY data /lbaf/data
COPY requirements.txt /lbaf/requirements.txt
COPY scripts/entrypoint.sh /lbaf/entrypoint.sh
COPY scripts/test_lbaf.py /lbaf/tests/test_lbaf.py
COPY scripts/run_tests.sh /lbaf/tests/run_tests.sh

WORKDIR /lbaf
RUN mkdir /lbaf/in /lbaf/out
RUN pip install virtualenv
RUN virtualenv --python /usr/local/bin/python3.8 venv
RUN /bin/sh venv/bin/activate && pip install -r requirements.txt

ENV PYTHONPATH /lbaf/venv/lib/python3.8/site-packages:/lbaf:/lbaf/src
ENV DISPLAY :99.0

RUN ["chmod", "+x", "/lbaf/entrypoint.sh"]
RUN ["chmod", "+x", "/lbaf/tests/run_tests.sh"]
RUN ["/bin/sh", "/lbaf/tests/run_tests.sh"]
ENTRYPOINT ["/lbaf/entrypoint.sh"]