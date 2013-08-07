#!/bin/sh

DIR=~barosl/dev/ngtv-m
APP=ngtvm
PORT=7001

VENV=~barosl/box/.sys/py
CFG_DIR=~barosl/web/cfgs

export APP_CFG=$CFG_DIR/$APP.py
[ -e $APP_CFG ] || { echo 'Configuration file not found.'; exit 1; }

. $VENV/bin/activate || exit 2

cd $DIR && exec $VENV/bin/gunicorn -b 127.0.0.1:$PORT $APP:app
