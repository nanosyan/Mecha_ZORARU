# -*- coding: utf-8 -*-
from Main import *

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

def getTime(status_id):
	created = ((status_id>>22)+1288834974657)/1000.0
	now = time.time()
	return str(now - created)