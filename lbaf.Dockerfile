FROM python:3.8-slim-buster
ARG INSTALL_PREFIX=/home/install
ARG ZOLTAN=$INSTALL_PREFIX
ARG ZOLTAN_INCLUDE=/usr/include/trilinos
ARG ZOLTAN_LIBRARY=/usr/lib/x86_64-linux-gnu
ARG USE_TRILINOS=1

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y git xvfb
RUN apt-get install -y openmpi-bin libopenmpi-dev libtrilinos-zoltan-dev build-essential

COPY requirements-3.8.txt /lbaf/requirements.txt

WORKDIR /home
RUN git clone https://github.com/pypr/pyzoltan.git
WORKDIR /home/pyzoltan
RUN sh build_zoltan.sh $INSTALL_PREFIX

WORKDIR /lbaf
RUN python -m venv venv
RUN venv/bin/pip install --upgrade pip
RUN venv/bin/pip install -r /home/pyzoltan/requirements.txt && venv/bin/pip install pyzoltan --no-build-isolation && venv/bin/pip install -r /lbaf/requirements.txt

ENV PYTHONPATH /lbaf/venv/lib/python3.8/site-packages:/lbaf:/lbaf/src
ENV DISPLAY :99.0

COPY src /lbaf/src
COPY data /lbaf/data
COPY scripts/entrypoint.sh /lbaf/entrypoint.sh
COPY scripts/test_lbaf.py /lbaf/tests/test_lbaf.py
COPY scripts/run_tests.sh /lbaf/tests/run_tests.sh
COPY scripts/test_config/conf.yaml /lbaf/src/Applications/conf.yaml

WORKDIR /lbaf
RUN mkdir /lbaf/in /lbaf/out

RUN ["chmod", "+x", "/lbaf/entrypoint.sh"]
ENTRYPOINT ["/lbaf/entrypoint.sh"]