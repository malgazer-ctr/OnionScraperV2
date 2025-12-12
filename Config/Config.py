from __future__ import annotations

import os
from OnionScraperLib import FileOperate as fo
from tkinter.tix import COLUMN

g_deletingFromBox = False
# -------------------------------------------------------------------------------------------
# デバッグ用
# -------------------------------------------------------------------------------------------
headless_options = 0

# -------------------------------------------------------------------------------------------
# ヘッドレス設定を判定する用
# -------------------------------------------------------------------------------------------
isheadless = True
# -------------------------------------------------------------------------------------------
#　レポート系メールのインターバル
# -------------------------------------------------------------------------------------------
# レポートメールを送るインターバル3時間
REPORTMAIL_INTERVAL = 10800
# REPORTMAIL_INTERVAL = 3600
# レポートメールを送るインターバル1時間
REPORTMAIL_INTERVAL_YUICHI = 7200
# REPORTMAIL_INTERVAL = 60
# レポートメール用のログ保存インターバル
# REPORTMAIL_LOG_INTERVAL = 60
REPORTMAIL_LOG_INTERVAL = 600

# -------------------------------------------------------------------------------------------
#　サブプロセス(HTML取得するプロセス)の戻り値
# -------------------------------------------------------------------------------------------
# 何らかのエラーのためHTML取得処理に到達できませんでした
# サイトへの接続エラーなどのExceptionもこのエラー
SUB_RETURNCODE_ERR = 0
# なんらかのHTMLは取得できた
SUB_RETURNCODE_GETHTML = 0x00000001
# TargetURL.jsonで指定されたオブジェクト検知(HTML取得成功)
SUB_RETURNCODE_GETHTML_FINDOBJECT = 0x00000002
# TargetURL.jsonで指定されたオブジェクト検知失敗(HTML取得？？)
# TargetURL.jsonでオブジェクト未指定(HTML取得？？)
SUB_RETURNCODE_GETHTML_NOTFINDOBJECT = 0x00000004
# HTML取得処理には入ったけど取得できなかった
SUB_RETURNCODE_GETHTML_FAILED = 0x00000008
# 個別対応での情報取得成功
SUB_RETURNCODE_GETHTML_INDIVISUAL_SUCCESS = 0x00000010
# 個別対応での情報取得失敗
SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED = 0x00000020
# HTML取得できたけど完全無視リストにひっかかった
SUB_RETURNCODE_GETHTML_IGNORE = 0x00000040
# 差分あり
SUB_RETURNCODE_DIFF = 0x00001000
# 差分あり(個別対応)
SUB_RETURNCODE_DIFF_INDIVISUAL = 0x00002000
# 差分なし
SUB_RETURNCODE_NODIFF = 0x00004000
# 差分なし(個別対応)
SUB_RETURNCODE_NODIFF_INDIVISUAL = 0x00008000


# スクリーンショットを何世代残すか
GEN_STOCKSCREENSHOT = 15

# -------------------------------------------------------------------------------------------
# 全般
# -------------------------------------------------------------------------------------------
# FireFoxのドライバ使用しているか
g_useFFDriver = False
# ベースのパス
PATH_CURRNET = r'E:\MonitorSystem\Source\OnionScraperV2'
# マルチプロセス用
PATH_SUBMOD = os.path.join(PATH_CURRNET, 'MonitorSub.py')
# pythonexe = r'C:\Users\test\AppData\Local\Programs\Python\Python39\python.exe'
PATH_CONFIG = os.path.join(PATH_CURRNET,r'Config')

# -------------------------------------------------------------------------------------------
# TOR関連
# -------------------------------------------------------------------------------------------
PATH_TOR_DATA = r'C:\ProgramData\Tor\data'
# マルチプロセス化された各Torプロセスが使う設定ファイル。プログラム上で動的生成される
PATH_TOR_DATA_TOR = os.path.join(PATH_CURRNET, r'Data\torConfig\tor')
# PATH_TORRC_DIR = r'C:\ProgramData\Tor\multi_torrc'
# V2では場所変えてみる
PATH_TORRC_DIR = os.path.join(PATH_CURRNET, r'Config\torConfig\multi_torrc')
PATH_FIREFOX = r'C:\Program Files\Mozilla Firefox\firefox.exe'
PATH_BRAVE = r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe'
PATH_TOREXE = os.path.join(PATH_CURRNET,r'Tor Browser\Browser\TorBrowser\Tor\tor.exe')
# https://chromedriver.chromium.org/downloads
PATH_CHROMEDRIVER = r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'

