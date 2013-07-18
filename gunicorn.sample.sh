#!/bin/sh

DIR=~barosl/dev/ngtv-m
APP=ngtvm
PORT=7001

VENV=~barosl/box/.sys/py
CFG_DIR=~barosl/dev/cfgs

cd $DIR && APP_CFG=$CFG_DIR/$APP.py exec $VENV/bin/gunicorn -b 127.0.0.1:$PORT $APP:app
