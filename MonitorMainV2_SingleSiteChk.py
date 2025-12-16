import html
import os
import random
import time
from datetime import datetime
import threading
import requests
import csv
import sys
import subprocess
from subprocess import PIPE
import ctypes
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
from stem import SocketError
from multiprocessing import Lock
import socket
import tempfile
import psutil
from concurrent.futures import ThreadPoolExecutor
import hashlib
from selenium.webdriver.common.by import By

import json
import urllib.parse
from Config import Config as cf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import SetupBrowser as sb
from OnionScraperLib import GetHTML as gh

# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# 監視対象
# TARGET_GROUPLIST = [
#     'LunaLock',
#     # 'Cephalus',
#     # 'Warlock',
#     # 'BQTLOCK',
#     # 'SatanLock',
#     # 'CACTUS',
#     # 'DireWolf',
# ]

TARGET_GROUPLIST_JSON = [
    # {
    #     "groupName":"LunaLock"
    # },
    # {
    #     "groupName":"BLACKSHRANTAC"
    # },
    {
        "groupName":"Dark Shinigamis"
    },  
    {
        "groupName":"CRY0"
    },    
    {
        "groupName":"FulcrumSec"
    },
    # {
    #     "groupName":"TENGU"
    # },
    {
        "groupName":"AKIRA",
        "useRequestMethod":True,
        "AdditionalURL":"/s",
        "Headers":{
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://akiral2iz6a7qgd3ayp3l6yub7xx2uep76idk3u2kollpj5z3z636bad.onion/",
            "X-CSRF-Token": "pEAtpAurXy7iGcwxxfRIEdwyMPl9u00lBYxWUIfK08HMd3X32yYzm4G9zbv9ENtMKxVMtT8zH1pLVWGTjDHAZA",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-GPC": "1",
            "Connection": "keep-alive",
            "Cookie": "_app_session=Oj8CYJSnRMtYLA/1B97MyqyPvTmm7wwyQjqb8YNVAoACWyatckxpSa1BfH5VV35ziKUBqT8RRZAfwlkGT3/4DYQGmGPvgmdxWKXbAL7G4NNl4voun1fvvW0AwapIGagdOjZ+GCXzGnxm9U3lbN85WzEZT6lhbN+UYdSxrrShcv7BgYpOzlO0eIXdt216OmTYdLjmbf0sHZv+QKiiYWuENZe7yBzKUCR1860OP1fppiR7OLwOO7zFeAGFVm9cqA864nVhPHbwYy/09z7rpssWWQEPh/Q==--ZTzwAWcq/DuxWbg5--AwjT9AxAHHNoE+fE3y0izw==",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0"
        },
        "RequestData":{
            'q': 'Genmark'
        },
        "Note": "leaksキーに値が入ったらリーク開始の可能性"
    }
]

# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------


DEBUG_MODE = True  # デバッグモード


RESULT_STOCK_DIR = r'E:\MonitorSystem\Source\OnionScraperV2\Data\SingleSiteChecker'
OUTPUT_FILE = 'output.csv'  # 出力ファイル名
HEADLESS_MODE = False  # ヘッドレスモード
MAX_THREADS = 5  # 最大スレッド数
MAX_RETRIES = 5  # 最大リトライ回数
lock = Lock()  # ファイルアクセスの排他制御用ロック
TOR_CONTROL_PORT = 9052  # Tor制御ポート番号
TOR_SOCKS_PORT = 9050  # Tor SOCKSポート番号
TOR_PATH = r"C:\Users\malga\Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe"
# https://github.com/mozilla/geckodriver/releases
GECKO_DRIVER_PATH = r"E:\MonitorSystem\Source\OnionScraperV2\WebDriver\geckodriver_v036.exe"
FIREFOX_BINARY_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
# ACCESSLOG_PATH = 'accessLog.json'
# 保管するHTMLやスクショの最大数
MAX_LOCAL_FILES = 20

def set_no_proxy():
    # Windowsでは環境変数名は大文字小文字を区別しませんが、
    # 必要に応じて 'NO_PROXY' としてもOKです。
    os.environ['no_proxy'] = 'localhost,127.0.0.1'

    no_proxy = os.environ.get('no_proxy', os.environ.get('NO_PROXY'))
    print("no_proxy is set to:", no_proxy)

def unset_no_proxy():
    # 環境変数を削除（存在しない場合は何もしない）
    os.environ.pop('no_proxy', None)
    print("no_proxy has been removed.")

