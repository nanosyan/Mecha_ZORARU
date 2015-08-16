# -*- coding: utf-8 -*-
"""プラグイン情報"""
"""製作者情報 AUTHOR = ?
プラグインの開発者名"""
AUTHOR = ''
"""概要 DESC = ?
プラグインの内容を簡潔に"""
DESC = ''
"""使用法 USAGE = ?
プラグインの使用法を簡潔に"""
USAGE = ''

"""プラグインの適用先を指定 TARGET = ?
REPLY = リプライに対して適用されます
TIMELINE = タイムラインのツイートに対して適用されます
EVENT = UserStreamイベントに対して適用されます
OTHER = これら以外の受け取ったストリームに対して適用されます"""
TARGET = ''

"""実行確率 1/n RATIO = ?
n分の1でプラグインを実行します
必ず実行するには 1 を定義してください"""
RATIO = 1

"""関数名は必ずdoとして 2つの引数を受け取ること"""
def do(stream):
	"""引数について
	stream = UserStreamから受信したJSONの辞書オブジェクト"""


	"""プラグインで実行する処理"""


	"""めかぞらるへの返り値について
	返り値には
	text(必須) = 返信したり投稿したりするツイート本文
	in_reply_to = リプライの場合に返信先のツイートID(Int型)
	filename = 画像をアップロードする場合にファイルへの絶対パス (str型)
	dm = TrueならDMで送信 Falseならツイートで送信
	lat = ツイートに付加する位置情報のうち、経度 int または float
	longs = ツイートに付加する位置情報のうち、緯度 int または float
	これらを辞書のキーとバリューにしてreturnしてください
	任意の返り値で指定がないものは自動的にNone(False)として代入されます"""
	text = None
	in_reply_to = None
	filename = None
	lat = None
	longs = None
	result = {"text": text, "in_reply_to": in_reply_to, "filename": filename, "dm": False, "lat": lat, "longs": longs}
	return result