# -------------------------------------------------------------------------------------------
# ログファイル
# -------------------------------------------------------------------------------------------
PATH_LOG_DIR = os.path.join(PATH_CURRNET, r'Data\Log')
PATH_LOGMULTI_DIR = os.path.join(PATH_LOG_DIR, r'\multi')
PATH_ALLLOG_FILE = os.path.join(PATH_LOG_DIR, r'Crawl_All.log')
PATH_ALLLOG_EXCEPTION_FILE = os.path.join(PATH_LOG_DIR, r'Crawl_All_Exception.log')
PATH_BENCHMARK_FILE = os.path.join(PATH_LOG_DIR, r'Benchmark.log')
PATH_ACCESSLOG_FILE = os.path.join(PATH_LOG_DIR, r'AccessLog.log')
FILE_PATH_ACCESSLOG_GENERAL = os.path.join(PATH_CURRNET, r'Data\Log\AccessLogGeneral.log')
PATH_LOG2_ROOT = os.path.join(PATH_CURRNET, r'Data\Log2')
LOG2_ENABLED = True
LOG2_RETENTION_DAYS = 7

# -------------------------------------------------------------------------------------------
# 排他制御用のロックファイル
# -------------------------------------------------------------------------------------------
# AccessLog.logの排他制御用
PATH_ACCESSLOGLOCK_FILE = os.path.join(PATH_LOG_DIR, r'AccessLogLock')
# TargetURL系ファイル更新時のロック
PATH_TARGETURLLOCK_FILE = os.path.join(PATH_LOG_DIR, r'TargetURLFileLock')
# TargetURLReport.json更新用の排他制御用
PATH_JSON_REPORTLOCK_FILE = os.path.join(PATH_CURRNET, r'Config\TargetURLReportLock')

# -------------------------------------------------------------------------------------------
# 結果ファイル関連
# -------------------------------------------------------------------------------------------
PATH_DATA = os.path.join(PATH_CURRNET,r'Data')
PATH_HTMLDIFF_DATA = os.path.join(PATH_DATA,r'HTMLdiff_Data')
PATH_OUTERHTML_TEXT = os.path.join(PATH_HTMLDIFF_DATA,r'OuterHtmlText')
PATH_DIFFHTML_DIR = os.path.join(PATH_HTMLDIFF_DATA,r'DiffHtml')
PATH_DIFFPDF_DIR = os.path.join(PATH_HTMLDIFF_DATA,r'DiffPDF')
PATH_SCREENSHOT_DIR = os.path.join(PATH_HTMLDIFF_DATA,r'ScreenShot')
PATH_CAPTCHAIMG_DIR = os.path.join(PATH_HTMLDIFF_DATA,r'Captcha')
PATH_SCREENSHOT_DIFF_DIR = os.path.join(PATH_HTMLDIFF_DATA,r'ScreenShot\DiffScreenShot')
PATH_NOTIFIED_IMPORANT_INFO = os.path.join(PATH_HTMLDIFF_DATA,r'NotifiedImportantInfo')
# PATH_HTMLDIFF_RESULTS = os.path.join(PATH_CURRNET,r'Data\HTMLdiff_ResultFiles')

# -------------------------------------------------------------------------------------------
# 画像テンプレートマッチ用
# -------------------------------------------------------------------------------------------
PATH_IMAGETEMPLATE_DIR = r'E:\MonitorSystem\Source\OnionScraperV2\Config\TemplateImage'

# -------------------------------------------------------------------------------------------
# 通知メール用のHTMLテンプレート
# -------------------------------------------------------------------------------------------
DATA_TEMPLATE_HTML = fo.Func_ReadFile(os.path.join(PATH_CONFIG,'NotificationMailTemplate.html'))
DATA_TEMPLATE_DIFFTABLEHEADER = fo.Func_ReadFile(os.path.join(PATH_CONFIG,'DiffTableHeader.html'))
DATA_TEMPLATE_REPORTHTML = fo.Func_ReadFile(os.path.join(PATH_CONFIG,'AccessLogReport.html'))
DATA_TEMPLATE_DIFFINFO = fo.Func_ReadFile(os.path.join(PATH_CONFIG,'DiffInfoTable.html'))
DATA_TEMPLATE_DIFFINFO_DEL = fo.Func_ReadFile(os.path.join(PATH_CONFIG,'DiffInfoTable_Del.html'))

