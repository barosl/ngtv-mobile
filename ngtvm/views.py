#!/usr/bin/env python

from . import app
from flask import render_template, request, url_for, session, redirect
import requests
import re
import lxml.etree, lxml.html

def err(msg):
	return render_template('err.html', msg=msg)

def req_with_sess():
	sess = requests.Session()
	if 'php_sess_id' in session: sess.cookies['PHPSESSID'] = session['php_sess_id']
	return sess

def parse_user(tree):
	try: user = {'nick': tree.cssselect('div.name_text_area b')[0].text_content().strip()}
	except IndexError: user = None
	return user

def inner_html(tree):
	return (tree.text or u'') + u''.join(lxml.etree.tostring(el, encoding=unicode, method='html') for el in tree)

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

	tree = lxml.html.fromstring(res.text)

	body_el = tree.cssselect('td.view_content')[0]

	for img in body_el.cssselect('img'):
		img.attrib.pop('onload', None)
		img.set('src', 'http://www.nicegame.tv'+img.get('src'))
		img.set('style', 'width: 100%;')

	comms = [{
		'author': row[0].text.strip(),
		'body': inner_html(row[1]).strip(),
	} for row in tree.cssselect('td.comment_text_cell')]

	vals = {
		'name': tree.cssselect('th.view_title')[0].text_content().strip(),
		'body': inner_html(body_el).strip(),
		'author': tree.cssselect('th.view_auther')[0].text_content().strip(),
		'comms': comms,
		'user': parse_user(tree),
		'page_id': page_id,
	}

	return render_template('page.html', **vals)

@app.route('/new/', methods=['GET', 'POST'])
def new():
	if request.method == 'POST':
		name = request.form['name']
		body = request.form['body']

		res = req_with_sess().post('http://www.nicegame.tv/board/bbs/write/1/7/', data={'title': name, 'body_text': body})
		page_id = int(re.search(u'([0-9]+)$', res.url).group(1))

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

	tree = lxml.html.fromstring(res.text)

	items = [{
		'url': url_for('page', page_id=int(row[0].text_content().strip())),
		'name': row[1].text_content().strip(),
		'author': row[2].text_content().strip(),
	} for row in tree.cssselect('table.board_list_table tbody tr:not(.list_notice)')]

	vals = {
		'items': items,
		'user': parse_user(tree),
	}

	return render_template('index.html', **vals)

@app.route('/logout/')
def logout():
	session.pop('php_sess_id', None)
	return redirect(url_for('index'))
