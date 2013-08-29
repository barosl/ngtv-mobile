#!/usr/bin/env python

SECRET_KEY = 'development key'

from flask import Flask
app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_envvar('APP_CFG', silent=True)

import views
