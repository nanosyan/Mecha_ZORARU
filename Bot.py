# -*- coding: utf-8 -*-
import os, imp, re, urllib, json, threading
import tweepy #pip install tweepy

"""利用するディレクトリ"""
current = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = current + '/data'
TMP_DIR = current + '/tmp'
"""認証データ"""
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

ACCESS_TOKEN1 = ''
ACCESS_TOKEN_SECRET1 = ''
#ACCESS_TOKEN2 = ''
#ACCESS_TOKEN_SECRET2 = ''
#ACCESS_TOKEN3 = ''
#ACCESS_TOKEN_SECRET3 = ''
"""のように以下無限個記述できる"""

n = 0 #アカウントの個数を自動判定
while True:
	n += 1
	try:
		eval('ACCESS_TOKEN'+str(n))
		eval('ACCESS_TOKEN_SECRET'+str(n))
		break
	except:
		continue

AVAILABLE = map(str, range(1, int(n)+1)) #使用するアカウントのリスト

def auth(x):
	"""x番目のアカウントを認証する関数"""
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(eval('ACCESS_TOKEN'+x), eval('ACCESS_TOKEN_SECRET'+x))
	api = tweepy.API(auth)
	return api

def post(text, stream, data, dm=False, lat=None, longs=None, in_reply_to=None, filename=None):
	for x in AVAILABLE:
		if dm == True:
			try:
				eval('api'+x+".send_direct_message(screen_name=stream['user']['screen_name'], text=text)")
				return True
			except tweepy.TweepError, e:
				code = process_error(e)[0]
				if code == [150]: #150 = only you can send messages to who follows you
					continue
				elif code == [226]: #226 = automated
					continue
				elif code == [354]: #354 = too long message
					continue
				continue

		else:
			if 'to' in data:
				"""リプライだったら返信先付加"""
				text = '@'+data['to']+' '+text
			if filename == None:
				try:
					eval('api'+x+'.update_status(status=text, in_reply_to_status_id=tweetid, lat=lat, long=longs)')
					return True
				except tweepy.TweepError, e:
					code = process_error(e)[0]
					if code == 186: # 186 = Status is over 140 characters
						if 'to' in data:
							tmp = u'ツイートが長すぎるため、DMで送信しました。'
							post(tmp, stream, data, dm=dm, lat=lat, longs=longs, in_reply_to=in_reply_to, filename=filename)
						post(text, stream, data, dm=True, lat=lat, longs=longs, in_reply_to=in_reply_to, filename=filename)
						return True
					elif code in 187: #187 = Status is a duplicate
						continue
					elif code == 226: #226 = automated
						continue
					continue

			else:
				try:
					eval('api'+x+'.update_with_media(filename=filename, status=text, in_reply_to_status_id=tweetid, lat=lat, long=longs)')
					break
				except tweepy.TweepError, e:
					code = process_error(e)[0]
					if code == 186: # 186 = Status is over 140 characters
						if 'to' in data:
							tmp = u'ツイートが長すぎるため、DMで送信しました。'
							post(tmp, stream, data, dm=dm, lat=lat, longs=longs, in_reply_to=in_reply_to, filename=filename)
						post(text, stream, data, dm=True, lat=lat, longs=longs, in_reply_to=in_reply_to, filename=filename)
						return True
					elif code in 187: #187 = Status is a duplicate
						continue
					elif code == 226: #226 = automated
						continue

	else:
		return False

def process_error(e): #TweepErrorを処理する関数
	try:
		e = eval(e)[0]
		return [e['code'], e['message']]
	except:
		try:
			e = e[0]
			return [e['code'], e['message']]
		except:
			return [0, e]

def initialize():
	plugins = {}
	plugins_directory = current+'/plugins'

	"""plugins_directoryから拡張機能読み込み"""
	re_plugin = re.compile('[^.].*\.py$')
	for plugin_file in os.listdir(plugins_directory):
		if re_plugin.match(plugin_file):
			name = plugin_file[:-3]
			ext_info = imp.find_module(name, [plugins_directory])
			plugin = imp.load_module(name, *ext_info)
			plugins[name] = plugin

	global reply_plugin
	reply_plugin = []
	"pluginの種類を分類"
	for i in plugins:
		plugin = plugins[i]
		if plugin.TARGET == 'REPLY':
			reply_plugin.append(plugin)

def StreamLine(raw):
	"""UserStreamを処理する関数"""
	stream = json.loads(raw)
	if 'text' in stream:
		data = {"to": "", "name":"", "via": ""} #提供API
		for plugin in reply_plugin:
			result = plugin.do(stream, data)
			if result:
				print result

class UserStream(tweepy.Stream):
	def user_stream(self):
		self.parameters = {"delimited": "length"}
		self.headers['Content-type'] = "application/x-www-form-urlencoded"
		self.scheme = "https"
		self.host = 'userstream.twitter.com'
		self.url = '/1.1/user.json'
		self.body = urllib.urlencode(self.parameters)
		self._start(async=False)

class CustomStreamListener(tweepy.StreamListener):
	def on_data(self, raw):
		if raw.startswith('{'):
			threading.Thread(target=StreamLine, name='stream', args=(raw)).start()

if __name__ == '__main__':
	"""主要なアカウント(UserStreamに接続するアカウント)の認証"""
	auth_main = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth_main.set_access_token(ACCESS_TOKEN1, ACCESS_TOKEN1)
	api_main = tweepy.API(auth_main)

	initialize()

	while True:
		stream = UserStream(auth_main, CustomStreamListener())
		stream.timeout = None
		stream.user_stream()