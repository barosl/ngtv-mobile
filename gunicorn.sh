#!/bin/sh

DIR=~barosl/dev/ngtv-m
APP=main
PORT=7001

VENV=~barosl/box/.sys/py

cd $DIR && exec $VENV/bin/gunicorn -b 127.0.0.1:$PORT $APP:app
