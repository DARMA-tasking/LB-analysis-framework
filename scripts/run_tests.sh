#!/bin/sh

export PYTHONPATH=/lbaf/venv/lib/python3.8/site-packages:/lbaf:/lbaf/src:/lbaf/utils
export DISPLAY=:99.0
/bin/sh /lbaf/venv/bin/activate
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
pip install -r requirements.txt
python /lbaf/tests/test_lbaf.py
