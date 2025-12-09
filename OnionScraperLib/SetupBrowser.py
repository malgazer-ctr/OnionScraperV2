import os
from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from Config import Config as cf
from OnionScraperLib import Log
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import GroupLogger as groupLogger


#スクリーンショット時のヘッドレスの有効無効（0：ブラウザが表示され無効にすると見えている範囲だけ撮影される）
headless_options = 1

import requests
# def getChromeDriverPath(options_):

#     url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
#     response = requests.get(url)
#     ret = None
 
#     ## 最新のバージョンのChromeドライバーを取得する
#     try:
#         ret = ChromeDriverManager().install()

#     except ValueError:
#         # ValueErrorが発生した場合、バージョンを指定してインストール
#         ret = ChromeDriverManager(version=response.text).install()
#     return ret

# getChromeDriverPath() の最後で、返ってきたパスが .exe でなければ同じディレクトリをスキャンして .exe ファイルを探し、そちらを返すようにします。
def getChromeDriverPath(options_):
    url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
    response = requests.get(url)
    ret = None

    ## 最新のバージョンのChromeドライバーを取得する
    try:
        # install() はダウンロードした chromedriver.exe のフルパスまたは
        # キャッシュディレクトリパスを返します
        ret = ChromeDriverManager().install()
    except ValueError:
        # ValueErrorが発生した場合、バージョンを指定してインストール
        # response.text には "114.0.5735.90" のようなバージョン文字列が入っています
        ret = ChromeDriverManager(version=response.text.strip()).install()

    # ────────────────────────────────────────────
    # install() が返してくるパスが .exe でなければ、
    # 同じフォルダ内の chromedriver.exe を探して返す
    # ────────────────────────────────────────────
    # もし既に .exe ならそのまま返す
    if isinstance(ret, str) and ret.lower().endswith('.exe') and os.path.exists(ret):
        return ret

    # パスがファイルならディレクトリ部分を、ディレクトリならそのまま
    directory = ret if os.path.isdir(ret) else os.path.dirname(ret)

    # ディレクトリ内のファイルを走査して .exe を探す
    for fname in os.listdir(directory):
        if fname.lower().startswith('chromedriver') and fname.lower().endswith('.exe'):
            return os.path.join(directory, fname)

    # 万一見つからなければ元のパスを返す
    return ret


def createTempDir():
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    return temp_dir

# def Func_SettingDriver_Chrome(portForGroup, RansomName, execute_driver, TorEnable, impersonation = False, headless_options = True):
#     try:
#         service = None
#         temp_dir = ''
#         #Seleniumオプション
#         selenium_options = Options()
#         selenium_options.add_argument('--hide-scrollbars') #スクロールバーを消す
#         main_driver = None
        
#         if headless_options:
#             selenium_options.add_argument('--headless') #ヘッドレス（ブラウザが見えなくなる）
   
#         if impersonation:
#             # selenium_options.add_argument(r"--user-data-dir=C:\users\malga\AppData\Local\Google\Chrome\User Data\Profile 1") #e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
#             # selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
#             selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
#         else:
#             #UserAgent
#             # selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0')
#             selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0')

#         # if desiredCapabilities:
#         selenium_options.add_argument("--ignore-ssl-errors=yes")
#         selenium_options.add_argument("--ignore-certificate-errors")

#         if TorEnable == True:
#             #TorをPROXYで設定
#             PROXY = "socks5://localhost:" + str(portForGroup)
#             selenium_options.add_argument('--proxy-server=%s' % PROXY)

#         temp_dir = createTempDir()
#         selenium_options.add_argument(f'--user-data-dir={temp_dir}')
#         selenium_options.add_argument('--disk-cache-dir={temp_dir}/cache')
#         selenium_options.add_argument('--disable-application-cache')
#         selenium_options.add_argument('--media-cache-size=1')
#         selenium_options.add_argument('--disk-cache-size=1')

#         if execute_driver == True:
#             # 2023/8からChromeDriver取得の仕様が変更。Serviceを渡すことで最新のDriverを取得してくるらしいのでパス渡しやめ
#             new_driver = getChromeDriverPath(selenium_options)

