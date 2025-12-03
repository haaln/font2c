#!/bin/bash

python3 -m venv .
[ -f ./bin/pip ] && ./bin/pip install --upgrade pip || ./bin/python3 pip install -r requirements.txt
[ -f ./bin/pip ] && ./bin/pip install -r requirements.txt