# エラーロギング関数
def log_exception(e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(f"Exception in {fname}, line {exc_tb.tb_lineno}: {e}")

# -------------------------------------------------------------------------------------------------
# TORの起動とブラウザのセットアップ、クリア処理関数
# -------------------------------------------------------------------------------------------------
# 一時的なtorrcファイルを作成
def create_torrc(socks_port):
    torConfFile = ''
    try:
        temp_dir = tempfile.mkdtemp()
        torConfFile = os.path.join(temp_dir, f'torrc_{socks_port}')
        with open(torConfFile, 'w') as torrc_file:
            torrc_file.write(f"ControlPort {TOR_CONTROL_PORT}\n")
            torrc_file.write("CookieAuthentication 1\n")
            torrc_file.write(f"SOCKSPort {socks_port}\n")
    except Exception as e:
        log_exception(e)

    return torConfFile

# Torをバックグラウンドで起動する
def start_tor(socks_port):
    try:
        torProc = None
        if not os.path.exists(TOR_PATH):
            raise FileNotFoundError(f"Tor executable not found at {TOR_PATH}. Please install Tor or provide the correct path.")
        torConfFile = create_torrc(socks_port)
        torProc = subprocess.Popen([TOR_PATH, '-f', torConfFile])
        wait_for_tor_startup()
    except Exception as e:
        log_exception(e)

    return torProc, torConfFile

# Torが完全に起動したか確認する
def wait_for_tor_startup():
    try:
        start_time = time.time()
        timeout = 60  # 最大待機時間 60秒
        while True:
            if time.time() - start_time > timeout:
                ctypes.windll.user32.MessageBoxW(0, "Tor did not start within the expected time frame.", "Error", 1)
                raise TimeoutError("Tor did not start within the expected time frame.")
            if is_tor_running():
                print("Tor is fully started.")
                break
            time.sleep(5)  # 5秒待機して再確認
    except Exception as e:
        log_exception(e)

# Torプロセスが実行中かどうかを確認
def is_tor_running():
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'tor.exe' or proc.info['name'] == 'tor':
                return True
        return False
    except Exception as e:
        log_exception(e)
        return False

# Torのポートをリセットする
def reset_tor_port():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            time.sleep(10)  # 新しいIPが有効になるまで少し待機
    except SocketError as e:
        log_exception(f"Socket error: {e}. Make sure Tor is running and the control port is accessible.")
    except Exception as e:
        log_exception(e)

def killService(service):
    try:
        # Service オブジェクトから親プロセスの PID を取得
        pid = service.process.pid
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        # すでにプロセスが存在しない場合は何もしない
        return

    # 親プロセスの子プロセスを再帰的に取得
    children = parent.children(recursive=True)

    # 子プロセスをすべて強制終了
    for child in children:
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass

    # 親プロセスを強制終了
    try:
        parent.kill()
    except psutil.NoSuchProcess:
        pass

    # 全てのプロセスが終了するまで少し待つ
    gone, alive = psutil.wait_procs([parent] + children, timeout=5)
    if alive:
        # 万一終了していないプロセスがあれば再度 kill する
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass

def find_unused_port(start_port=9500, end_port=9900):
    """
    指定した範囲内で未使用のポート番号をランダムに取得する
    :param start_port: チェック開始のポート番号（含む）
    :param end_port: チェック終了のポート番号（含む）
    :return: 未使用のポート番号
    :raises RuntimeError: 指定範囲内に未使用のポートが見つからなかった場合
    """
    # 指定範囲のポート番号リストを作成し、ランダム順に並び替え
    port_range = list(range(start_port, end_port + 1))
    random.shuffle(port_range)

    for port in port_range:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # オプション: すぐに再利用できるようにする（必須ではない）
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                # 空のホスト名 ("") を使ってバインドを試みる
                sock.bind(("", port))
                # バインドに成功したら、そのポートは未使用
                return port
            except OSError:
                # バインド失敗ならそのポートは使用中なので、次のポートをチェック
                continue

    # 指定範囲内に未使用のポートが見つからない場合
    raise RuntimeError(f"No free port available in range {start_port}-{end_port}")


# ブラウザドライバをセットアップする
def setup_driver():
    try:
        # socks_port = get_random_socks_port()
        socks_port = find_unused_port()
        reset_tor_port()

        torProc, torConfFile = start_tor(socks_port)  # Torを起動

        driver, service, temp_dir = sb.Func_SettingDriver_Chrome(socks_port,
                                                                 'SingleSiteWatcher',
                                                                 execute_driver = True,
                                                                 TorEnable = True,
                                                                 headless_options = False)

        return torProc, driver, service, temp_dir, torConfFile
    except Exception as e:
        log_exception(e)
        return None
    
def clear_driver(torProc, driver, service, temp_dir, torConfFile):
    # temp_dirはE:\MonitorSystem\Source\OnionScraperV2\MonitorMainV2_Watcher.pyがわで削除してくれるから頼る

    if driver:
        driver.quit()
    if torProc:
        torProc.terminate()
        torProc.wait()  # プロセスが終了するのを待つ
    if service:
        killService(service)

    cleanup_torrc(torConfFile)

# 一時的なtorrcファイルを削除
def cleanup_torrc(torConfFile):
    try:
        if torConfFile and fo.Func_IsFileExist(torConfFile):
            os.remove(torConfFile)
    except Exception as e:
        log_exception(e)

# -------------------------------------------------------------------------------------------------
# TORの起動とブラウザのセットアップ、クリア処理関数 - ここまで
# -------------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------------------------
# 結果ファイルの書き込みや比較など
# -------------------------------------------------------------------------------------------------
def update_status_arrays(newEntry, exsitData, target_group):
    # 各グループについて、target_group に該当する場合に new_entry を追加
    access_results = []
    groupName = exsitData.get('groupName', '')
    if groupName == target_group:
        access_results = exsitData.get('accessResult',[])                    
    # 新しいエントリを追加
    access_results.append(newEntry)
    # status.connectTime で降順にソート（最新が先頭になる）
    access_results.sort(key=lambda item: item["status"]["connectTime"], reverse=True)
    
    # 最大500件にしておく
    return access_results[:500]

def update_and_write_status(groupName, newData, notificationInfo = {}):
    """
    ファイルから既存データを読み込み、新しいデータでアップデートして書き込む
    スレッドロックによる排他制御付きの関数
    """
    try:
        targetDir = os.path.join( RESULT_STOCK_DIR, groupName)
        fo.Func_CreateDirectry(targetDir)
        targetPath = os.path.join( targetDir, f'accessLog.json')
        # with file_lock:
        # 既存データの読み込み
        existing_data = fo.Func_ReadJson2Dict(targetPath)
        # データの更新
        if newData:
            updated_data = update_status_arrays(newData, existing_data, groupName)
        else:
            updated_data = existing_data.get("accessResult", [])

        notificationInfoTmp = notificationInfo
        if notificationInfo == {}:
            notificationInfoTmp = existing_data.get("notificationInfo", {})

        targetData = {
            'groupName':groupName,
            'notificationInfo': notificationInfoTmp,
            'accessResult': updated_data
        }
        # 更新データの書き込み
        fo.Func_WriteDict2Json(targetPath, targetData)
    except Exception as e:
        log_exception(e)

    return targetData

def readNotificationstatus(groupName):
    ret = {}
    targetDir = os.path.join( RESULT_STOCK_DIR, groupName)
    fo.Func_CreateDirectry(targetDir)
    targetPath = os.path.join( targetDir, f'accessLog.json')
    existing_data = fo.Func_ReadJson2Dict(targetPath)
    ret = existing_data.get('notificationInfo', {})

    return ret

def cleanup_local_backups(groupName, dstDirPath):
    """
    ローカルバックアップフォルダ内のファイルが MAX_LOCAL_FILES を超えた場合、
    一番古いファイルを削除して、最大保存数を維持する。
    """
    files = [os.path.join(dstDirPath, f) for f in os.listdir(dstDirPath) ]
    files.sort(key=lambda x: os.path.getmtime(x))
    while len(files) > MAX_LOCAL_FILES:
        file_to_delete = files.pop(0)
        os.remove(file_to_delete)
        print(f"古いローカルバックアップファイルを削除しました: {file_to_delete}")

def saveResultOuterHtmltext(groupName, accessTimeStr, htmlText):
    try:
        retDstFilePath = ''
        if len(htmlText) > 0:
            dstDirPath = os.path.join( RESULT_STOCK_DIR, groupName)
            dstDirPath = os.path.join( dstDirPath, 'OuterHtml')
            if not os.path.exists(dstDirPath): 
                fo.Func_CreateDirectry(dstDirPath)
            retDstFilePath = os.path.join(dstDirPath, f'{groupName}_OuterHtml_{accessTimeStr}.txt')
       
            fo.Func_WiteFile(retDstFilePath, htmlText)
            
            cleanup_local_backups(groupName, dstDirPath)

    except Exception as e:
        log_exception(e)

    return retDstFilePath  

def saveResultTextData(groupName, accessTimeStr, textData):
    try:
        retDstFilePath = ''
        if len(textData) > 0:
            dstDirPath = os.path.join( RESULT_STOCK_DIR, groupName)
            dstDirPath = os.path.join( dstDirPath, 'TextData')
            if not os.path.exists(dstDirPath): 
                fo.Func_CreateDirectry(dstDirPath)
            retDstFilePath = os.path.join(dstDirPath, f'{groupName}_TextData_{accessTimeStr}.txt')
       
            fo.Func_WiteFile(retDstFilePath, textData)
            
            cleanup_local_backups(groupName, dstDirPath)

    except Exception as e:
        log_exception(e)

    return retDstFilePath 

def generate_sha256(input_str):
    # 文字列をバイト列に変換
    encoded_str = input_str.encode()
    # SHA256 のハッシュオブジェクトを生成
    sha256_hash = hashlib.sha256(encoded_str)
    # 16進数の文字列に変換して返す
    return sha256_hash.hexdigest()  

def saveResultScreenShot(groupName, accessTimeStr, driver):
    try:
        retDstFilePath = ''
        dstDirPath = os.path.join( RESULT_STOCK_DIR, groupName)
        dstDirPath = os.path.join( dstDirPath, 'ScreenShot')
        if not os.path.exists(dstDirPath): 
            fo.Func_CreateDirectry(dstDirPath)
        retDstFilePath = os.path.join(dstDirPath, f'{groupName}_BodyScreenShot_{accessTimeStr}.png')
    
        # <body> 要素を取得
        # body = driver.find_element(By.TAG_NAME, 'body')
        # body.screenshot(retDstFilePath)

        retDstFilePath = gh.getScreenShot(groupName, driver, dstDirPath)

        cleanup_local_backups(groupName, dstDirPath)

    except Exception as e:
        log_exception(e)

    return retDstFilePath  
# -------------------------------------------------------------------------------------------------
# 結果ファイルの書き込みや比較など - ここまで
# -------------------------------------------------------------------------------------------------
# stmp_user_v4 = 'iroiromonitaro1v2.4@gmail.com'
# stmp_password_v4 = 'pnvy rvun ozbm myjf'
stmp_user_v5 = 'iroiromonitaro1v2.5@gmail.com'
stmp_password_v5 = 'utkupxnucvlmgmef'

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from PIL import Image
import io

def defang_url(url):
    # http/https を defang し、ドメイン部分の "." も置換
    url = url.replace("http://", "hxxp://")
    url = url.replace("https://", "hxxps://")
    url = url.replace(".", "[.]")
    return url

from jinja2 import Template
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
import io

def defang_url(url):
    # http/https を defang し、ドメイン部分の "." も置換
    url = url.replace("http://", "hxxp://")
    url = url.replace("https://", "hxxps://")
    url = url.replace(".", "[.]")
    return url

def sendMail_google(groupName, subject, accessTime, targetURL, pngFilePath, text = '', note = None):
    # print(f"[メール送信停止中] {subject}")  # 確認用
    try:
        stmp_server = "smtp.gmail.com"
        stmp_port = 587
        # ここはグローバル変数等で定義されている前提
        from_address = stmp_user_v5
        send_address = cf.SENDTO_REPORT
        # send_address = ['y.yasuda@mbsd.jp','m.fukuda@mbsd.jp']


        # メッセージコンテナを作成（インライン画像用に'related'を指定）
        msg = MIMEMultipart('related')
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = from_address

        defanged_url = defang_url(targetURL)

        if text:
            # AKIRAのJSON形式データを整形してHTML化
            try:
                data = json.loads(text)
                formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                # JSON の内部でエスケープされている "\n" を実際の改行に変換
                formatted_json = formatted_json.replace('\\n', '\n')
                # その後に HTML エスケープ
                safe_formatted_json = html.escape(formatted_json)
            except:
                safe_formatted_json = html.escape(text)  # JSONパースに失敗したら生データを使用
            # memo
            if '接続不可の可能性' in subject:
                memo = f"監視対象の{groupName}リークサイトにアクセスしましたが、データを取得できませんでした。サイトが一時的にダウンしているか、接続に問題がある可能性があります。"
            else:
                # デフォルト（差分検知の場合）
                memo = f"監視対象の{groupName}リークサイトの差分が検知されました。前回の接続成功時とテキストの差分が発生している可能性があります。"

            note_section = ""
            if note and '接続不可の可能性' not in subject:
                #接続成功時のみNoteを表示
                note_section = f'<div class="note-section">{note}</div>'

            html_body = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        max-width: 900px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: #dc3545;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 8px 8px 0 0;
                    }}
                    .json-content {{
                        padding: 20px;
                        background: #1e1e1e;
                        color: #d4d4d4;
                        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                        font-size: 14px;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        overflow-x: auto;
                    }}
                    .warning {{
                        background: #ffecb5;
                        border: 1px solid #ffc107;
                        padding: 15px;
                        margin: 20px;
                        border-radius: 4px;
                    }}
                    .note-section {{
                        padding: 15px 20px;
                        background: #f0f8ff;
                        border-left: 4px solid #2196F3;
                        margin: 20px;
                        font-size: 13px;
                        color: #555;
                        line-height: 1.5;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{groupName} - 差分検知</h2>
                    </div>
                    {note_section}
                    <pre class="json-content">{safe_formatted_json}</pre>
                    <div class="warning">
                        <strong>メモ:</strong> {memo}<br>
                        アクセス時間: {accessTime}<br>
                        対象サイト: {defanged_url}
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, "html"))
        else:
            img_cid = 'png_image'

            # pngFilePath の存在確認で表示内容を変更
            if pngFilePath and os.path.exists(pngFilePath):
                image_div = f'<div class="image-container"><img src="cid:{img_cid}" alt="サイトの状況"></div>'
            else:
                image_div = '<div class="image-container"><p>スクリーンショットの取得に失敗しました。</p></div>'

            # Jinja2 のテンプレートを利用した HTML 本文
            html_template = """
            <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f9f9f9;
                        margin: 0;
                        padding: 20px;
                    }
                    .container {
                        background-color: #fff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    }
                    .header {
                        font-size: 24px;
                        margin-bottom: 10px;
                    }
                    .access-time {
                        color: #888;
                        font-size: 14px;
                        margin-bottom: 20px;
                    }
                    .content {
                        font-size: 16px;
                        line-height: 1.5;
                    }
                    .image-container {
                        margin-top: 20px;
                        text-align: center;
                    }
                    .image-container img {
                        max-width: 100%;
                        height: auto;
                        border-radius: 4px;
                    }
                    .note-section {
                        padding: 15px 20px;
                        background: #f0f8ff;
                        border-left: 4px solid #2196F3;
                        margin: 20px;
                        font-size: 13px;
                        color: #555;
                        line-height: 1.5;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">{{ groupName }}のサイトに変更が発生した可能性があります</div>
                    <div class="access-time">アクセス時間: {{ accessTime }}</div>
                    <div class="content">
                        サイトに変更があったことをお知らせします。<br>
                        以下は現在のサイトの状況です。<br>
                        対象サイト: {{ defanged_url }}<br>
                    </div>
                    {{ image_div | safe }}
                </div>
            </body>
            </html>
            """
            template = Template(html_template)
            html_body = template.render(
                groupName=groupName,
                accessTime=accessTime,
                defanged_url=defanged_url,
                image_div=image_div
            )

            # HTML本文をMIMETextとして添付
            msg.attach(MIMEText(html_body, "html"))

            # pngFilePath が存在する場合は画像を読み込み、リサイズして添付
            if pngFilePath and os.path.exists(pngFilePath):
                max_width = 800
                max_height = 600
                with Image.open(pngFilePath) as img:
                    if img.width > max_width or img.height > max_height:
                        img.thumbnail((max_width, max_height))
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    img_data = img_byte_arr.getvalue()

                image_part = MIMEImage(img_data, 'png')
                image_part.add_header('Content-ID', f'<{img_cid}>')
                image_part.add_header('Content-Disposition', 'inline', filename="screenshot.png")
                msg.attach(image_part)

        # SMTPサーバに接続してメール送信
        s = smtplib.SMTP(stmp_server, stmp_port)
        s.starttls()
        s.login(stmp_user_v5, stmp_password_v5)
        s.sendmail(from_address, send_address, msg.as_string())
        s.quit()

        isSuccess = True
    except Exception as e:
        log_exception(e)
        isSuccess = False

    return isSuccess


