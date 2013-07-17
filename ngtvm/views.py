#!/usr/bin/env python

from . import app
from flask import render_template, request, url_for, session, redirect
import requests
import re

def err(msg):
	return render_template('err.html', msg=msg)

def req_with_sess():
	sess = requests.Session()
	if 'php_sess_id' in session: sess.cookies['PHPSESSID'] = session['php_sess_id']
	return sess

def parse_user(res):
	try: user = {'nick': re.search(ur'<div class="name_text_area">\s*<b>(.*?)</b>', res.text).group(1)}
	except AttributeError: user = None
	return user

@app.route('/login/', methods=['POST'])
def login():
	username = request.form['username']
	password = request.form['password']

	res = requests.post('http://www.nicegame.tv/users/member/login/', data={'userid': username, 'passwd': password})
	res.encoding = 'utf-8'

	if u'empty_login_alert_area' in res.text:
		return err('Login failed.'), 401

	session['php_sess_id'] = res.cookies['PHPSESSID']

	return redirect(url_for('index'))

@app.route('/page/<int:page_id>')
def page(page_id):
	res = req_with_sess().get('http://www.nicegame.tv/board/bbs/view/1/7/-/-/%d/0/' % page_id)
	res.encoding = 'utf-8'

	name = re.search(u'<th class="view_title">(.*?)</th>', res.text).group(1)
	body = re.search(u'(?s)<td colspan="2" class="view_content">(.*?)</td>', res.text).group(1)
	body = body.replace('<img src="/', '<img style="width: 100%;" src="http://www.nicegame.tv/')
	author = re.search(u'(?s)<th class="view_auther">.*?>(.*?)</th>', res.text).group(1)

	rows = re.findall(u'(?s)<td class="comment_text_cell">(.*?)</td>', res.text)
	comms = []
	for row in rows:
		mat = re.search(u'(?s)<p class="comment_nick">(.*?) <span.*?<p class="comment_text">(.*?)<ul', row)
		comm_author, comm_body = mat.groups()

		comm_body = re.sub(u'<img src="/images/board/btn.comment_delete.png".*?>', u'', comm_body)

		comms.append({
			'author': comm_author,
			'body': comm_body,
		})

	vals = {
		'name': name,
		'body': body,
		'author': author,
		'comms': comms,
		'user': parse_user(res),
		'page_id': page_id,
	}

	return render_template('page.html', **vals)

@app.route('/new/', methods=['GET', 'POST'])
def new():
	if request.method == 'POST':
		name = request.form['name']
		body = request.form['body']
		res = req_with_sess().post('http://www.nicegame.tv/board/bbs/write/1/7/', data={'title': name, 'body_text': body})
		res.encoding = 'utf-8'

		page_id = int(re.search(u'<div id="bbs_report_(.*?)"', res.text).group(1))
		return redirect(url_for('page', page_id=page_id))

	vals = {}

	return render_template('new.html', **vals)

@app.route('/page/<int:page_id>/new/', methods=['POST'])
def new_comm(page_id):
	body = request.form['body']

	res = req_with_sess().post('http://www.nicegame.tv/board/bbs/write_comment/1/7/-/-/%d' % page_id, data={'comment': body})
	res.encoding = 'utf-8'

	return redirect(url_for('page', page_id=page_id))

@app.route('/')
def index():
	res = req_with_sess().get('http://www.nicegame.tv/board/bbs/lists/1/7/')
	res.encoding = 'utf-8'

	rows = re.findall(u'(?s)<tr class="">(.*?)</tr>', res.text)
	items = []
	for row in rows:
		mat = re.search(u'(?s)<a href="(.*?)".*?>(.*?)</a>.*?<td>(.*?)</td>', row)
		url, name, author = mat.groups()
		url = url_for('page', page_id=int(re.search(u'/-/([0-9]+)/', url).group(1)))
		items.append({
			'url': url,
			'name': name,
			'author': author,
		})

	vals = {
		'items': items,
		'user': parse_user(res),
	}

	return render_template('index.html', **vals)

@app.route('/logout/')
def logout():
	session.pop('php_sess_id', None)
	return redirect(url_for('index'))