#             # もしブラウザのバージョンが上がってしまいChromeDrier.exeとバージョン互換がとれなくなったら
#             # https://googlechromelabs.github.io/chrome-for-testing/#stable から同バージョンのChromeDrier.exeをダウンロードし
#             # E:\MonitorSystem\Python310\Lib\site-packages\seleniumbase\drivers 直下のChromeDrier.exeを置き換える
#             # 自動バージョンアップしてたけど、タイミングによっては最新バージョンに自動アップデートできないケースがあったので手動
#             # service = Service()  # Serviceオブジェクトを生成
#             service = Service(executable_path=new_driver)  # Serviceオブジェクトを生成

#             main_driver = webdriver.Chrome(service=service, options=selenium_options)

#             #ページロードのタイムアウトを設定
#             main_driver.set_page_load_timeout(200) #秒
#             #ページ上の要素読み込み待ち時間
#             main_driver.implicitly_wait(200) # seconds
#             #Javascript読み込み待ち時間
#             main_driver.set_script_timeout(20)

#     except Exception as e:
#         Log.Logging(RansomName,"{}: Exception:Get Driver Failed/{}".format(Log.Trace.execution_location(), str(e.args)))
        
#     return main_driver, service, temp_dir
# def Func_SettingDriver_Chrome(portForGroup, RansomName, execute_driver, TorEnable, 
#                              impersonation=False, headless_options=True, 
#                              custom_headers=None):
#     """
#     Args:
#         portForGroup: Torプロキシのポート番号
#         RansomName: ログ用の名前
#         execute_driver: ドライバーを実行するかどうか
#         TorEnable: Torを使用するかどうか
#         impersonation: なりすましモードかどうか
#         headless_options: ヘッドレスモードかどうか
#         custom_headers: カスタムヘッダー辞書（指定時はselenium-wire使用）
#     """
#     try:
#         service = None
#         temp_dir = ''
#         # Seleniumオプション
#         selenium_options = Options()
#         selenium_options.add_argument('--hide-scrollbars')
#         main_driver = None
        
#         if headless_options:
#             selenium_options.add_argument('--headless')
   
#         if impersonation:
#             selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
#         else:
#             selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0')
        
#         selenium_options.add_argument("--ignore-ssl-errors=yes")
#         selenium_options.add_argument("--ignore-certificate-errors")
        
#         # selenium-wire用のオプション
#         seleniumwire_options = {}
        
#         # カスタムヘッダーが指定されている場合
#         if custom_headers:
#             seleniumwire_options['custom_headers'] = custom_headers
        
#         if TorEnable == True:
#             PROXY = "socks5://localhost:" + str(portForGroup)
#             selenium_options.add_argument('--proxy-server=%s' % PROXY)
            
#             # custom_headersが指定されている場合はselenium-wire用のプロキシ設定
#             if custom_headers:
#                 seleniumwire_options['proxy'] = {
#                     'http': PROXY,
#                     'https': PROXY,
#                     'no_proxy': 'localhost,127.0.0.1'
#                 }
        
#         temp_dir = createTempDir()
#         selenium_options.add_argument(f'--user-data-dir={temp_dir}')
#         selenium_options.add_argument('--disk-cache-dir={temp_dir}/cache')
#         selenium_options.add_argument('--disable-application-cache')
#         selenium_options.add_argument('--media-cache-size=1')
#         selenium_options.add_argument('--disk-cache-size=1')
        
#         if execute_driver == True:
#             new_driver = getChromeDriverPath(selenium_options)
#             service = Service(executable_path=new_driver)
            
#             # custom_headersの有無でドライバーを切り替え
#             if custom_headers:
#                 # selenium-wireを使用
#                 from seleniumwire import webdriver
#                 main_driver = webdriver.Chrome(
#                     service=service, 
#                     options=selenium_options,
#                     seleniumwire_options=seleniumwire_options
#                 )
#             else:
#                 # 通常のseleniumを使用
#                 from selenium import webdriver
#                 main_driver = webdriver.Chrome(
#                     service=service, 
#                     options=selenium_options
#                 )
            
#             main_driver.set_page_load_timeout(200)
#             main_driver.implicitly_wait(200)
#             main_driver.set_script_timeout(20)
            
#     except Exception as e:
#         Log.Logging(RansomName,"{}: Exception:Get Driver Failed/{}".format(Log.Trace.execution_location(), str(e.args)))
        