def should_retry(error_message):
    """
    リトライすべきでないエラーかどうかを判断し、該当するエラーパターンを返す
    
    Args:
        error_message (str): エラーメッセージ
        
    Returns:
        tuple: (リトライすべきかどうか, エラーの種類を示す文字列)
    """
    no_retry_patterns = {
        "about:neterror?e=connectionFailure": "Connection Failure - Server unreachable",
        "about:neterror?e=dnsNotFound": "DNS Not Found - Domain does not exist",
        "SSL_ERROR": "SSL Certificate Error"
    }
    
    for pattern, message in no_retry_patterns.items():
        if pattern in error_message:
            return False, message
            
    return True, error_message

# スクレイピング処理
def scrape_urls(url_list):
    ret = {}

    print(f"[DEBUG] scrape_urls開始: {len(url_list)}件")  # ← 追加

    try:
        # urlDataArray = copy.deepcopy(url_list)
        for entry in url_list:
            groupName = entry['groupName']
            urlList = entry["urlList"]

            print(f"[DEBUG] 処理開始: {groupName}, URL数: {len(urlList)}")  # ← 追加

            for url in urlList:
                print(f"[DEBUG] URL処理: {groupName} - {url}")  # ← 追加
                currentTime = int(time.time())
                human_readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(currentTime))
                forFileName_time = time.strftime("%Y%m%d_%H%M%S", time.localtime(currentTime))
                
                retOuterHtmlText = ''
                retTextData = ''
                resultScreenShotPath = ''
                driver = None
                
                accessResult = {
                    'url':url,
                    'status':{
                    'title':'',
                    'outerHtmlHash': '',
                    'textDataHash': '',
                    'connectionStatus':'error',
                    'errorString':'',
                    'connectTime':currentTime,
                    'connectTime_display':human_readable_time
                    }
                }

                jsonItem = next(g for g in TARGET_GROUPLIST_JSON if g['groupName'] == groupName)
                useRequestMethod = jsonItem.get('useRequestMethod', False)

                # seleniumを使用する場合はDriverの取得は一回だけ
                if not useRequestMethod:
                    torProc, driver, service, temp_dir, torConfFile = setup_driver()
                    if not driver:
                        raise Exception("Driver setup failed")
                
                try:
                    retries = 0
                    while retries < MAX_RETRIES:
                        try:
                            access_start = time.time()

                            if useRequestMethod:
                                databaseUrl = urllib.parse.urljoin(url, jsonItem.get('AdditionalURL', '/s'))
                                headers = jsonItem.get('Headers', None)
                                requestData = jsonItem.get('RequestData', None)
                                response = sb.getHtmlResponseByRequest_Post(databaseUrl, headers=headers, requestData=requestData, verify=False)
                                if response:
                                    if response.content:
                                        raw_bytes = response.content
                                        if len(raw_bytes) > 0:
                                            retTextData = raw_bytes.decode("utf-8")
                                            jsonData = json.loads(retTextData)
                                else:
                                    retries += 1
                                    continue
                            else:
                                driver.set_page_load_timeout(600)  # タイムアウト時間を設定
                                driver.get(url)
                                html = driver.page_source.encode('utf-8')
                                soup = BeautifulSoup(html, 'html.parser')
                                retOuterHtmlText = soup.prettify()
                                retTextData = soup.get_text(separator="\n")

                            # 接続完了時の経過時間を計算
                            access_time = time.time() - access_start
                            if access_time >= 60:
                                print(f"{groupName} 接続完了: {url} - 所要時間: {int(access_time // 60)}分{int(access_time % 60)}秒")
                            else:
                                print(f"{groupName} 接続完了: {url} - 所要時間: {int(access_time)}秒")

                            title = ''
                            if useRequestMethod:
                                # 取得JSONの例外を防ぐ処理を挿入
                                # title = jsonData.get('articles', [])[0].get('title', '').strip()
                                try:
                                    articles = (jsonData.get('articles') or []) if isinstance(jsonData, dict) else []
                                    if len(articles) > 0 and isinstance(articles[0], dict):
                                        title = (articles[0].get('title') or '').strip()
                                except Exception:
                                    title = ''
                            else:
                                title = driver.title
                            
                            accessResult['status']['title'] = title
                            accessResult['status']['connectionStatus'] = 'success'
                            accessResult['status']['accessTime'] = access_time

                            break  # 成功したらループを抜ける
                        except TimeoutException as e:
                            print(f"Timeout while trying to connect to {url}, retrying...")
                            accessResult['status']['errorString'] = 'TimeoutException'
                            accessResult['status']['connectionStatus'] = 'error'
                            log_exception(e)
                            time.sleep(5 * (retries + 1))
                            retries += 1
                        except requests.RequestException as e:
                            print(f"Requests error connecting to {url}: {e}, retrying...")
                            accessResult['status']['errorString'] = f"Requests error connecting : {str(e)}"
                            accessResult['status']['connectionStatus'] = 'error'
                            log_exception(e)
                            time.sleep(5 * (retries + 1))
                            retries += 1
                        except WebDriverException as e:
                            error_message = str(e)
                            print(f"WebDriver error scraping {url}: {e}")
                            should_continue, error_type = should_retry(error_message)
                            accessResult['status']['connectionStatus'] = 'error'
                            log_exception(e)
                            if not should_continue:
                                accessResult['status']['errorString'] =f"WebDriver error. Non-retryable error detected : {error_type}"
                                break  # リトライ不要なエラーの場合はループを抜ける
                            else:
                                accessResult['status']['errorString'] = f"WebDriver error : {error_type}"
                            time.sleep(5 * (retries + 1))        
                            retries += 1

                        except Exception as e:
                            accessResult['status']['errorString'] = f"Exception : {str(e)}"
                            accessResult['status']['connectionStatus'] = 'error'
                            log_exception(e)
                            time.sleep(5 * (retries + 1))
                            retries += 1
                        
                finally:
                    if retOuterHtmlText:
                        hashStr = generate_sha256(retOuterHtmlText)
                        accessResult['status']['outerHtmlHash'] = hashStr
                        resultOuterHtmlPath = saveResultOuterHtmltext(groupName, forFileName_time, retOuterHtmlText)
                        resultScreenShotPath = saveResultScreenShot(groupName, forFileName_time, driver)
                        
                    if retTextData:
                        hashStr = generate_sha256(retTextData)
                        accessResult['status']['textDataHash'] = hashStr
                        resultTextDataPath = saveResultTextData(groupName, forFileName_time, retTextData)

                    if driver:
                        clear_driver(torProc, driver, service, temp_dir, torConfFile)

                ret = update_and_write_status(groupName, accessResult)

                # 次の処理の前に少し待つ
                import time as time_module
                time_module.sleep(5)  # 5秒待機（Torが完全に終了するまで）

                accessResultTmp = ret.get('accessResult', [])
                if len(accessResultTmp) >= 1:
                    subject = ''
                    text = ''
                    forceNotification = False
                    if len(accessResultTmp) == 1:
                        forceNotification = True
                        subject = '特定監視サイトの変更検知 (監視開始)'
                    else:
                        latest = accessResultTmp[0]
                        latest_status = latest.get('status', {})
                        latest_hash = latest_status.get('textDataHash', '')
                        latest_conn = latest_status.get('connectionStatus', 'error')

                        prev_success_hash = ''
                        for item in accessResultTmp[1:]:
                            st = item.get('status', {})
                            if st.get('connectionStatus') == 'success' and st.get('textDataHash', '') != '':
                                prev_success_hash = st.get('textDataHash', '')
                                break

                        if latest_conn == 'success' and latest_hash != '' and prev_success_hash != '' and latest_hash != prev_success_hash:
                            forceNotification = True
                            subject = '特定監視サイトの変更検知'
                            if useRequestMethod:
                                text = retTextData
                        #接続不可時は2時間以内にメール送信されていない場合にのみ送信
                        elif latest_hash == '':
                            subject = '特定監視サイトの変更検知 (接続不可の可能性)'
                            if useRequestMethod:
                                text = 'リークサイトにアクセスした結果、何らかの理由で接続できず、情報を取得できませんでした。'
                        
                        # --------前回条件（直前ハッシュとの比較）-----
                        # accessResultHash0 = accessResultTmp[0]['status']['textDataHash']
                        # accessResultHash1 = accessResultTmp[1]['status']['textDataHash']
                        # # 前回と差分がある
                        # if accessResultHash0 != accessResultHash1:
                        #     # 今回のアクセスでテキストが取得できた
                        #     if accessResultHash0 != '':
                        #         forceNotification = True
                        #         subject = '特定監視サイトの変更検知'
                        #         if useRequestMethod:
                        #             text = retTextData
                            # 今回のアクセスでテキストが取得できなかった場合
                            # else:
                            #     subject = '特定監視サイトの変更検知 (接続不可の可能性)'
                            #     if useRequestMethod:
                            #         text = 'リークサイトにアクセスした結果、何らかの理由で接続できず、情報を取得できませんでした。'
                        
                    if subject != '':
                        sendNotifiocation = False
                        currentTime = int(time.time())
                        notificationStatus = readNotificationstatus(groupName)
                        if notificationStatus:
                            setTime = notificationStatus.get('sentTime', -1)
                            if setTime > 1 and int(time.time()) >= setTime + 43200:  # 12時間
                                sendNotifiocation = True
                        else:
                            # 初回や未送信時は2時間ルールに従い送信しない（明示的に何もしない）
                            pass
                            # notificationStatus = True
                        
                        # 取得したウェブサイトのテキストに差分が発生したら
                        if sendNotifiocation or forceNotification: 
                            # DEBUG
                            # text = "{"articles":[{"date":"2025-09-01","title":"Genmark Automation\n","content":"Founded in 1985 and headquartered in California. Genmark Automati\non is a worldwide developer and manufacturer of tool and fab auto\nmation equipment solutions for the semiconductor, flat panel, sol\nar, LED, data storage, and associated industries.\n\nWe are ready to upload more than 47Gb files of essential corporat\ne documents such as: financial data (audit, payment details,finan\ncial reports, invoices), employees and customers information (gre\nen cards, passports, driver's license, Social Security Numbers, c\nredit cards, death/birth certificate, medical information, emails\n, phones, addresses) confidential information, NDAs and other doc\numents with detailed personal information so on. \n\nThe company management refused to take the situation seriously. S\no their employees and customers will have to face all the consequ\nences of their data being compromised.\n"}],"leaks":[]}
                            note = jsonItem.get('Note', None)
                            sendMail_google(groupName, subject, human_readable_time, url, resultScreenShotPath, text, note)
                            human_readable_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(currentTime))
                            notificationInfo = {
                                'sentTime': currentTime,
                                'sentTime_display': human_readable_time,
                                'accessStatus': accessResultTmp[0]['status']['connectionStatus']
                            }
                            update_and_write_status(groupName, newData = None, notificationInfo = notificationInfo)
    except Exception as e:
        log_exception(e)

    return ret

