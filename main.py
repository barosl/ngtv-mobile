#!/usr/bin/env python

from flask import Flask
app = Flask(__name__, static_url_path='')

from flask import render_template, request, url_for, session, redirect
import requests
import re

@app.route('/login/', methods=['POST'])
def login():
	username = request.form['username']
	password = request.form['password']
	sess = requests.Session()
	res = sess.post('http://www.nicegame.tv/users/member/login/', data={'userid': username, 'passwd': password})
	res.encoding = 'utf-8'
	if u'empty_login_alert_area' in res.text:
		return 'Login failed.\n'

	session['php_sess_id'] = res.cookies['PHPSESSID']
	return redirect(url_for('index'))

@app.route('/page/<int:page_id>')
def page(page_id):
	cookies = {}
	if 'php_sess_id' in session:
		cookies['PHPSESSID'] = session['php_sess_id']

	res = requests.get('http://www.nicegame.tv/board/bbs/view/1/7/-/-/%d/0/' % page_id, cookies=cookies)
	res.encoding = 'utf-8'

	try:
		user_nick = re.search(u'(?s)<div class="name_text_area">.*?<b>(.*?)</b>', res.text).group(1)
		user = {'nick': user_nick}
	except AttributeError: user = None

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
		'user': user,
		'page_id': page_id,
	}

	return render_template('page.html', **vals)

@app.route('/new/', methods=['GET', 'POST'])
def new():
	if request.method == 'POST':
		cookies = {}
		if 'php_sess_id' in session:
			cookies['PHPSESSID'] = session['php_sess_id']

		name = request.form['name']
		body = request.form['body']
		res = requests.post('http://www.nicegame.tv/board/bbs/write/1/7/', data={'title': name, 'body_text': body}, cookies=cookies)
		res.encoding = 'utf-8'

		page_id = int(re.search(u'<div id="bbs_report_(.*?)"', res.text).group(1))
		return redirect(url_for('page', page_id=page_id))

	vals = {}

	return render_template('new.html', **vals)

@app.route('/page/<int:page_id>/new/', methods=['POST'])
def new_comm(page_id):
	cookies = {}
	if 'php_sess_id' in session:
		cookies['PHPSESSID'] = session['php_sess_id']

	body = request.form['body']

	res = requests.post('http://www.nicegame.tv/board/bbs/write_comment/1/7/-/-/%d' % page_id, data={'comment': body}, cookies=cookies)
	res.encoding = 'utf-8'

	return redirect(url_for('page', page_id=page_id))

@app.route('/')
def index():
	cookies = {}
	if 'php_sess_id' in session:
		cookies['PHPSESSID'] = session['php_sess_id']
	res = requests.get('http://www.nicegame.tv/board/bbs/lists/1/7/', cookies=cookies)
	res.encoding = 'utf-8'

	try:
		user_nick = re.search(u'(?s)<div class="name_text_area">.*?<b>(.*?)</b>', res.text).group(1)
		user = {'nick': user_nick}
	except AttributeError: user = None

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
		'user': user,
	}

	return render_template('index.html', **vals)

@app.route('/logout/')
def logout():
	session.pop('php_sess_id', None)
	return redirect(url_for('index'))

app.secret_key = 'hgrlahglaehgilaheilahelghaelgahglaheglageaeglhaeage'

if __name__ == '__main__':
	app.debug = True
	app.run()
