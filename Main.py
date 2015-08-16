# -*- coding: utf-8 -*-
from Function import Auth, Post, getTime
import os, imp, re, urllib, json, threading, logging, datetime, time
import tweepy #pip install tweepy
import yaml #pip install PyYAML

"""利用するパス"""
current = os.path.dirname(os.path.abspath(__file__))
current = '/my/Bot/GitHub'
WORK_DIR = current + '/data'
TMP_DIR = current + '/tmp'
PLUGIN_DIR = current+'/plugins'
LOG_PATH = current + '/logs/' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.txt'
"""認証データの読み込み"""
#認証データはaccounts.yamlに記述する
authdb = yaml.load(open(current+'/accounts.yaml').read())
#アカウントの個数を判定して格納する変数
n = (len(authdb)-2)
#使用するアカウントの番号のリスト
AVAILABLE = range(1, int(n)+1)

"""初期化する関数: コマンドでプラグインを再読み込みする際にも使用"""
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
		if plugin.TARGET == 'REPLY': #リプライに適用
			reply_plugin.append(plugin)
		elif plugin.TARGET == 'TIMELINE': #タイムライン全体に適用
			timeline_plugin.append(plugin)
		elif plugin.TARGET == 'EVENT': #イベントに適用
			event_plugin.append(plugin)
		elif plugin.TARGET == 'OTHER': #その他のストリームに適用
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
			print stream
			if 'text' in stream:
				stream['source'] = re.sub('<.*?>','', stream['source'])
			else:
				"""DMもリプライと同じように扱えるように形式を変換"""
				stream['user'] = stream['sender']
				stream['source'] = None
				stream['text'] = '@'+ME+' '+stream['text']
			stream['user']['name'] = stream['user']['name'].replace('@', u'@​')
			if re.match('@(%s)\s' % set1, stream['text'], re.IGNORECASE):
				for plugin in reply_plugin:
					print getTime(stream['id'])
					ExecutePlugin(plugin, stream)

		elif 'event' in stream:
			for plugin in event_plugin:
				ExecutePlugin(plugin, stream)

		else:
			for plugin in other_plugin:
				ExecutePlugin(plugin, stream)

	except Exception, e:
		print e

def ExecutePlugin(plugin, stream):
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

class CustomStreamListener(tweepy.StreamListener):
	def on_data(self, raw):
		if raw.startswith('{'):
			t = threading.Thread(target=StreamLine, name='StreamLine', args=(raw, ))
			t.start()
			t.join(20) #スレッドのタイムアウト
			if t.isAlive():
				t.__stop()
				logging.warning(u'スレッドがタイムアウトしました: %s' % raw)
			return True
		else:
			logging.warning(u'解析不能なUserStreamデータを受信しました: %s' % raw)
			return False
	def on_error(self, status_code):
		print status_code

class UserStream(tweepy.Stream):
	def user_stream(self):
		self.parameters = {"delimited": "length", "replies": "all", "filter_level": "none"}
		self.headers['Content-type'] = "application/x-www-form-urlencoded"
		self.scheme = "https"
		self.host = 'userstream.twitter.com'
		self.url = '/1.1/user.json'
		self.body = urllib.urlencode(self.parameters)
		self.timeout = None
		self._start(False)

if __name__ == '__main__':
	"""ロガーを準備"""
	logging.basicConfig(filename=LOG_PATH, format='%(asctime)s [%(levelname)s]\n%(message)s', datefmt='%Y/%m/%d %H:%M:%S')

	"""プラグインを格納する辞書を定義"""
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
	auth_main.set_access_token(authdb[1]['ACCESS_TOKEN'], authdb[1]['ACCESS_TOKEN_SECRET'])
	api_main = tweepy.API(auth_main)

	"""初期化"""
	Initialize()

	"""UserStreamに接続"""
	while True:
		connect = UserStream(auth_main, CustomStreamListener())
		connect.user_stream()