def getUrlData():
    try:
        ret = []
        orgData = fo.Func_ReadJson2Dict(cf.TARGET_URL_JSON_PATH)
        print(f"[DEBUG] orgData keys: {orgData.keys()}")  # ← 追加

        for item in TARGET_GROUPLIST_JSON:
            groupName = item.get('groupName')
            print(f"[DEBUG] 処理中: {groupName}")  # ← 追加
            if groupName:
                groupCfg = orgData.get(groupName, {})
                print(f"[DEBUG] {groupName} groupCfg: {groupCfg}")  # ← 追加
                if groupCfg:
                    urlList = groupCfg.get('urlList', [])
                    url = groupCfg.get('url', '')
                    print(f"[DEBUG] {groupName} url: {url}, urlList: {urlList}")  # ← 追加
                    if url and url not in urlList:
                        urlList.append(url)
                    if urlList:
                        ret.append({'groupName': groupName, 'urlList': urlList})
                        print(f"[DEBUG] {groupName} 追加完了")  # ← 追加
        print(f"[DEBUG] getUrlData結果: {ret}")  # ← 追加               
        return ret

    except Exception as e:
        print(f'Exception: {str(e)}')
        return []

# マルチスレッドでのスクレイピング実行
def start_scraping():
    try:
        urlDataArray = getUrlData()
        # accessLog = fo.read_from_json_file(ACCESSLOG_PATH)
        
        if urlDataArray:
            retAccessStatusArray = []
            if DEBUG_MODE:
                retAccessStatusArray = scrape_urls(urlDataArray[:2])  # デバッグモードの場合は単一スレッドで実行
            else:
                # URLリストをスレッド数で分割
                chunk_size = max(1, len(urlDataArray) // MAX_THREADS)
                url_chunks = [urlDataArray[i:i + chunk_size] for i in range(0, len(urlDataArray), chunk_size)]
                
                # ThreadPoolExecutorを使用して並行処理
                with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                    # 全てのタスクを実行し、完了を待つ
                    result = list(executor.map(scrape_urls, url_chunks))
                    result = result
                    # retAccessStatusArray = [item for sublist in resultArray for item in sublist]

                    # # エラーハンドリングを追加（オプション）
                    # for future in retAccessStatusArray:
                    #     try:
                    #         if future is not None:  # 結果が返されている場合の処理
                    #             pass  # 必要に応じて結果の処理を追加
                    #     except Exception as e:
                    #         log_exception(e)

    except Exception as e:
        log_exception(e)

if __name__ == "__main__":
    set_no_proxy()

    while True:
        try:
            start_time = datetime.now()
            print(f"\n処理開始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            start_scraping()
            
            end_time = datetime.now()
            print(f"処理終了: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 次の実行までの待機時間を計算（10分 = 600 秒）
            elapsed_time = (end_time - start_time).total_seconds()
            intervalTime = 600
            # LunaLockerのデータ公開までタイマーを差分検知しちゃってうざいのでいったん時間を延ばす
            # intervalTime = 3600
            wait_time = max(0, intervalTime - elapsed_time)
            
            count = 0
            while count <= intervalTime:
                time.sleep(1)
                count += 1

                # 1分おきにPrint
                if count % 60 == 0:
                    # print(f"次の実行まで {wait_time:.1f} 秒待機します")
                    print(f"次の実行まで {intervalTime-count:.1f} 秒待機します")

            
        except Exception as e:
            log_exception(e)
            # エラーが発生した場合も待機してから次の実行を試みる
            time.sleep(600)
