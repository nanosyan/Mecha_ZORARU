# -*- coding: utf-8 -*-
import os, imp, re, urllib, json, threading, logging, time
import tweepy #pip install tweepy
import yaml #pip install PyYAML

"""利用するディレクトリ"""
current = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = current + '/data'
TMP_DIR = current + '/tmp'
PLUGIN_DIR = current+'/plugins'
"""認証データの読み込み"""
#認証データはaccounts.yamlに記述する
authdb = yaml.load(open(current+'/accounts.yaml').read())

#アカウントの個数を判定して格納する変数
n = (len(authdb)-2)
#使用するアカウントの番号のリスト
AVAILABLE = range(1, int(n)+1)

def Auth(x):
	"""x番目のアカウントを認証する関数"""
	auth = tweepy.OAuthHandler(authdb['CONSUMER_KEY'], authdb['CONSUMER_SECRET'])
	auth.set_access_token(authdb[x]['ACCESS_TOKEN'], authdb[x]['ACCESS_TOKEN_SECRET'])
	api = tweepy.API(auth)
	return api

def Post(text, stream, dm=False, lat=None, longs=None, in_reply_to_status_id=None, filename=None):
	for x in AVAILABLE:
		api = Auth(x)
		try:
			if dm == True:
				api.send_direct_message(screen_name=stream['user']['screen_name'], text=text)
			elif filename == None:
				api.update_status(status=text, in_reply_to_status_id=in_reply_to_status_id, lat=lat, long=longs)
			else:
				api.update_with_media(filename=filename, status=text, in_reply_to_status_id=in_reply_to_status_id, lat=lat, long=longs)
			return True
		except tweepy.TweepError, e:
			code = e[0]
			if code == 186: # 186 = Status is over 140 characters
				Post(u'ツイートが長すぎるため、DMで送信しました。', stream, dm=False, lat=lat, longs=longs, in_reply_to_status_id=in_reply_to_status_id, filename=filename)
				Post(text, stream, dm=True, lat=lat, longs=longs, in_reply_to_status_id=in_reply_to_status_id, filename=filename)
				return True
			elif code in [150, 187, 226]:
				continue
				#150 = only you can send messages to who follows you(DM)
				#187 = Status is a duplicate
				#226 = your request was automated
			elif code == 354:
				return False
				#354 = too long message(DM)
			continue
	else:
		return False

def Initialize():
	plugins = {}
	"""PLUGIN_DIRから拡張機能読み込み"""
	re_plugin = re.compile('[^.].*\.py$')
	for plugin_file in os.listdir(PLUGIN_DIR):
		if re_plugin.match(plugin_file):
			name = plugin_file[:-3]
			ext_info = imp.find_module(name, [PLUGIN_DIR])
			plugin = imp.load_module(name, *ext_info)
			plugins[name] = plugin

	"pluginの種類を分類"
	for i in plugins:
		plugin = plugins[i]
		if plugin.TARGET == 'REPLY':
			reply_plugin.append(plugin)
		elif plugin.TARGET == 'TIMELINE':
			timeline_plugin.append(plugin)
		elif plugin.TARGET == 'EVENT':
			event_plugin.append(plugin)
		elif plugin.TARGET == 'OTHER':
			other_plugin.append(plugin)

	"""利用するアカウントのスクリーンネームのリストを生成"""
	accountset = []
	for x in AVAILABLE:
		api = Auth(x)
		accountset.append(api.me().screen_name)
	global ME #最も主要なアカウントのスクリーンネーム
	ME = accountset[0]
	global set1 #正規表現で使うためのセット
	set1 = '|'.join(accountset)
	global set2 # if inで使うためのセット
	set2 = accountset

def StreamLine(raw):
	"""UserStreamを処理する関数"""
	stream = json.loads(raw)
	try:
		if 'text' in stream or 'direct_message' in stream:
			if 'text' in stream:
				stream['source'] = re.sub('<.*?>','', stream['source'])
			else:
				"""DMもリプライと同じように扱えるように形式を変換"""
				stream['user'] = stream['sender']
				stream['source'] = None
				stream['text'] = '@'+ME+' '+stream['text']
			stream['user']['name'] = stream['user']['name'].replace('@', u'@​')
			if re.match('@(%s)\s' % set1, stream['text']):
				for plugin in reply_plugin:
					ProcessResult(plugin, stream)

		elif 'event' in stream:
			for plugin in event_plugin:
				ProcessResult(plugin, stream)

		else:
			for plugin in other_plugin:
				ProcessResult(plugin, stream)
	except Exception, e:
		print e

def ProcessResult(plugin, stream):
	result = plugin.do(stream)
	if result:
		if isinstance(result, dict):
			if 'text' in result:
				text = result['text']
				if 'dm' in result: dm = result['dm']
				else: dm = False
				if 'lat' in result: lat = result['lat']
				else: lat = None
				if 'longs' in result: longs = result['longs']
				else: longs = None
				if 'in_reply_to_status_id' in result: in_reply_to_status_id = result['in_reply_to_status_id']
				else: in_reply_to_status_id = None
				if 'filename' in result: filename = result['filename']
				else: filename = None
				Post(text, stream, dm, lat, longs, in_reply_to_status_id, filename)
		else:
			logging

class CustomStreamListener(tweepy.StreamListener):
	def on_data(self, raw):
		print raw
		if raw.startswith('{'):
			t = threading.Thread(target=StreamLine, name='StreamLine', args=(raw))
			t.start()
			t.daemon = True
			t.join(20)

class UserStream(tweepy.Stream):
	def user_stream(self):
		self.parameters = {"delimited": "length"}
		self.headers['Content-type'] = "application/x-www-form-urlencoded"
		self.scheme = "https"
		self.host = 'userstream.twitter.com'
		self.url = '/1.1/user.json'
		self.body = urllib.urlencode(self.parameters)
		self.timeout = None
		self._start(False)

class Watch(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		while True:
			print threading.active_count()
			time.sleep(10)

if __name__ == '__main__':
	global reply_plugin
	reply_plugin = []
	global timeline_plugin
	timeline_plugin = []
	global event_plugin
	event_plugin = []
	global other_plugin
	other_plugin = []

	"""一番主要なアカウント(UserStreamに接続するアカウント)の認証"""
	auth_main = tweepy.OAuthHandler(authdb['CONSUMER_KEY'], authdb['CONSUMER_SECRET'])
	auth_main.set_access_token(authdb[1]['ACCESS_TOKEN'], authdb[1]['ACCESS_TOKEN'])
	api_main = tweepy.API(auth_main)

	Initialize()

	Watch().start()

	while True:
		connect = UserStream(auth_main, CustomStreamListener())
		connect.user_stream()