# -------------------------------------------------------------------------------------------
# 監視対象URL系の情報
# -------------------------------------------------------------------------------------------
TARGET_URL_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\TargetURL_new.csv')
TARGET_URL_JSON_PATH = os.path.join(PATH_CURRNET,r'Config\TargetURL.json')
# 実行中更新し続けるログ的な。本プロセス全体が終了するとき必ずTARGET_URL_JSON_PATHに置き換える
TARGET_URL_JSON_REPORT_PATH = os.path.join(PATH_CURRNET,r'Config\TargetURLReport.json')
TARGET_URL_SECONDARYLIST_PATH = os.path.join(PATH_CURRNET,r'Config\TargetURL_secondary.csv')
TARGET_URL_LISTSUB_DIR = os.path.join(PATH_CURRNET,r'Config\TargetURLSub')

# Watcher用に各グループがアクティブとして実行されているかどうかなどの情報を渡す用
WATCHER_JSON_PATH = os.path.join(PATH_CURRNET,r'Config\watcher.json')

# TargetURLSubに作成される各CSVのカラム
TARGET_URL_LIST_GROUP_NAME = 0
TARGET_URL_LIST_GROUP_URL = 1
TARGET_URL_LIST_ACCESS_STATUS = 2
TARGET_URL_LIST_GROUP_STATUS = 3
TARGET_URL_LIST_GROUP_CATEGORY = 4

# スクリーンショットエラー時の代替画像
PATH_ERR_SCREENSHOT = os.path.join(PATH_CURRNET,r'Config\ScreenShotError.jpg')
# 初回取得時の前回用スクリーンショット画像
PATH_FIRSTTIME_SCREENSHOT = os.path.join(PATH_CURRNET,r'Config\ScreenShotFirstTime.jpg')

# Htmlで取得時この文言が入っていたら取得できてない扱いにする
# PATH_IGNOREWORD_LIST = os.path.join(PATH_CURRNET,r'Config\IgnoreWord.csv')
PATH_IGNOREWORD_LIST = os.path.join(PATH_CURRNET,r'Config\IgnoreWord.json')

# Html差分で出ても無視するリスト
PATH_EXCLUDEDIFF_LIST = os.path.join(PATH_CURRNET,r'Config\ExcludeDiffList.json')

# 重要ワード
IMPORTANTWORD_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\ImportantWord.csv')

# 重要ワード(アップデート)
# このリストに含まれる被害組織名の情報を検知した場合、過去検知済みでも検知メールを送り、重要フラグを立てる
IMPORTANTWORD_UPDATE_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\ImportantWord_update.csv')

# 重要ワード特殊対応
# 特別な相手に特別な件名で送信する
# これ系増えるようならハードコーディングではなく外だしでメアドとかとセットにする
IMPORTANTWORD_MBK_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\ImportantWord_MBK.csv')
IMPORTANTWORD_YAMAHA_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\ImportantWord_YAMAHA.csv')
IMPORTANTWORD_YAMAHAMOTORS_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\ImportantWord_YAMAHA_MOTORS.csv')
IMPORTANTWORD_NIDEC_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\ImportantWord_NIDEC.csv')
# 日本語チェッカーで無視するワードリスト
# このリストに含まれる被害組織名の情報を検知した場合、過去検知済みでも検知メールを送り、重要フラグを立てる
IGNOREWORD_JAPANESELIKE_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\IgnoreWord_JapaneseLike.csv')

# "audi" → "Saudi Arabia"が検知されてしまうような場合に対応
# 重要ワードの前後８文字を含む文字列にこのファイルに含まれる単語が存在したら重要扱いしない
IGNOREWORD_IFINCLUDED_LIST_PATH = os.path.join(PATH_CURRNET,r'Config\IgnoreWord_Included.csv')


# -------------------------------------------------------------------------------------------
# 各サイトのアクセスログ用の構造体
# -------------------------------------------------------------------------------------------
# 検知メールに関係なくアクセスログメールを送るインターバル3時間
ACCESSLOG_MAIL_INTERVAL = 43200
ACCESSLOG_ON_REPORTMAIL_MAX = 100
# 検知メールに掲載するアクセスログの最大件数
ACCESSLOG_ON_DETECTMAIL_MAX = 10
ACCESSDATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'