#     return main_driver, service, temp_dir
def Func_SettingDriver_Chrome(portForGroup, RansomName, execute_driver, TorEnable, 
                             impersonation=False, headless_options=True, 
                             custom_headers=None):
    """
    Args:
        portForGroup: Torプロキシのポート番号
        RansomName: ログ用の名前
        execute_driver: ドライバーを実行するかどうか
        TorEnable: Torを使用するかどうか
        impersonation: なりすましモードかどうか
        headless_options: ヘッドレスモードかどうか
        custom_headers: カスタムヘッダー辞書（指定時はselenium-wire使用）
    """
    try:
        service = None
        temp_dir = ''
        main_driver = None

        # --- Seleniumオプション作成 ---
        selenium_options = Options()
        # （安定化）Linux等のCIでのクラッシュ/描画不全対策
        selenium_options.add_argument('--no-sandbox')
        selenium_options.add_argument('--disable-dev-shm-usage')
        selenium_options.add_argument('--ignore-ssl-errors=yes')
        selenium_options.add_argument('--ignore-certificate-errors')
        selenium_options.add_argument('--hide-scrollbars')

        # ヘッドレスの扱い：newを優先（旧環境は後段で自動フォールバック）
        if headless_options:
            selenium_options.add_argument('--headless=new')
            # ヘッドレスでは最大化が効かないため、十分広い初期ビューポートを指定
            selenium_options.add_argument('--window-size=2400,1600')
            # 高DPI相当で鮮明に（任意・環境により無視されることあり）
            selenium_options.add_argument('--force-device-scale-factor=2')
        else:
            # 非ヘッドレスはOSウィンドウ最大化を試みる
            selenium_options.add_argument('--start-maximized')

        cf.isheadless = headless_options

        # UA（既存仕様を踏襲）
        if impersonation:
            selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        else:
            selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0')

        # selenium-wire用のオプション
        seleniumwire_options = {}
        if custom_headers:
            seleniumwire_options['custom_headers'] = custom_headers

        # プロキシ（Tor）
        if TorEnable is True:
            PROXY = "socks5://localhost:" + str(portForGroup)
            selenium_options.add_argument(f'--proxy-server={PROXY}')
            if custom_headers:
                seleniumwire_options['proxy'] = {
                    'http': PROXY,
                    'https': PROXY,
                    'no_proxy': 'localhost,127.0.0.1'
                }

        # 一時プロファイル（既存仕様を踏襲）
        temp_dir = createTempDir()
        selenium_options.add_argument(f'--user-data-dir={temp_dir}')
        selenium_options.add_argument(f'--disk-cache-dir={temp_dir}/cache')  # ← 元コードのフォーマット漏れを修正
        selenium_options.add_argument('--disable-application-cache')
        selenium_options.add_argument('--media-cache-size=1')
        selenium_options.add_argument('--disk-cache-size=1')

        if execute_driver is True:
            new_driver = getChromeDriverPath(selenium_options)
            service = Service(executable_path=new_driver)

            # --- ドライバ生成（custom_headers の有無で selenium-wire 切替）---
            def _launch_driver(opts):
                if custom_headers:
                    from seleniumwire import webdriver as wire_webdriver
                    return wire_webdriver.Chrome(service=service, options=opts, seleniumwire_options=seleniumwire_options)
                else:
                    from selenium import webdriver
                    return webdriver.Chrome(service=service, options=opts)

            try:
                # まずは --headless=new で起動（または非ヘッドレス）
                main_driver = _launch_driver(selenium_options)
            except Exception as e:
                # 古いChrome/Driverで --headless=new 非対応の場合は旧スイッチへ安全フォールバック
                if headless_options:
                    try:
                        # 同じフラグを再構築しつつ --headless に差し替え
                        fallback_opts = Options()
                        for arg in selenium_options.arguments:
                            # '--headless=new' を削除
                            if arg.strip().startswith('--headless'):
                                continue
                            fallback_opts.add_argument(arg)
                        fallback_opts.add_argument('--headless')  # 旧ヘッドレス
                        main_driver = _launch_driver(fallback_opts)
                    except Exception:
                        raise e  # それでも失敗なら元の例外を外側の except へ

            # --- タイムアウト（既存値を踏襲）---
            main_driver.set_page_load_timeout(200)
            main_driver.implicitly_wait(200)
            main_driver.set_script_timeout(20)

            # --- 画面サイズの最終保証 ---
            try:
                if headless_options:
                    # ヘッドレスはウィンドウ最大化が効かないので明示セット
                    main_driver.set_window_size(2400, 1600)
                else:
                    # 非ヘッドレスはOS最大化を試行、失敗時はサイズ指定
                    try:
                        main_driver.maximize_window()
                    except Exception:
                        main_driver.set_window_size(1600, 1000)
            except Exception:
                pass

    except Exception as e:
        Log.Logging(RansomName, "{}: Exception:Get Driver Failed/{}".format(Log.Trace.execution_location(), str(e.args)))

    return main_driver, service, temp_dir


