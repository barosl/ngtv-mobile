#!/usr/bin/env python

from . import app
from flask import render_template, request, url_for, session, redirect
import requests
import re
import lxml.html

def err(msg):
	return render_template('err.html', msg=msg)

def req_with_sess():
	sess = requests.Session()
	if 'php_sess_id' in session: sess.cookies['PHPSESSID'] = session['php_sess_id']
	return sess

def parse_user(tree):
	try:
		user = {
			'nick': tree.cssselect('div.name_text_area b')[0].text_content().strip(),
			'msg_cnt': int(tree.cssselect('li.memo_s span.color_red')[0].text),
		}
	except IndexError: user = None
	return user

def inner_html(tree):
	try: unicode
	except NameError: unicode = str

	return (tree.text or u'') + u''.join(lxml.html.tostring(el, encoding=unicode) for el in tree)

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
	res = req_with_sess().get('http://nicegame.tv/community/view/%d/?ccode=1&bcode=7&page=1' % page_id)
	res.encoding = 'utf-8'

	tree = lxml.html.fromstring(res.text)

	body_el = tree.cssselect('div.viewContent')[0]

	for img in body_el.cssselect('img'):
		img.attrib.pop('onload', None)
		img.set('style', 'width: 100%;')

	comms = [{
		'author': row[1].cssselect('strong')[0].text.strip(),
		'body': row[1][0].tail.strip(),
		'depth': 'cmtReply' in row.get('class'),
	} for row in tree.cssselect('li.commentLI')]

	nums = re.findall('[0-9]+', tree.cssselect('div.viewInfo2 span.infoRight')[0].text_content())

	vals = {
		'name': tree.cssselect('div.viewInfo1')[0].cssselect('span.infoLeft')[0].text_content().strip(),
		'body': inner_html(body_el).strip(),
		'author': tree.cssselect('div.viewInfo2')[0].cssselect('span.infoLeft')[0].text_content().strip(),
		'comms': comms,
		'user': parse_user(tree),
		'page_id': page_id,
		'date': tree.cssselect('div.viewInfo1')[0].cssselect('span.infoRight')[0].text_content().strip(),
		'views': nums[0],
		'votes': nums[1],
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
	res = req_with_sess().get('http://nicegame.tv/community/bbs_list/?ccode=1&bcode=7')
	res.encoding = 'utf-8'

	tree = lxml.html.fromstring(res.text)

	items = [{
		'url': url_for('page', page_id=int(row[0].text_content().strip())),
		'name': row[1].text_content().strip(),
		'author': row[2].text_content().strip(),
		'votes': int(row[3].text_content().strip()),
		'views': int(row[4].text_content().strip()),
		'date': row[5].text_content().strip(),
	} for row in tree.cssselect('div.bbs table tbody tr:not(.noticeList)')]

	vals = {
		'items': items,
		'user': parse_user(tree),
	}

	return render_template('index.html', **vals)

@app.route('/logout/')
def logout():
	req_with_sess().get('http://www.nicegame.tv/users/member/logout/')
	session.pop('php_sess_id', None)
	return redirect(url_for('index'))

@app.route('/msgs/')
def msgs():
	res = req_with_sess().get('http://www.nicegame.tv/memo/lists/')
	res.encoding = 'utf-8'

	tree = lxml.html.fromstring(res.text)

	msgs = [{
		'author': row[2].text_content().strip(),
		'name': row[3].text_content().strip(),
		'id': int(row[0].cssselect('input')[0].get('value')),
		'unread': u'unread' in row[1].cssselect('img')[0].get('src'),
		'date': row[4].text_content().strip(),
	} for row in tree.cssselect('table.memo_list_table tbody tr')]

	vals = {
		'msgs': msgs,
	}

	return render_template('msgs.html', **vals)

@app.route('/msg/<int:nid>')
def msg(nid):
	res = req_with_sess().get('http://www.nicegame.tv/memo/read_memo/{}/r'.format(nid))
	res.encoding = 'utf-8'

	tree = lxml.html.fromstring(res.text)

	vals = {
		'author': tree.cssselect('th.view_th_col_3')[0].text_content().strip(),
		'body': tree.cssselect('table.memo_view_table tbody td')[0].text_content().strip(),
		'date': tree.cssselect('th.view_th_col_5')[0].text_content().strip(),
	}

	return render_template('msg.html', **vals)