accessLog = \
{
    'groupName':'',
    'getHTMLStatus':'-',
    'htmlSize':0,
    'accessStartTime':'-',
    'accessEndTime':'-',
    'errText':''
}
accessLogStruct = \
{
    # 'general':{
    #     # CIGメンバーにメールで通知した時間
    #     # 検知メールでは指定された件数をメールで送るが、それと関係なく
    #     # ACCESSLOG_MAIL_INTERVAL で指定された時間ごとにメールを送りたいので送るごとに記録しておく
    #     'sentMailTime':''
    # },
    'log':[]
}

# -------------------------------------------------------------------------------------------
# メールの送信先
# -------------------------------------------------------------------------------------------
# SNEDTO_DIFF_CIG = ['y.yasuda@mbsd.jp']
# SNEDTO_DIFF = ['y.yasuda@mbsd.jp']
# SNEDTO_DIFF_MBK = ['y.yasuda@mbsd.jp']
# SNEDTO_DIFF_YAMAHA = ['y.yasuda@mbsd.jp']
# SNEDTO_DIFF_YAMAHAMOTORS = ['y.yasuda@mbsd.jp']
# SENDTO_REPORT = ['y.yasuda@mbsd.jp']
# ------------------------------------------------------------------------------------------------------------
# SNEDTO_DIFF_CIG = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp']
# SNEDTO_DIFF = ['']
# SNEDTO_DIFF_MBK = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp']
# SNEDTO_DIFF_YAMAHA = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp']
# SENDTO_REPORT = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp']
# ------------------------------------------------------------------------------------------------------------
SNEDTO_DIFF_CIG_PLUS = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp', 'm.kasuya@mbsd.jp', 's.urata@mbsd.jp', 'm.sekihara@d.mbsd.jp']
# SNEDTO_DIFF_CIG = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp', 'm.kasuya@mbsd.jp']

# SNEDTO_DIFF = [
#     'daisuke.yasuda.tj@d.mbsd.jp',
#     't.tamura@d.mbsd.jp',
#     'ke.nakayama@mbsd.jp',
#     # 'yuzo.goda.od@d.mbsd.jp', #退社済 2024/1/19
    
#     # 以下メディア
#     'taroukimura1969@gmail.com',
#     'kurosesjk29@gmail.com',
#     # 'akiyama.t-hq@nhk.or.jp',
#     'shimada.t-go@nhk.or.jp',
#     'fukuda.y-jy@nhk.or.jp',
#     'sumi.ryota@kyodonews.jp',
#     'akinobu.iwasawa@nex.nikkei.com'
# ]

SNEDTO_DIFF = [
    'daisuke.yasuda.tj@d.mbsd.jp',
    't.tamura@d.mbsd.jp',
    'ke.nakayama@mbsd.jp',
    
    # NHK
    # 'fukuda.y-jy@nhk.or.jp',
    'nishimura.s-je@nhk.or.jp',
    'kinugawa.c-du@nhk.or.jp',
    # 'kurosesjk29@gmail.com', 2025/10/14 担当が変わったので除外

    # 共同通信
    'sumi.ryota@kyodonews.jp',

    # 日経
    'akinobu.iwasawa@nex.nikkei.com'
]

SNEDTO_DIFF_MBK = [
'y.yasuda@mbsd.jp',
'takashi.yoshikawa.el@d.mbsd.jp',
'm.fukuda@mbsd.jp',
'm.kasuya@mbsd.jp',
's.urata@mbsd.jp',
'm.sekihara@d.mbsd.jp',
'mc2-cig-ti@mbsd.jp'

# 'i.murakami@mbsd.jp',
# 'k.uehara@mbsd.jp',
# 'hiroshi.kojima.xy@mbsd.jp',
# 'j.ito@d.mbsd.jp',
# 'ke.nakayama@mbsd.jp',
# # 'kei.sugawara.yf@d.mbsd.jp',
# # 'm.nakazawa@mbsd.jp',退社？送れなくなった
# 's.matsuura@mbsd.jp',
# 's.nakajima@d.mbsd.jp',
# 'm.shinjo@d.mbsd.jp',
# 'n.yanai@d.mbsd.jp',
# 't.nakajima@mbsd.jp',
# 't.tamura@d.mbsd.jp',
# 'yo.hayashi@mbsd.jp',
# 'yuzo.goda.od@d.mbsd.jp',
# 'h.ono@mbsd.jp',
# 'y.kamibayashi@mbsd.jp',
# 'm.akiyama@mbsd.jp'
]