import undetected_chromedriver as uc
def Func_SettingDriver_Chrome_Undetected(portForGroup, RansomName,execute_driver,TorEnable, impersonation = False, headless_options = True):
    try:
        temp_Dir = ''
        #Seleniumオプション
        selenium_options = Options()
        selenium_options.add_argument('--hide-scrollbars') #スクロールバーを消す
        
        if headless_options:
            Log.Logging(RansomName,"ヘッドレスオプション設定：有効")
            selenium_options.add_argument('--headless') #ヘッドレス（ブラウザが見えなくなる）
        else:
            Log.Logging(RansomName,"ヘッドレスオプション設定：無効")

        Log.Logging(RansomName,"UserAgentを設定")

        if impersonation:
            # selenium_options.add_argument(r"--user-data-dir=C:\users\malga\AppData\Local\Google\Chrome\User Data\Profile 1") #e.g. C:\Users\You\AppData\Local\Google\Chrome\User Data
            selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        else:
            #UserAgent
            # selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0')
            selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0')

        # if desiredCapabilities:
        selenium_options.add_argument("--ignore-ssl-errors=yes")
        selenium_options.add_argument("--ignore-certificate-errors")

        Log.Logging(RansomName,"{}: TorEnable={}".format(Log.Trace.execution_location(), str(TorEnable)))
        
        if TorEnable == True:
            #TorをPROXYで設定
            Log.Logging(RansomName,"TorをPROXYで設定(port:" + str(portForGroup) + ")")
            PROXY = "socks5://localhost:" + str(portForGroup)
            selenium_options.add_argument('--proxy-server=%s' % PROXY)

        Log.Logging(RansomName,"{}: Optionを設定".format(Log.Trace.execution_location()))

        temp_dir = createTempDir
        selenium_options.add_argument(f'--user-data-dir={temp_dir}')

        if execute_driver == True:
            # 2023/8からChromeDriver取得の仕様が変更。Serviceを渡すことで最新のDriverを取得してくるらしいのでパス渡しやめ
            # new_driver = getChromeDriverPath(selenium_options)

            main_driver = uc.Chrome(options=selenium_options)

            #ページロードのタイムアウトを設定
            main_driver.set_page_load_timeout(300) #秒
            #ページ上の要素読み込み待ち時間
            main_driver.implicitly_wait(300) # seconds
            #Javascript読み込み待ち時間
            main_driver.set_script_timeout(60)

    except Exception as e:
        Log.Logging(RansomName,"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        
    return main_driver, temp_dir


def Func_SettingDriver_Firefox(portForGroup, RansomName,execute_driver,TorEnable):

    try:
        #Seleniumオプション
        selenium_options = webdriver.FirefoxOptions()
        selenium_options.binary_location = cf.PATH_FIREFOX
        selenium_options.add_argument('--hide-scrollbars') #スクロールバーを消す
        
        if headless_options == 1:
            Log.Logging(RansomName,"ヘッドレスオプション設定：有効")
            selenium_options.add_argument('--headless') #ヘッドレス（ブラウザが見えなくなる）
        else:
            Log.Logging(RansomName,"ヘッドレスオプション設定：無効")

        Log.Logging(RansomName,"UserAgentを設定")
        #UserAgent
        # 2022/12/01 FireFoxアップデートしたから？これやるとNS_ERROR_UNKNOWN_HOST吐くようになった。
        # ネット情報ではこれやらなければ起きないといった同一現象の報告も見かけたのでいったんコメント
        # selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0')
        # selenium_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0')

        Log.Logging(RansomName,"{}: TorEnable={}".format(Log.Trace.execution_location(), str(TorEnable)))

        if TorEnable == True:
            Log.Logging(RansomName,"TorをPROXYで設定(port:" + str(portForGroup) + ")")
            Log.Logging(RansomName,"Firefox プロファイル設定")
            # Firefox プロファイル設定
            torProxy = "localhost:" + str(portForGroup)
            ip, port = torProxy.split(':')
            profile = webdriver.FirefoxProfile()
            profile.set_preference('network.proxy.type', 1)
            profile.set_preference('network.proxy.socks_version', 5 )    # Socks5
            profile.set_preference('network.proxy.socks', ip)
            profile.set_preference('network.proxy.socks_port', int(port))
            profile.set_preference('network.proxy.socks_remote_dns', True )

            # Selenium 4.11.xではwebdriver.Firefoxがfirefox_profileを引数に取らなくなったので対応
            profilePath = r'C:\Users\malga\AppData\Roaming\Mozilla\Firefox\Profiles\wx6921np.default-release'
            # selenium_options.set_preference('profile', profilePath)
            # selenium_options.set_preference('network.proxy.type', 1)
            # selenium_options.set_preference('network.proxy.socks', '127.0.0.1')
            # selenium_options.set_preference('network.proxy.socks_port', 9050)
            # selenium_options.set_preference('network.proxy.socks_remote_dns', False)
            selenium_options.setProfile(profile)
        
        Log.Logging(RansomName,"{}: Optionを設定".format(Log.Trace.execution_location()))

        if execute_driver == True:
            new_driver = GeckoDriverManager().install()
            if TorEnable == True:
                #Optionを適用
                # webdriver.Firefoxが返ってこない場合はFireFoxのバージョンとGeckoのバージョンの互換性を疑う
                # https://github.com/mozilla/geckodriver/releases/
                main_driver = webdriver.Firefox(options=selenium_options)
            else:
                main_driver = webdriver.Firefox(options=selenium_options)
            #ページロードのタイムアウトを設定
            main_driver.set_page_load_timeout(200) #秒
            #ページ上の要素読み込み待ち時間
            main_driver.implicitly_wait(200) # seconds
            #Javascript読み込み待ち時間
            main_driver.set_script_timeout(20)

    except Exception as e:
        Log.Logging(RansomName,"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return main_driver, ''

from selenium.webdriver.chrome import service as fs
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as BraveService
def Func_SettingDriver_Brave(groupName, TorEnable = True, headless = True):
    browser = None  # ここで初期化
    driver = None
    try:
        option = webdriver.ChromeOptions()
 
        # Brave本体が、保存されているパスを入力
        option.binary_location = cf.PATH_BRAVE
 
        # BraveはheadlessモードにするとTORが動作しない疑惑。
        # 吉川さん環境だとうまくいっているっぽい・・・けど同じこと言っている人はけっこういる
        # option.add_argument('--headless')

        if TorEnable:
            option.add_argument("--tor")  # Launch in Tor mode

            if headless:
                option.add_argument('--headless=new')
        else:
            if headless:
                option.add_argument('--headless=new')
 
        option.add_argument("--start-maximized")
        option.add_argument("--disable-infobars")
        option.add_argument("--disable-extensions")
        option.add_argument("--disable-popup-blocking")
        option.add_argument("--disable-notifications")
        option.add_argument("--log-level=3")  # 出力をエラーメッセージのみに制限
        option.add_argument("--ignore-ssl-errors=yes")
        option.add_argument("--ignore-certificate-errors")
        
        driverPath = ChromeDriverManager().install()
        service=BraveService(driverPath)
        driver = webdriver.Chrome(options=option, service=service)

                # # WebDriverを保存したファイルパスを入力
                # chromDriverPath = ChromeDriverManager().install()
                # service = fs.Service(executable_path=chromDriverPath)
        
                # driver = webdriver.Chrome(options=option, service=service)
        # driver = webdriver.Chrome(options = option)
 
        # サイト表示
        # browser.get(inputURL)
 
        driver.implicitly_wait(10)

    except Exception as e:
        Log.Logging(groupName,"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return driver

# -----------------------------------------------------------------------------------
import requests
import tempfile
import os
import subprocess
import time
import ctypes
import psutil
import random
from stem import Signal
from stem.control import Controller
from stem import SocketError
import socket

def create_torrc(socks_port):
    torConfFile = ''
    try:
        temp_dir = tempfile.mkdtemp()
        torConfFile = os.path.join(temp_dir, f'torrc_{socks_port}')
        with open(torConfFile, 'w') as torrc_file:
            torrc_file.write(f"ControlPort {9051}\n")
            torrc_file.write("CookieAuthentication 1\n")
            torrc_file.write(f"SOCKSPort {socks_port}\n")
    except Exception as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return torConfFile

# Torが完全に起動したか確認する
def wait_for_tor_startup():
    # Torプロセスが実行中かどうかを確認
    def is_tor_running():
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'tor.exe' or proc.info['name'] == 'tor':
                    return True
            return False
        except Exception as e:
            Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
            return False
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
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

def start_tor(socks_port):
    try:
        torProc = None
        TOR_PATH = r"C:\Users\malga\Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe"
        if not os.path.exists(TOR_PATH):
            raise FileNotFoundError(f"Tor executable not found at {TOR_PATH}. Please install Tor or provide the correct path.")
        torConfFile = create_torrc(socks_port)
        torProc = subprocess.Popen([TOR_PATH, '-f', torConfFile])
        wait_for_tor_startup()
    except Exception as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return torProc, torConfFile

TOR_CONTROL_PORT = 9051  # Tor制御ポート番号
# Torのポートをリセットする
def reset_tor_port():
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            time.sleep(10)  # 新しいIPが有効になるまで少し待機
    except SocketError as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
    except Exception as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

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

# request用
def getSession(port = 9050):
    session = requests.Session()
    session.proxies = {
        'http': f'socks5h://127.0.0.1:{str(port)}',
        'https': f'socks5h://127.0.0.1:{str(port)}'
    }
    return session

# ブラウザドライバをセットアップする
def setup_driver(groupName, headless_ = False):
    try:
        # socks_port = get_random_socks_port()
        socks_port = find_unused_port()
        reset_tor_port()

        torProc, torConfFile = start_tor(socks_port)  # Torを起動

        driver, service, temp_dir = Func_SettingDriver_Chrome(socks_port,
                                                            groupName,
                                                            execute_driver = True,
                                                            TorEnable = True,
                                                            headless_options = headless_)

        return torProc, driver, service, temp_dir, torConfFile
    except Exception as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        return None
    
# setup_driverの戻りとこの関数の引数は合わせる→かならずセットで呼び出すのでわかりやすくするため
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
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

# torProc, driver, service, temp_dir, torConfFile = setup_driver('DataCarry')
# clear_driver(torProc, driver, service, temp_dir, torConfFile)

def getHtmlResponseByRequest(url, headers = None, verify=False, group_name=None):
    try:
        response = None

        socks_port = find_unused_port()
        reset_tor_port()
        torProc, torConfFile = start_tor(socks_port)  # Torを起動
        session = getSession(socks_port)
        logger_name = group_name or 'unknown'
        groupLogger.log(logger_name, 'getHtmlResponseByRequest', 'request_start', {
            'port': socks_port,
            'url': url,
            'headers': {
                'User-Agent': headers.get('User-Agent') if headers else None,
                'Accept': headers.get('Accept') if headers else None
            }
        })
        response = session.get(url, headers=headers, verify=False, timeout=30)

        if torProc:
            torProc.terminate()
            torProc.wait()  # プロセスが終了するのを待つ

        cleanup_torrc(torConfFile)
        logger_name = group_name or 'unknown'
        if response is None:
            groupLogger.log(logger_name, 'getHtmlResponseByRequest', 'no_response', {'port': socks_port, 'url': url})
        else:
            groupLogger.log(logger_name, 'getHtmlResponseByRequest', 'request_complete', {
                'port': socks_port,
                'status_code': getattr(response, 'status_code', None),
                'reason': getattr(response, 'reason', None),
                'url': url
            })
    except Exception as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

        logger_name = group_name or 'unknown'
        groupLogger.log(logger_name, 'getHtmlResponseByRequest', 'exception', {
            'error': str(e),
            'args': e.args
        })

    return response

def getHtmlResponseByRequest_Post(url, headers = None, requestData = None, verify=False):
    try:
        response = None

        socks_port = find_unused_port()
        reset_tor_port()
        torProc, torConfFile = start_tor(socks_port)  # Torを起動
        session = getSession(socks_port)

        # リクエストの送信
        response = session.post(
            url,
            headers=headers,
            # cookies=cookies,
            data=requestData,
            verify=False,
            timeout=30
        )
        if torProc:
            torProc.terminate()
            torProc.wait()  # プロセスが終了するのを待つ

        cleanup_torrc(torConfFile)
    except Exception as e:
        Log.Logging("System","{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return response