SNEDTO_DIFF_YAMAHA = [
'y.yasuda@mbsd.jp',
'takashi.yoshikawa.el@d.mbsd.jp',
'm.fukuda@mbsd.jp',
'm.kasuya@mbsd.jp',
's.urata@mbsd.jp',
'm.sekihara@d.mbsd.jp',
'yamaha-ti@mbsd.jp'
]

SNEDTO_DIFF_YAMAHAMOTORS = [
'y.yasuda@mbsd.jp',
'takashi.yoshikawa.el@d.mbsd.jp',
'm.fukuda@mbsd.jp',
'm.kasuya@mbsd.jp',
's.urata@mbsd.jp',
'm.sekihara@d.mbsd.jp',
'ymc-ti@mbsd.jp'
]

# 2024/6/3 Nidecが被害にあったとの内部情報から追加
SNEDTO_DIFF_NIDEC = [
    'ds-nid@mbsd.jp',
    # 's.nakajima@d.mbsd.jp',
    # 'kazumasa.oohashi.es@d.mbsd.jp'
]

# 2024/6/3 Nidecが被害にあったとの内部情報から追加
# SNEDTO_DIFF_METRICON = [
#     'y.yasuda@mbsd.jp',
#     # 'raine.shirai.rz@d.mbsd.jp'
# ]
# ------------------------------------------------------------------------------------------------------------
SENDTO_REPORT = ['y.yasuda@mbsd.jp','takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp', 'm.kasuya@mbsd.jp', 's.urata@mbsd.jp']
SENDTO_REPORT_YUICHI = ['y.yasuda@mbsd.jp']

# -------------------------------------------------------------------------------------------
# 重要ワードを送る先と重要ワードリストのセットなど
# -------------------------------------------------------------------------------------------
# Debug用
# cfgDic = \
# {
#     'mailConfig':{
#         # CIG向けに通知したい
#         'cig':{
#             'sendTo':SENDTO_REPORT_YUICHI,
#             'importantWordList':IMPORTANTWORD_LIST_PATH,
#             # 日本語らしきものを自動識別する
#             'autoCheckJapanese':True,
#             # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
#             'setImportantFlagForce':False,
#             # 以下はIsImportantInfo関数の結果で書き換え
#             'hasImportantInfo':False,
#             'importantWords':'',
#             'importantWordsList':[]
#         }
#     }
# }
# このDictionaryはcopyして使われるので動的に書き換え前提
cfgDic = \
{
    'mailConfig':{
        # CIG向けに通知したい
        'cig':{
            'sendTo':SNEDTO_DIFF_CIG_PLUS,
            # 'sendTo':SNEDTO_DIFF_CIG,
            'importantWordList':IMPORTANTWORD_LIST_PATH,
            # 日本語らしきものを自動識別する
            'autoCheckJapanese':True,
            # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
            'setImportantFlagForce':False,
            # 以下はIsImportantInfo関数の結果で書き換え
            'hasImportantInfo':False,
            'importantWords':'',
            'importantWordsList':[]
        },
        # メディア向けに通知したい
        'regular':{
            'sendTo':SNEDTO_DIFF,
            # 'sendTo':SNEDTO_DIFF_CIG,
            'importantWordList':IMPORTANTWORD_LIST_PATH,
            # 日本語らしきものを自動識別する
            'autoCheckJapanese':True,
            # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
            'setImportantFlagForce':False,
            # 以下はIsImportantInfo関数の結果で書き換え
            'hasImportantInfo':False,
            'importantWords':'',
            'importantWordsList':[]
        },
        # CIG、MBK関連担当者向けに通知したい
        'mbk':{
            'sendTo':SNEDTO_DIFF_MBK,
            # 'sendTo':SNEDTO_DIFF_CIG,
            'importantWordList':IMPORTANTWORD_MBK_LIST_PATH,
            # 日本語らしきものを自動識別する
            'autoCheckJapanese':False,
            # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
            'setImportantFlagForce':True,
            # メール件名にオプションで追加したい文字列
            'extraSubjectStr':'【重要組織情報の可能性有(M)】',
            # 以下はIsImportantInfo関数の結果で書き換え
            'hasImportantInfo':False,
            'importantWords':'',
            'importantWordsList':[]
        },
        # CIG、YAMAHA関連担当者向けに通知したい
        # 現状はCIGメンバーのみ
        'yamaha':{
            # 検知したい組織ごとに変える必要がある送信先とワードリスト
            'sendTo':SNEDTO_DIFF_YAMAHA,
            # 'sendTo':SNEDTO_DIFF_CIG,
            'importantWordList':IMPORTANTWORD_YAMAHA_LIST_PATH,
            # 日本語らしきものを自動識別する
            'autoCheckJapanese':False,
            # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
            'setImportantFlagForce':True,
            # メール件名にオプションで追加したい文字列
            'extraSubjectStr':'【重要組織情報の可能性有(Y)】',
            # 以下はIsImportantInfo関数の結果で書き換え
            'hasImportantInfo':False,
            'importantWords':'',
            'importantWordsList':[]
        },
        # CIG、YAMAHA発動機関連担当者向けに通知したい
        # 現状はCIGメンバーのみ
        'yamaha_motors':{
            # 検知したい組織ごとに変える必要がある送信先とワードリスト
            'sendTo':SNEDTO_DIFF_YAMAHAMOTORS,
            # 'sendTo':SNEDTO_DIFF_CIG,
            'importantWordList':IMPORTANTWORD_YAMAHAMOTORS_LIST_PATH,
            # 日本語らしきものを自動識別する
            'autoCheckJapanese':False,
            # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
            'setImportantFlagForce':True,
            # メール件名にオプションで追加したい文字列
            'extraSubjectStr':'【重要組織情報の可能性有(YM)】',
            # 以下はIsImportantInfo関数の結果で書き換え
            'hasImportantInfo':False,
            'importantWords':'',
            'importantWordsList':[]
        },
        # Nidec
        'Nidec':{
            # 検知したい組織ごとに変える必要がある送信先とワードリスト
            'sendTo':SNEDTO_DIFF_NIDEC,
            # 'sendTo':SNEDTO_DIFF_CIG,
            'importantWordList':IMPORTANTWORD_NIDEC_LIST_PATH,
            # 日本語らしきものを自動識別する
            'autoCheckJapanese':False,
            # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
            'setImportantFlagForce':True,
            # メール件名にオプションで追加したい文字列
            'extraSubjectStr':'【重要組織情報の可能性有(NI)】',
            # 以下はIsImportantInfo関数の結果で書き換え
            'hasImportantInfo':False,
            'importantWords':'',
            'importantWordsList':[]
        },
        # Metricon
        # 'Metricon':{
        #     # 検知したい組織ごとに変える必要がある送信先とワードリスト
        #     'sendTo':SNEDTO_DIFF_METRICON,
        #     # 'sendTo':SNEDTO_DIFF_CIG,
        #     'importantWordList':IMPORTANTWORD_NIDEC_LIST_PATH,
        #     # 日本語らしきものを自動識別する
        #     'autoCheckJapanese':False,
        #     # 通知済みの重要単語を再度通知するかフラグ。Trueなら強制通知
        #     'setImportantFlagForce':True,
        #     # メール件名にオプションで追加したい文字列
        #     'extraSubjectStr':'【重要組織情報の可能性有(ME)】',
        #     # 以下はIsImportantInfo関数の結果で書き換え
        #     'hasImportantInfo':False,
        #     'importantWords':'',
        #     'importantWordsList':[]
        # }
    }            
}

# -------------------------------------------------------------------------------------------
# 設定周りにかかわる関数
# -------------------------------------------------------------------------------------------
def getTargetLeakSite(path = TARGET_URL_JSON_PATH):
    ret = {}

    dict_ = fo.Func_ReadJson2Dict(path)
    ret = dict(filter(lambda x: ('exclude' in x[1]) == False or x[1]['exclude'] == False, dict_.items()))

    return ret

# -------------------------------------------------------------------------------------------
# 親プロセスと子プロセスで共通のファイルを読み書きするので、各攻撃グループごとにロックを格納
# -------------------------------------------------------------------------------------------
g_dicAccessLogLock = {}
# BOXの共有最上層の親フォルダのIDとか
g_logMainFolderId = ''
g_shareFolderLink = ''
g_BoxFolderIds = {}
