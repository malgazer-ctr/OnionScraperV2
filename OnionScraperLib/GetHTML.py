# from concurrent.futures import thread
import os
from asyncio.windows_events import NULL
import sys
import time
import re
import cv2
import numpy as np
import base64
import math
import urllib
import urllib.parse
import requests
from requests_tor import RequestsTor
from urllib import parse
from urllib.parse import unquote

from pickle import NONE
# from selenium import webdriver
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from OnionScraperLib import Log
from OnionScraperLib import utilFuncs as uf
from Config import Config as cf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import SetupBrowser as sb
from OnionScraperLib import GenerativeAI as ga
from OnionScraperLib import GroupLogger as groupLogger

#スクリーンショット全体の何割を監視するか（0.5なら上から半分の領域だけを比較監視）
check_img_bunkatu = 0.5

def Func_FindElementByClassName(driver, className):
    #全要素に対して見つかるまで指定時間のwaitかます
    #retDriver.implicitly_wait(20)
 
    try:
        #ret = retDriver.find_element_by_class_name(className)
        ret = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
        #ret = WebDriverWait(retDriver, 20).until(EC.presence_of_element_located((By.ID, className))
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
        return None

    return ret

def Func_FindElementFlexibleByConditions(
    driver,
    className=None,
    tagName="*",  # 任意のタグ名、指定がなければ全タグ対象
    attributes=None,  # dict形式で { "data-index": "0" } のように指定
    contains_text=None,  # 要素内テキストを含むかどうか
    timeout=20
):
    try:
        # CSSセレクタ構築
        selector = tagName
        if className:
            selector += f".{className}"
        if attributes:
            for key, val in attributes.items():
                selector += f'[{key}="{val}"]'

        # 該当要素の取得
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
        )

        # テキストフィルタが指定されていれば一致確認
        for el in elements:
            try:
                if contains_text:
                    if contains_text in el.text:
                        return el
                else:
                    return el
            except Exception:
                continue

    except TimeoutException as e:
        Log.LoggingWithFormat('groupName', logCategory='E', logtext=f'Timeout: {str(e.args)}')
        return None
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory='E', logtext=f'Error: {str(e.args)}')
        return None

    return None


def Func_FindElementByCSSSelector(driver, selectorName):
    try:
        ret = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, selectorName)))
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
        return None

    return ret

def Func_FindElementById(driver, id, maxWait = 20):
    #全要素に対して見つかるまで指定時間のwaitかます
    #retDriver.implicitly_wait(20)
 
    try:
        ret = WebDriverWait(driver, maxWait).until(EC.presence_of_element_located((By.ID, id)))
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
        return None

    return ret

def Func_FindElementByTagName(driver, tag_name, maxWait=20):
    try:
        ret = WebDriverWait(driver, maxWait).until(
            EC.presence_of_element_located((By.TAG_NAME, tag_name))
        )
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory='E', logtext=f'{str(e.args)}')
        return None

    return ret

# 5秒単位でmaxWaitまで待機
def findElemtsByClassName(driver, className, maxWait = 30):
    ret = []
    if driver != None:
        sleepTime = 5
        count = maxWait // sleepTime
        for i in range(count):
            soup = BeautifulSoup(driver.page_source.encode('utf-8'), 'html.parser')
            ret = soup.find_all(class_=className)
            if len(ret) > 0:
                break

            time.sleep(sleepTime)

    return ret

def findElemtsById(driver, Id, maxWait = 30):
    ret = []
    if driver != None:
        sleepTime = 5
        count = maxWait // sleepTime
        for i in range(count):
            soup = BeautifulSoup(driver.page_source.encode('utf-8'), 'html.parser')
            ret = soup.find_all(id=Id)
            if len(ret) > 0:
                break

            time.sleep(sleepTime)

    return ret
def findElemtsByCssSelector(driver, selector, maxWait = 20):
    ret = []
    if driver != None:
        sleepTime = 5
        count = maxWait // sleepTime
        for i in range(count):
            soup = BeautifulSoup(driver.page_source.encode('utf-8'), 'html.parser')
            ret = soup.select_one(selector)
            if len(ret) > 0:
                break

            time.sleep(sleepTime)

    return ret

# WebDriverWaitの待機仕様がわからないので使わない。
# 返ってこないときある
def Func_FindElemtsByClassName(driver, className, maxWait = 20):
    try:
        ret = WebDriverWait(driver, maxWait).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
        return None

    return ret

def Func_IsVisibleElemtsByClassName(driver, className, maxWait = 20):
    try:
        ret = WebDriverWait(driver, maxWait).until(EC.visibility_of_element_located((By.CLASS_NAME, className)))
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
        return None

    return ret

def Func_FindElemtsByCssSelector(driver, selector, maxWait = 20):
    try:
        # ret = driver.find_element_by_css_selector(selector)
        ret = WebDriverWait(driver, maxWait).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')

        return None

    return ret

def Func_FindAllElemts(driver, maxWait = 20):
    try:
        ret = WebDriverWait(driver, maxWait).until(EC.presence_of_all_elements_located)
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
        return None

    return ret

def Func_IsVisibleAllElemts(driver, maxWait = 20):
    try:
        ret = WebDriverWait(driver, maxWait).until(EC.visibility_of_element_located)
    except:
        print(sys.exc_info())
        return None

    return ret    

# 待機用特殊処理
# Lockbit2.0などはDDOS対策でミラーリングされており、そちらが取れてしまうのでちゃんとした被害者リストが表示されるまで待機する
def _waitObject(driver, groupName):
    # とりあえず全ての要素が読み込まれるまで待機
    # これが待機成功してれば下の個別対応待機処理もすぐ抜けるはず
    Func_FindAllElemts(driver,180)
    Func_IsVisibleAllElemts(driver,180)

    # driver取得時、driver.implicitly_wait(180)をセットした→一回セットすればいいらしい
    if uf.strstr('LockBit', groupName) == True:
        Func_FindElemtsByClassName(driver, "post-title")
        Func_IsVisibleElemtsByClassName(driver, "post-title")
    elif uf.strstr('Hive', groupName) == True:
        Func_FindElemtsByClassName(driver, "blog-card-main")
        Func_IsVisibleElemtsByClassName(driver, "blog-card-main")
    elif uf.strstr('AlphV', groupName) == True:
        Func_FindElemtsByClassName(driver, "post")
        Func_IsVisibleElemtsByClassName(driver, "post")
    elif uf.strstr('Quantum', groupName) == True:
        Func_FindElemtsByClassName(driver, "blog-post-title")        
        Func_IsVisibleElemtsByClassName(driver, "blog-post-title")        
    elif uf.strstr('CHEERS', groupName) == True:
        Func_FindElemtsByClassName(driver, "main")        
        Func_IsVisibleElemtsByClassName(driver, "main")        
        Func_FindElemtsByClassName(driver, "excerpt-title")
        Func_IsVisibleElemtsByClassName(driver, "excerpt-title")
    # elif uf.strstr('BlackByte', groupName) == True:
    #     Func_FindElemtsByClassName(driver, "table table-bordered table-content ", 120)   
    #     Func_IsVisibleElemtsByClassName(driver, "table table-bordered table-content ", 120)   
    elif uf.strcmp('Everest', groupName) == True:
        Func_FindElementById(driver,'site-content', 60)
        # なぜか要素は存在するのに見つからず指定の時間でタイムアウトしてこなくて長時間待機してしまうのでコメント
        # Func_FindElemtsByClassName(driver, "entry-header has-text-align-center", 60)   
        # Func_IsVisibleElemtsByClassName(driver, "entry-header has-text-align-center", 60) 
    elif uf.strstr('Royal', groupName) == True:
        Func_FindElemtsByClassName(driver,'post', 120)
        Func_IsVisibleElemtsByClassName(driver,'post', 60)     
    elif uf.strstr('JUSTICE_BLADE', groupName) == True:
        Func_FindElementById(driver,'buySellHeading', 120)
           
    # else:
        # Driver取得時にimplicitly_waitを設定しているのでいったんコメント
        # 待ちきれないやついるからとりあえずSleepいれとく
        # time.sleep(180)

        # TODO:待機間隔短くしてbodyや特定のWordを探すとか

# ret
# -1:既定のSleepによる待機
# 0:指定されたオブジェクトが見つからない
# 1:指定されたオブジェクトが見つかった
def waitObject(driver, groupName):
    ret = cf.SUB_RETURNCODE_GETHTML_FAILED

    logLocation = ''
    try:
        groupInfoList = cf.getTargetLeakSite()

        if len(groupInfoList) > 0:
            logLocation = Log.Trace.execution_location()
            if groupName in groupInfoList.keys():
                item = groupInfoList[groupName]

                logLocation = Log.Trace.execution_location()

                # "ObjectForWait":{
                #     "Type": "Class",
                #     "Name":"page-wrapper"
                # }
                # 上記Jsonから指定されているオブジェクトを取得
                if 'ObjectForWait' in item:
                    type = item['ObjectForWait']['Type']
                    Name = item['ObjectForWait']['Name']
                    ExtraSleep = item['ObjectForWait'].get('ExtraSleep', 0)
                    
                    maxWait = 180
                    if 'MaxWait' in item['ObjectForWait']:
                        maxWait = item['ObjectForWait']['MaxWait']

                    ret = cf.SUB_RETURNCODE_GETHTML_NOTFINDOBJECT
                    object_ = None

                    logLocation = Log.Trace.execution_location()
                    if type == 'Class':
                        logLocation = Log.Trace.execution_location()
                        object_ = findElemtsByClassName(driver, Name, maxWait)

                        if object_ != None and len(object_) > 0:
                            logLocation = Log.Trace.execution_location()
                            ret = cf.SUB_RETURNCODE_GETHTML_FINDOBJECT
                        logLocation = Log.Trace.execution_location()
                    elif type == 'Id':
                        logLocation = Log.Trace.execution_location()
                        object_ = findElemtsById(driver, Name, maxWait)

                        if object_ != None and len(object_) > 0:
                            logLocation = Log.Trace.execution_location()
                            ret = cf.SUB_RETURNCODE_GETHTML_FINDOBJECT     
                        logLocation = Log.Trace.execution_location()                       
                    elif type == 'CssSelector':
                        logLocation = Log.Trace.execution_location()
                        object_ = findElemtsByCssSelector(driver, Name, maxWait)
    
                        if object_ != None and len(object_) > 0:
                            logLocation = Log.Trace.execution_location()
                            ret = cf.SUB_RETURNCODE_GETHTML_FINDOBJECT
                        logLocation = Log.Trace.execution_location()
                    else:
                        logLocation = Log.Trace.execution_location()
                        time.sleep(30)

                    if ExtraSleep > 0:
                        time.sleep(ExtraSleep)
                else:
                    logLocation = Log.Trace.execution_location()
                    time.sleep(30)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return ret

def ignorePrivacyError(ffDrive, groupName):
    try:
        # BlackBastaはプライバシー接続エラーでるのでクリックで回避
        if uf.strstr('Black_Basta', groupName):
            detailBtn = Func_FindElementById(ffDrive,'details-button', 5)
            if detailBtn != None:
                detailBtn.click()    

                forward = Func_FindElementById(ffDrive,'proceed-link', 5)
                if forward != None:
                    forward.click()
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

# Html取得できても以下文言が含まれる場合は無視する
def IsIgnoreAllTextText(groupName, str):
    try:
        ret = False

        ignoreWordsDic = fo.Func_ReadJson2Dict(cf.PATH_IGNOREWORD_LIST)
        # patternキーに配列として除外ワードの一覧が入っている
        ignorePatternList = ignoreWordsDic['pattern']

        for pattern in ignorePatternList:
            groupNames = pattern.get('groupNames', [])

            chkTarget = False
            # 特定のグループ専用かチェック
            if len(groupNames) > 0:
                for item in groupNames:
                    if uf.strcmp(item , groupName):
                        chkTarget = True
                        break
            else:
                # 特にグループ指定されてなければ全グループ対象
                chkTarget = True

            # チェック開始
            if chkTarget:
                isUseRegExp = pattern.get('regExp', False)
                wordArray = pattern.get('words', [])
            
                #　改行コードの配列にして一行ずつチェック
                lineArray = str.splitlines()

                # wordsに複数登録されている場合は全て見つからないと無視しちゃいけない
                for word in wordArray:
                    # 一行ずつチェック
                    for line in lineArray:
                        if isUseRegExp:
                            if re.match(word, line) != None:
                                ret = True
                                break
                        else:
                            if uf.strstr(word, line):
                                ret = True
                                break
                    # 各wordごとにチェックするので、全文検索して一つでもFalseのwordがあったら無視対象ではない
                    if ret == False:
                        break
                # ここをTrueで抜けてきたら無視対象なのでBreak
                if ret:
                    break

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return ret


def OperateBrowser(driver, groupName):
    import pyautogui
    try:

        if uf.strstr('BlackByte', groupName):
            close_button = driver.find_element(By.CLASS_NAME, "closes")
            if close_button:
                close_button.click()
        elif uf.strstr('AKIRA', groupName):
            elem = driver.find_element(By.CLASS_NAME, 'cmd-clipboard')

            if elem != None:
                elem.click()
                time.sleep(10)
                elem.send_keys('leaks')
                time.sleep(10)
                elem.send_keys(Keys.ENTER)
                time.sleep(10)
                elem.send_keys('news')
                time.sleep(10)
                elem.send_keys(Keys.ENTER)
                time.sleep(10)

        elif uf.strstr('Kawa4096', groupName):
            elem = driver.find_element(By.ID, "terminal-command")

            if elem != None:
                elem.click()
                time.sleep(5)
                elem.send_keys('leaks')
                time.sleep(5)
                elem.send_keys(Keys.ENTER)
                time.sleep(1)

        elif uf.strstr('VanirGroup', groupName):
            elem = driver.find_element(By.CLASS_NAME, 'incorrect-command')

            if elem != None:
                elem.click()
                time.sleep(10)
                elem.send_keys('victims')
                time.sleep(5)
                elem.send_keys(Keys.ENTER)
                time.sleep(5)

        elif uf.strstr('HANDARA', groupName):
            # elem = driver.find_element(By.CLASS_NAME, 'cf-btn cf-btn-danger')
            elem = driver.find_element(By.TAG_NAME, "button")

            if elem != None:
                elem.click()
                time.sleep(5)

        # elif uf.strstr('Snatch', groupName):
        elif uf.strstr('Snatch', groupName):
            # #指定したdriverに対して最大で10秒間待つように設定する
            # wait = WebDriverWait(driver, 10)
            # #指定したボタンが表示されクリック出来る状態になるまで待機する
            # wait.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "ctp-checkbox-label")))
            # elem = driver.find_element(By.XPATH, "//*[@id=""challenge-stage""]/div/label/input")

            # elem = driver.find_element(By.CLASS_NAME, 'ctp-checkbox-label')
            # if elem != None:
            #     elem.click()

            # 小手先。画像をクリックするので最前面にしたい。
            driver.minimize_window()
            time.sleep(3)
            driver.maximize_window()
            pyautogui.click(r'E:\MonitorSystem\Source\OnionScraperV2\Config\ClickTarget\SiteSaftyCheck.PNG')

            # from seleniumbase import page_actions
            # page_actions.click(driver, "#challenge-stage > div > label > input[type=checkbox]")

        elif uf.strstr('Crazy Hunter Team', groupName):
            elems = driver.find_elements(By.TAG_NAME, "button")

            if elems:
                for elem in elems:
                    try:
                        if elem.text and elem.text.lower() == 'confirm':
                            elem.click()
                            time.sleep(5)
                            break
                    except:
                        continue
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')


def wrap_waitImageLoadComplete(groupName, driver):
    ret = False
    try:
        cnt = 1
        retryCnt = 10    
        for cnt in range(retryCnt):
            ret = waitImageLoadComplete(groupName, driver)

            if ret:
                break
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return ret

# 現状個別対応したサイトの詳細ページのスクショ用
def goTargetUrl(driver, url, groupName):
    try:
        if driver != None:
            driver.maximize_window()
            # driver.set_page_load_timeout(600)
            driver.get(url)

            # 待機用
            if uf.strstr('NoEscape', groupName):
                findElemtsByClassName(driver, "display-6 mb-1 lh-1")
            elif uf.strstr('LockBit3.0', groupName):
                findElemtsByClassName(driver, "desc")
            elif uf.strstr('Mallox', groupName):
                findElemtsByClassName(driver, "card-body")
            elif uf.strstr('MedusaBlog', groupName):
                findElemtsByClassName(driver, "card-body")
            elif uf.strstr('HUNTERS_INTERNATIONAL', groupName):
                findElemtsByClassName(driver, "details ng-star-inserted")
            else:
                time.sleep(3)

    except Exception as e:
        error_text = str(e)
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'error:{error_text}')
        groupLogger.log(groupName, 'Func_scraping_AKIRA_error', 'exception during AKIRA scraping', {
            'error': error_text,
            'args': e.args
        })

def wrap_getURL(driver, url, groupName):
    try:
        driver.set_page_load_timeout(600)
        driver.get(url)

        # Snatchのサイトで「サイトの安全性を確認しています」がでてしまうので
        OperateBrowser(driver, groupName)
        
        # # Seleniumで開いたページのURLを取得
        # curUrl = driver.current_url
        # # requestsを使用してHTTPステータスコードを取得
        # rt = RequestsTor(tor_ports=(9050,), tor_cport=9051)
        # response = rt.get(curUrl)

        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'get(url) 終了', note = '')

        # SUB_RETURNCODE_GETHTML_NOTFINDOBJECT の時は一応リトライかましてみる
        # 構造変更時は時間無駄になるが、HIVEとか読み込み遅い奴は救えるかもしれない
        cnt = 1
        retryCnt = 3
        for cnt in range(retryCnt):
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'waitObject 直前 Title:{driver.title} CurrentUrl:{driver.current_url}', note = '')

            retCode = waitObject(driver, groupName)

            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'waitObject 終了', note = '')

            if retCode != cf.SUB_RETURNCODE_GETHTML_NOTFINDOBJECT:
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'waitObject 成功', note = '')

                break
            else:
                driver.refresh()
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'waitObject 失敗 get(url)のリトライ {str(cnt)}回目', note = '')

        # テンプレートマッチングによる待機処理
        # 待機処理の精度をあげるだけなので戻りは見ない
        wrap_waitImageLoadComplete(groupName, driver)
 
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

def clearCaptha(groupName, driver, soup, url):
    ret = soup

    def saveCAPTCHAImage(groupName, pngData):
        try:
            timeStr = uf.getDateTime('%Y%m%d%H%M')
            filePath = os.path.join(cf.PATH_CAPTCHAIMG_DIR, f'{groupName}_CAPTCHA_{timeStr}.png')
            with open(filePath, 'wb') as file:
                file.write(pngData)

            return filePath
        except Exception as e:
            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    try:        
        if uf.strstr(groupName, 'MedusaBlog'):
            ret = _solve_medusa_captcha(groupName, driver, soup, saveCAPTCHAImage)

        elif uf.strstr(groupName, 'LockBit3.0_2024_1') or \
            uf.strstr(groupName, 'LockBit3.0_2024_2') or \
            uf.strstr(groupName, 'LockBit3.0_2024_6') or \
            uf.strstr(groupName, 'LockBit3.0_2024_4'):
            ret = _solve_lockbit2024_captcha(groupName, driver, soup, saveCAPTCHAImage)

        # elif uf.strcmp(groupName, 'Lockbit5.0'):
        #     ret = _solve_lockbit5_captcha(groupName, driver, soup, saveCAPTCHAImage)

        elif uf.strstr(groupName, 'CHORT'):
            ret = _solve_chort_captcha(groupName, driver, soup, saveCAPTCHAImage)
        elif uf.strstr(groupName, 'RALord'):
            ret = _solve_ralord_captcha(groupName, driver, soup, saveCAPTCHAImage)


        elif uf.strstr(groupName, 'ransomhub') or uf.strstr(groupName, 'DragonForce'):
            ret = _solve_ransomhub_dragonforce_captcha(groupName, driver, soup, saveCAPTCHAImage)

        elif uf.strstr(groupName, 'ThreeAM'):
            ret = _solve_threeam_captcha(groupName, driver, soup, saveCAPTCHAImage)
        elif uf.strstr(groupName, 'Kyber'):
            ret = _solve_kyber_captcha(groupName, driver, soup, saveCAPTCHAImage)
        elif uf.strstr(groupName, 'RustyLocker'):
            ret = _solve_RustyLocker_captcha(groupName, driver, soup, saveCAPTCHAImage)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    # 応急処置：CAPTHCAがなくなったりした場合、
    if not ret:
        ret = soup
    return ret


def _solve_medusa_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    # imgタグを探してsrc属性を取得
    img_tag = soup.find('img', {'id': 'captcha-image'})
    src_value = img_tag['src'] if img_tag else None

    if src_value:
        time.sleep(10)
        pngData = Func_FindElementByClassName(driver, 'captcha-image-wrapper').screenshot_as_png

        if pngData:
            # 中のテキストが表示されるまで時間がかかる
            filePath = saveCAPTCHAImage(groupName, pngData)

            captchaTxt = ga.request_openai_vision_latest(image_path = filePath)

            # MedusaはCAPTCHAのテキストに数字はいらないのでチェック
            captchaTxt = captchaTxt.lower()
            if bool(re.search(r'\d', captchaTxt)) == False:
                captcha_input = driver.find_element(By.NAME, 'captcha')
                if captcha_input:
                    captcha_input.send_keys(captchaTxt)

                    verifyBtn = driver.find_element(By.CLASS_NAME, 'captcha-card-button')
                    # verifyBtn = Func_FindElementByClassName(driver,'btn btn-primary captcha-card-button')
                    if verifyBtn != None:
                        verifyBtn.click()

                        Func_FindElementByClassName(driver, 'card-title')

                        html = driver.page_source.encode('utf-8')
                        newSoup = BeautifulSoup(html, 'html.parser')

                        if newSoup:
                            if newSoup.title.text != 'Human Verify':
                                # 成功してればCAPTCHAは抜けるので見つからない
                                ret = newSoup
                                fo.Func_DeleteFile(filePath)
    return ret


def _save_base64_background_image(element, groupName, saveCAPTCHAImage):
    filePath = ''
    try:
        styleValue = element.get_attribute('style') or ''
        match = re.search(r'data:image/[^;]+;base64,([^"\)]+)', styleValue)
        if not match:
            return ''

        rawData = base64.b64decode(match.group(1))
        np_arr = np.frombuffer(rawData, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return ''

        success, buffer = cv2.imencode('.png', img)
        if not success:
            return ''

        filePath = saveCAPTCHAImage(groupName, buffer.tobytes())
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'base64 decode error:{str(e.args)}')

    return filePath


def _calc_css_calc_value(expr):
    try:
        work = expr.strip()
        if work.startswith('calc'):
            work = work[4:].strip()
        if work.startswith('(') and work.endswith(')'):
            work = work[1:-1]
        work = work.replace('px', '')
        work = work.replace('deg', '')
        work = work.replace('-', '+-')
        parts = [item.strip() for item in work.split('+') if item.strip() != '']
        total = 0.0
        for item in parts:
            total += float(item)
        return total
    except Exception:
        return None


def _parse_background_position_values(valueStr):
    try:
        if not valueStr:
            return None

        calcList = re.findall(r'calc\([^)]*\)', valueStr)
        values = []
        if len(calcList) >= 2:
            values = calcList[:2]
        else:
            temp = valueStr.split()
            if len(temp) >= 2:
                values = temp[:2]

        if len(values) < 2:
            return None

        def _to_float(item):
            item = item.strip()
            if item.startswith('calc'):
                return _calc_css_calc_value(item)
            if item.endswith('px'):
                item = item[:-2]
            return float(item)

        x_val = _to_float(values[0])
        y_val = _to_float(values[1])
        if x_val is None or y_val is None:
            return None

        return (x_val, y_val)
    except Exception:
        return None


def _extract_background_position(styleValue):
    try:
        if not styleValue:
            return None

        if 'background-position' not in styleValue:
            return _parse_background_position_values(styleValue)

        match = re.search(r'background-position\s*:\s*([^;]+)', styleValue)
        if not match:
            return None

        rawValue = match.group(1).strip()
        return _parse_background_position_values(rawValue)
    except Exception:
        return None


def _get_css_rule_values(driver, selector, properties):
    try:
        if not selector or not properties:
            return {}

        script = """
        const selector = arguments[0];
        const props = arguments[1];
        const result = {};
        for (const sheet of document.styleSheets) {
            let rules;
            try {
                rules = sheet.cssRules;
            } catch (err) {
                continue;
            }
            if (!rules) {
                continue;
            }
            for (const rule of rules) {
                if (rule.selectorText === selector) {
                    for (const prop of props) {
                        result[prop] = rule.style.getPropertyValue(prop) || '';
                    }
                    return result;
                }
            }
        }
        return result;
        """
        return driver.execute_script(script, selector, properties)
    except Exception:
        return {}


def _extract_rotation_angle(styleValue):
    try:
        if not styleValue:
            return None

        matrixMatch = re.search(r'matrix\(([^,]+),([^,]+),([^,]+),([^,]+),', styleValue)
        if matrixMatch:
            a = float(matrixMatch.group(1))
            b = float(matrixMatch.group(2))
            angle = math.degrees(math.atan2(b, a))
            return angle

        key = 'rotate('
        start = styleValue.find(key)
        if start == -1:
            return None

        idx = start + len(key)
        depth = 1
        end = idx
        while end < len(styleValue) and depth > 0:
            if styleValue[end] == '(':
                depth += 1
            elif styleValue[end] == ')':
                depth -= 1
            end += 1

        if depth != 0:
            return None

        content = styleValue[idx:end-1]
        return _calc_css_calc_value(content)
    except Exception:
        return None


def _solve_lockbit2024_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    for i in range(3):
        # CAPTCHAじゃなく本物に接続できるケースがあるので
        if uf.strstr('LockBit BLOG', driver.title):
            ret = soup
            break

        time.sleep(10)
        # imgタグを探してsrc属性を取得
        # img_tag = soup.find('img', {'class': 'captcha__image'})
        # src_value = img_tag['src'] if img_tag else None
        pngData = Func_FindElementByClassName(driver, 'captcha__image').screenshot_as_png

        if pngData:
            filePath = saveCAPTCHAImage(groupName, pngData)

            promptText = 'この画像には英数字が６文字書いてあります。なんと書いてありますか？英数字として読み取れる文字だけ教えてください。\
                            回答に際は必ず「文字列:なんと書いてあるか」のように回答してください。\
                            これ以外の回答は不要です。'
            captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)

            captcha_input = driver.find_element(By.NAME, 'captcha')
            if captcha_input:
                captcha_input.send_keys(captchaTxt)

                # verifyBtn = driver.find_element(By.CLASS_NAME, 'captcha-card-button')
                verifyBtns = Func_FindElemtsByCssSelector(driver, "button[type='submit']")
                if verifyBtns:
                    verifyBtns[0].click()

                    time.sleep(10)

                    html = driver.page_source.encode('utf-8')
                    newSoup = BeautifulSoup(html, 'html.parser')

                    title = newSoup.title.string
                    if title:
                        if not uf.strstr('Humanity check', title):
                            ret = newSoup
                            fo.Func_DeleteFile(filePath)
                            break
                        # errorText = 'The entered code does not match the image!'
                        else:
                            refreshButton = Func_FindElementByClassName(driver, 'captcha__refresh')
                            if refreshButton:
                                refreshButton.click()
    return ret


def _solve_lockbit5_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    target_title = 'LockBit 5.0 Blog'
    # promptText = 'この画像には英数字が1文字だけ描かれています。最も目立つその1文字のみを回答してください。余計な言葉や記号は書かないでください。'

    for i in range(3):
        try:
            inputs = driver.find_elements(By.CLASS_NAME, 'ch')
            if len(inputs) < 6:
                continue
            
            imageElem = Func_FindElementByClassName(driver, 'image')
            if not imageElem:
                continue

            filePath = _save_base64_background_image(imageElem, groupName, saveCAPTCHAImage)
            # filePath = saveCAPTCHAImage(groupName, imageElem.screenshot_as_png)

            if not filePath:
                continue
            
            solved = True
            for input_box in inputs[:6]:
                try:
                    driver.execute_script("arguments[0].focus();", input_box)
                    input_box.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", input_box)

                # time.sleep(1)
                styleValue = imageElem.get_attribute('style') or ''
                positionValue = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).getPropertyValue('background-position');",
                    imageElem
                )
                transformValue = driver.execute_script(
                    "const style = window.getComputedStyle(arguments[0]);"
                    "return style.getPropertyValue('transform') || style.getPropertyValue('-webkit-transform') || '';",
                    imageElem
                )

                # position = _extract_background_position(positionValue)
                # rotation = _extract_rotation_angle(transformValue)

                # if not position:
                #     position = _extract_background_position(styleValue)

                # if rotation is None and styleValue:
                #     rotation = _extract_rotation_angle(styleValue)

                # if position:
                #     Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'Lockbit5 background-position: X={position[0]:.2f}px Y={position[1]:.2f}px')
                # if rotation is not None:
                #     direction = 'right' if rotation > 0 else ('left' if rotation < 0 else 'none')
                #     Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'Lockbit5 rotation: {rotation:.2f}deg ({direction})')

                promptText = [
                    f'この画像には英数字書かれています。この中から',
                    # f'X座標{str(position[0])}/Y座標{str(position[1])}の配置で',
                    f'座標{str(positionValue)}の配置で',
                    f'{transformValue}という拡大、回転ルールに基づいて配置されている',
                    f'1文字を読み取り回答してください。余計な言葉や記号は書かないでください。'
                ]

                captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)
                cleaned = ''.join(re.findall(r'[A-Za-z0-9]', captchaTxt))

                if not cleaned:
                    solved = False
                    break

                input_box.clear()
                input_box.send_keys(cleaned[0])

            fo.Func_DeleteFile(filePath)

            if solved is False:
                driver.refresh()
                continue

            submitBtn = Func_FindElementByClassName(driver, 'before')
            if submitBtn:
                submitBtn.click()

                start = time.time()
                while time.time() - start <= 180:
                    if uf.strstr(target_title, driver.title):
                        html = driver.page_source.encode('utf-8')
                        ret = BeautifulSoup(html, 'html.parser')
                        return ret
                    time.sleep(3)

            driver.refresh()
        except Exception as e:
            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
            driver.refresh()

    return ret


def _solve_chort_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    for i in range(3):
        time.sleep(10)
        # imgタグを探してsrc属性を取得
        img_tag = soup.find('img')
        # src_value = img_tag['src'] if img_tag else None
        pngData = Func_FindElementByCSSSelector(driver, "img[alt='Chort']").screenshot_as_png

        if pngData:
            filePath = saveCAPTCHAImage(groupName, pngData)

            promptText = 'この画像には４つの文字書いてあります。なんと書いてありますか？英数字として読み取れる文字だけ教えてください。\
                            回答に際は必ず「文字列:なんと書いてあるか」のように回答してください。\
                            これ以外の回答は不要です。'
            captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)

            captcha_input = driver.find_element(By.CLASS_NAME, 'form-control')
            if captcha_input:
                captcha_input.send_keys(captchaTxt)
                verifyBtns = Func_FindElemtsByCssSelector(driver, "button.btn.btn-primary.btn-lg[name='Submit']")
                
                if verifyBtns:
                    verifyBtns[0].click()

                    time.sleep(10)

                    html = driver.page_source.encode('utf-8')
                    newSoup = BeautifulSoup(html, 'html.parser')

                    title = newSoup.title.string
                    if title:
                        if uf.strstr('CHORT', title):
                            ret = newSoup
                            fo.Func_DeleteFile(filePath)
                            break
                    
                    driver.refresh()
    return ret


def _solve_ralord_captcha(groupName, driver, soup, saveCAPTCHAImage):
    #  or uf.strstr(groupName, 'Nova'
    ret = None
    # 失敗したらリトライ
    for i in range(3):
        clearCaptha = False

        time.sleep(60)
        while not clearCaptha:
            # 2025/6時点の新しいCAPTHCAは多段式で、
            # クイズが三回、XORの計算が一回、簡単な計算が一回あるので、それぞれをクリアする必要がある
            # ただし、クイズに三回失敗するとWikiに飛ばされるのでリロードする
            promptText = '''画像には、Linuxに関連するクイズが記載されています。
            クイズには、回答を候補から選択する問題と、そうでないものがあります。
            ・選択問題ではないとき
            クイズの内容を読み取り、その回答のみ教えてください。コピーしてそのまま貼り付けることで回答したいです。
            ・選択問題の時
            質問の回答を三つから選択肢、上から何番目が正しい回答か教えてください。
            解答するときは、一番上を「0」として、２番目が「1」、３番目が「2」のような番号で回答を教えてください。数字以外の回答は不要です。

            注意事項)クイズの内容が読み取れない場合や、回答が不明な場合は「不明」とだけ解答してください。'''
            # promptText = 'この画像には計算式が書かれています。この計算の結果を回答してください。\
            #             回答の際は必ず計算式の結果となる数字のみを回答し、数字以外は一切回答に含めないでください。'
            # pngData = Func_FindElementByClassName(driver, "ctf-challenge").screenshot_as_png
            linuxChallenge = None
            cryptoChallenge = None
            securityVerification = None
            filePath = ''

            linuxChallenge = Func_FindElementById(driver, "linuxChallenge")
            if linuxChallenge and linuxChallenge.is_displayed():
                    filePath = saveCAPTCHAImage(groupName, linuxChallenge.screenshot_as_png)
            else:
                linuxChallenge = None
                cryptoChallenge = Func_FindElementFlexibleByConditions(driver, className = 'xor-instruction')
                if not cryptoChallenge:
                    cryptoChallenge = None
                    securityVerification = Func_FindElementById(driver, "captchaQuestion")
      
            if not linuxChallenge and not cryptoChallenge and not securityVerification:
                driver.refresh()
                break

            # このテキストなら三択問題
            if linuxChallenge:
                elem = Func_FindElementFlexibleByConditions(driver, className = 'attempts')
                if elem:
                    # 試行回数の残りが0になったら間違えすぎなのでリロード
                    if uf.strstr('Attempts left: 1', elem.text):
                        break

                # captcha_input = driver.find_element(By.ID, 'captchaInput')
                captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)
                fo.Func_DeleteFile(filePath)

                verifyBtns = Func_FindElementFlexibleByConditions(driver, className = 'option', attributes={"data-index": captchaTxt})
                if verifyBtns:
                    verifyBtns.click()
            elif cryptoChallenge:
                captcha_input = Func_FindElementFlexibleByConditions(driver, className = 'crypto-input')
                if captcha_input:
                    texts = cryptoChallenge.text.split('\n')
                    hex1 = texts[1]
                    hex2 = texts[2]
                    def xor_hex_strings(hex1, hex2):
                        # 16進文字列を整数に変換
                        int1 = int(hex1, 16)
                        int2 = int(hex2, 16)

                        # XOR演算を実行
                        result = int1 ^ int2

                        # 結果を16進数文字列に変換（"0x" 付き）
                        return hex(result)
                    captchaTxt = xor_hex_strings(hex1, hex2)

                    captcha_input.send_keys(captchaTxt)
                    time.sleep(3)
                    captcha_input.send_keys(Keys.ENTER)
                    
            elif securityVerification:
                promptText = f'{securityVerification.text}の計算の結果を回答してください。\
                            回答の際は必ず計算式の結果となる値のみを回答し、数字以外は一切回答に含めないでください。'
                isSuccess, captchaTxt = ga.request_ChatGPT_latest(promptText = promptText)
                if captchaTxt:
                    captcha_input = Func_FindElementById(driver, "captchaInput")
                    if captcha_input:
                        captcha_input.send_keys(captchaTxt)
                
                        verifyBtns = Func_FindElementByClassName(driver, "captcha-submit")
                        if verifyBtns:
                            verifyBtns.click()
                            time.sleep(10)
                            html = driver.page_source.encode('utf-8')
                            newSoup = BeautifulSoup(html, 'html.parser')
                            if uf.strstr( 'Nova GBlog', newSoup):
                                clearCaptha = True
                                ret = newSoup
                                break
                            else:
                                driver.refresh()
                                break
            else:
                break

        if clearCaptha:
            break
    return ret


def _solve_ransomhub_dragonforce_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    captchaTitle = 'RansomHub | Challenge'
    if uf.strstr(groupName, 'DragonForce'):
     captchaTitle = 'DragonForce | Challenge'

    for i in range(3):
        time.sleep(3)

        try:
            # 入力用のボックス
            elements = driver.find_elements(By.CLASS_NAME, 'ch')  
            for element in elements:
                # 入力ボックスにカーソルを合わせてCAPTCHA画像を表示させる
                element.click()
                time.sleep(1)
                # 文字が一つずつ表示されるので、まず一つ目の文字をとる
                pngData = Func_FindElementByClassName(driver, "lense").screenshot_as_png

                if pngData:
                    filePath = saveCAPTCHAImage(groupName, pngData)

                    promptText = 'この画像には文字が様々な背景画像の上に、英数字が一文字だけ描かれています。\
                                一番目立つ文字を回答してください。回答は必ず読み取った一文字のみとし、余計な言葉は回答しないでください。'
                    captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)

                    if captchaTxt:
                        element.send_keys(captchaTxt)
                    fo.Func_DeleteFile(filePath)

            # SUBMITボタン
            submitBtn = Func_FindElementByClassName(driver, "before")
            if submitBtn:
                submitBtn.click()
                time.sleep(1)

                html = driver.page_source.encode('utf-8')
                newSoup = BeautifulSoup(html, 'html.parser')
                if newSoup.title.string != captchaTitle:
                    ret = newSoup
                    break
            else:
                break
        except Exception as e:
            driver.refresh()
            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    return ret


def _solve_threeam_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    for i in range(3):
        time.sleep(5)
        # imgタグを探してsrc属性を取得
        # pngData = Func_FindElementById(driver, "captchaQuestion").screenshot_as_png
        pngData = Func_FindElementByTagName(driver, 'img', maxWait=20).screenshot_as_png

        if pngData:
            filePath = saveCAPTCHAImage(groupName, pngData)

            promptText = '''この画像には、時計が描かれています。
                            白い針が短針で"時"表し、赤い針が長針で"分"を表します。そして"分"はかならず0起源で、5分刻みの時刻を表しています。
                            この画像が何時何分を示しているか、12時間表記で回答してください。
                            この回答はシンプルに数字をカンマ区切りで回答を行い、余計な文字は一切回答しないでください。
                            例：10,5'''
            captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)

            def parse_time_string(time_str):
                """
                "H,M" 形式の文字列を解析し、(hour, minute) を整数で返す。
                フォーマットが不正な場合や範囲外の場合は (-1, -1) を返す。
                """
                try:
                    # 正規表現で "数字,数字" 形式かを検証
                    if not re.fullmatch(r'\d{1,2},\d{1,2}', time_str):
                        raise ValueError("形式エラー")

                    hour_str, minute_str = time_str.split(',')
                    hour = int(hour_str)
                    minute = int(minute_str)

                    # 範囲チェック（12時間表記）
                    if not (1 <= hour <= 12):
                        raise ValueError("時の範囲エラー")
                    if not (0 <= minute <= 59):
                        raise ValueError("分の範囲エラー")

                    return hour, minute

                except ValueError:
                    return -1, -1
                
            hour, minute = parse_time_string(captchaTxt)

            # captcha_input = driver.find_element(By.ID, 'captchaInput')
            captcha_input_Hour = Func_FindElementById(driver, "hour")
            captcha_input_minute = Func_FindElementById(driver, "minute")

            if (hour >= 0) and (captcha_input_Hour and captcha_input_minute):
                captcha_input_Hour.send_keys(str(hour))
                captcha_input_minute.send_keys(str(minute))
                # verifyBtns = Func_FindElementByClassName(driver, "btn btn-primary")
                verifyBtns = Func_FindElementByTagName(driver, 'button', maxWait=20)

                if verifyBtns:
                    verifyBtns.click()

                    time.sleep(3)

                    html = driver.page_source.encode('utf-8')
                    newSoup = BeautifulSoup(html, 'html.parser')
                    elem = newSoup.find('h2')
                    if elem:
                        text = elem.get_text().strip()
                        if text != 'What time does the clock show?':
                            ret = newSoup
                            break
            fo.Func_DeleteFile(filePath)
                    
        driver.refresh()
    return ret


def _solve_kyber_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    for i in range(3):
        time.sleep(5)
        # imgタグを探してsrc属性を取得
        # pngData = Func_FindElementById(driver, "captchaQuestion").screenshot_as_png
        pngData = Func_FindElementByTagName(driver, 'img', maxWait=20).screenshot_as_png

        if pngData:
            filePath = saveCAPTCHAImage(groupName, pngData)

            promptText = '''この画像描かれている英数字を教えてください。英文字は大文字です。描かれている文字のみ回答し、その他の言葉を一切回答に含めないでください。'''
            captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)

            captcha_input = driver.find_element(By.CLASS_NAME, 'captcha-input')
            if captcha_input:
                captcha_input.send_keys(captchaTxt)
                verifyBtn = Func_FindElemtsByClassName(driver, "submit-btn")
                
                if verifyBtn:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", verifyBtn)

                    # クリック可能になるまで“待つ”（存在=presenceではなく）
                    from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, TimeoutException
                    try:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, verifyBtn.get_attribute("id") or "submit")))
                        # 通常クリック
                        verifyBtn.click()
                    except (ElementClickInterceptedException, ElementNotInteractableException, TimeoutException):
                        # 最後の砦：JSクリック
                        driver.execute_script("arguments[0].click();", verifyBtn)
                    time.sleep(30)

                    html = driver.page_source.encode('utf-8')
                    newSoup = BeautifulSoup(html, 'html.parser')

                    title = newSoup.title.string
                    if title:
                        if uf.strstr('Blog', title):
                            ret = newSoup
                            fo.Func_DeleteFile(filePath)
                            break
                    
                    driver.refresh()
    return ret


def _solve_RustyLocker_captcha(groupName, driver, soup, saveCAPTCHAImage):
    ret = None
    for i in range(3):
        time.sleep(10)
        pngData = Func_FindElementByClassName(driver, 'captcha-image').screenshot_as_png

        if pngData:
            filePath = saveCAPTCHAImage(groupName, pngData)

            promptText = (
                'この画像には英数字が5文字書いてあります。'
                '英数字として読み取れる文字だけ教えてください。'
                '回答は必ず「文字列:なんと書いてあるか」のように回答してください。これ以外の回答は不要です。'
            )
            captchaTxt = ga.request_openai_vision_latest(prompt_text = promptText, image_path = filePath)

            if len(captchaTxt) > 5:
                continue
            captcha_input = driver.find_element(By.NAME, 'captcha_input')
            if captcha_input:
                captcha_input.send_keys(captchaTxt)

                # verifyBtn = driver.find_element(By.CLASS_NAME, 'btn btn-soft-primary')
                verifyBtn = driver.find_element(By.TAG_NAME, 'button')
                # verifyBtn = Func_FindElementByClassName(driver, 'btn btn-soft-primary')
                if verifyBtn:
                    verifyBtn.click()

                    time.sleep(5)

                    html = driver.page_source.encode('utf-8')
                    newSoup = BeautifulSoup(html, 'html.parser')

                    title = newSoup.title.string
                    if title:
                        if not uf.strstr('Security Verification', title):
                            ret = newSoup
                            fo.Func_DeleteFile(filePath)
                            break
                        # errorText = 'The entered code does not match the image!'
                        # else:
                        #     refreshButton = Func_FindElementByClassName(driver, 'captcha__refresh')
                        #     if refreshButton:
                        #         refreshButton.click()
    return ret

#   戻り値：取得したテキストを返す → 戻りとしては使わない。成否判定くらい
def getHTMLData(driver, url, groupName, excludeIgnoreText = False, groupConfig = {}):
    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLData Start')

    try:
        retHTML = ''
        retOuterHtmlText = ''
        retVictms = {}
        retCode = cf.SUB_RETURNCODE_ERR
        IsIndivisialScrapingTarget = False

        # リークサイトダウンのための情報集め用ログ
        debugAccessLogData = cf.accessLog.copy()
        debugAccessLogData = {}
        debugAccessLogData['groupName'] = groupName
        debugAccessLogData['getHTMLStatus'] = '初期化中'

        if driver != None:
            debugAccessLogData['accessStartTime'] = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)
            
            wrap_getURL(driver, url, groupName)
            
            debugAccessLogData['accessEndTime'] = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)

            # Anti DDOSページ対策
            if uf.strstr('cicada', groupName.lower()):
                time.sleep(60)
            # elif uf.strstr('Nova', groupName.lower()):
            #     time.sleep(10)
                
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            soup = clearCaptha(groupName, driver, soup, url)

            specialSurveillance = groupConfig.get('specialSurveillance', False)
            specifiedObjects = groupConfig.get('specifiedObjects', {})
            # 特別監視対象で、かつ特定のオブジェクトを指定されている場合はそのオブジェクト以下のテキストのみ取得して差分検知に使う
            if specialSurveillance and len(specifiedObjects):
                try:
                    allText = []
                    for specifiedObject in specifiedObjects:
                        type_ = specifiedObject['type']
                        value_ = specifiedObject['Value']

                        if type_.lower() == 'class': 
                            elem = soup.find(class_=value_)
                        elif type_.lower() == 'id': 
                            elem = soup.find(id=value_)
                        else:
                            elem = None
                        
                        if elem:
                            allText.append(getTextAll(groupName, elem))
                    
                    if len(allText):
                        retHTML="\n".join(allText)
                except:
                    Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
                    retHTML = ''

            # 通常監視、もしくは上の特別監視用処理でこけたら最悪こっち
            if retHTML == '':
                # get_textでまんま取得すると改行なしの長文になって取得されてしまうサイトがある(Royalなど)
                # なのでタグ要素からテキストを一つずつ抜き出して改行で連結するように変更
                allTag = soup.body.find_all(True)
                retOuterHtmlText = soup.prettify()

                allText = []

                if soup.title and soup.title.text:
                    allText.append(soup.title.text)
                for iContent in allTag:
                    contentsCnt = len(iContent.contents)
                    if contentsCnt > 0:
                        for i in range(contentsCnt):
                            if type(iContent.contents[i]) is NavigableString:
                                text = iContent.contents[i].text
                                if len(text) > 0:
                                    text2 = text.strip().replace('\xa0', ' ')

                                    if len(text2) > 0:
                                        allText.append(text2)

                retHTML="\n".join(allText)

                if len(retHTML) > 0:
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'HTML取得 成功')

                    if excludeIgnoreText == False and IsIgnoreAllTextText(groupName, retHTML) == True:
                        debugAccessLogData['htmlBodyText'] = retHTML
                        retCode |= cf.SUB_RETURNCODE_GETHTML_IGNORE
                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'htmlText:{retHTML}')
                        retHTML = ''
                    else:
                        retryCnt = 0
                        #Huntesrなど読み込み完了してないケースもありうるので個別取得対象なのに情報とれてないならリピートしてみる
                        while True:
                            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'wrap_Func_scraping:{str(retryCnt+1)}回目')
                            retVictms, IsIndivisialScrapingTarget = wrap_Func_scraping(driver, soup, groupName, url)
                            if IsIndivisialScrapingTarget == False:
                                break
                            else:
                                if len(retVictms):
                                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'個別対応情報取得 成功')
                                    break
                                elif retryCnt >= 3:
                                    break
                                
                            time.sleep(5)
                            retryCnt += 1

            if retHTML != '':
                retCode |= cf.SUB_RETURNCODE_GETHTML
                if IsIndivisialScrapingTarget:
                    if len(retVictms):
                        retCode |= cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_SUCCESS
                    else:
                        retCode |= cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED

                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLData 成功')
            else:
                retCode |= cf.SUB_RETURNCODE_GETHTML_FAILED
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLData 失敗')
        else:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'ドライバ取得できてない')

    except Exception as e:
        retCode |= cf.SUB_RETURNCODE_GETHTML_FAILED
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLData End')


    if debugAccessLogData.get('htmlBodyText', '') != '':
        debugAccessLogData['getHTMLStatus'] = Log.getHtmlStatus(retCode)

        logPath = Log.getAccessLogPath(groupName, f'Debug_{groupName}', extraSubDir = 'DebugLog')
        debugAccessLogStruct = Log.readAccessLogStruct(groupName, logPath)
        debugAccessLogStruct['log'] = Log.mergeAccessLogDataList(debugAccessLogData, logPath)
        Log.saveAccessLog2File(groupName, debugAccessLogStruct, logPath)

    return retOuterHtmlText, retHTML, retVictms, IsIndivisialScrapingTarget, retCode

g_driverforisLoadedAllImages = None
# JavaScriptIsLoadedAllImagesCall = "return isLoadedAllImages();"
JavaScriptIsLoadedAllImages = '''
const isLoadedAllImages = () => {
  const images = document.getElementsByTagName("img");
  let completed = true;
  for (const image of images) {
    if (image.complete === false) {
      completed = false;
      break;
    }
  }
  return completed;
}
return isLoadedAllImages()
'''

def isLoadedAllImages(timeOut=60, interval=1):
  completed = False
  start = time.time()
  while time.time() - start < timeOut and completed == False:
    completed = g_driverforisLoadedAllImages.execute_script(JavaScriptIsLoadedAllImages)
    time.sleep(interval)
  return completed

# ★ ここに追加：最終保存の共通ヘルパー（縮小＋減色＋圧縮）
from PIL import Image as _PIL_Image

TARGET_MAX_WIDTH = 1200      # 横幅上限（要件に応じて調整）
PNG_COLORS = 128             # 128～256が実用的
PNG_COMPRESS_LVL = 9         # 0(速い/大)～9(遅い/小)
# JPEG/WebPを使いたいならここを切替（例: "JPEG" or "WEBP"）
OUTPUT_FORMAT = "PNG"        # 既存拡張子を変えたくないならPNGのまま

def _shrink_and_save_pillow(img, path):
    # 1) リサイズ（縦横比維持）
    if TARGET_MAX_WIDTH and img.width > TARGET_MAX_WIDTH:
        new_h = int(img.height * TARGET_MAX_WIDTH / img.width)
        img = img.resize((TARGET_MAX_WIDTH, new_h), _PIL_Image.LANCZOS)

    # 2) 保存
    if OUTPUT_FORMAT.upper() == "PNG":
        img = img.convert("RGB").quantize(colors=PNG_COLORS, method=_PIL_Image.MEDIANCUT, dither=_PIL_Image.NONE)
        img.save(path, "PNG", optimize=True, compress_level=PNG_COMPRESS_LVL)
        return path
    elif OUTPUT_FORMAT.upper() == "JPEG":
        jpg_path = path.rsplit('.', 1)[0] + ".jpg"
        img.convert("RGB").save(jpg_path, "JPEG", quality=72, optimize=True, progressive=True)
        return jpg_path
    elif OUTPUT_FORMAT.upper() == "WEBP":
        webp_path = path.rsplit('.', 1)[0] + ".webp"
        img.save(webp_path, "WEBP", quality=70, method=6)
        return webp_path
    else:
        # デフォルトはPNG
        img = img.convert("RGB").quantize(colors=PNG_COLORS, method=_PIL_Image.MEDIANCUT, dither=_PIL_Image.NONE)
        img.save(path, "PNG", optimize=True, compress_level=PNG_COMPRESS_LVL)
        return path

def getScreenShot(groupName, driver, distDir = '', forceMaximize = False, forceWidth = 0, forceHeight = 0):
    """
    フルページ安定撮影版（リサイズは return 直前のみ適用）:
      - Chrome CDP優先：captureBeyondViewport → NGなら clip 指定の“非スクロール”タイル撮影
      - 更にNGならスクロール＋ビューポート撮影で結合
      - 最終手段は一枚撮り
      - 画像サイズ調整は、共通の最終処理でのみ実施（途中の縮小・減色・再圧縮は一切しない）
    戻り値: 成功時は保存パス（PNG）/失敗時は空文字
    """
    ret = ''
    global g_driverforisLoadedAllImages

    try:
        if driver is None:
            try:
                Log.LoggingWithFormat(groupName, logCategory='E', logtext='msg:driverがNoneのためスクリーンショットの取得に失敗しました')
            except Exception:
                pass
            return ''

        import os, base64, time
        from io import BytesIO

        # ★ 最終リサイズ設定（return 直前のみ適用） -------------------------
        # 倍率で調整したい場合（2.0で2倍、0.5で半分）
        FINAL_SCALE = 0.5
        # 最大幅/高さで制限したい場合（0は無効）
        FINAL_MAX_WIDTH  = 0
        FINAL_MAX_HEIGHT = 0
        # ---------------------------------------------------------------

        # 出力先
        try:
            if distDir and not os.path.isdir(distDir):
                os.makedirs(distDir, exist_ok=True)
        except Exception:
            pass

        g_driverforisLoadedAllImages = driver
        dateTimeStr = uf.getDateTime('%Y%m%d%H%M')
        if distDir == '':
            file_pathTmp = os.path.join(cf.PATH_SCREENSHOT_DIR, f'{groupName}_{dateTimeStr}.png')
        else:
            file_pathTmp = os.path.join(distDir, f'{groupName}_{dateTimeStr}.png')

        # 便利: ヘッドレス判定
        def _is_headless(driver) -> bool:
            """
            Selenium WebDriver がヘッドレスで動いているかをできるだけ確実に判定する。
            - まず 'se:headless' を見る（Selenium 4+）
            - だめなら各ブラウザの options args を確認
            - さらに Chromium 系は DevTools からコマンドラインを確認
            """
            caps = getattr(driver, "capabilities", {}) or {}

            # 1) Selenium 4+ が付与する共通フラグ
            if isinstance(caps, dict) and "se:headless" in caps:
                return bool(caps.get("se:headless"))

            # 2) ブラウザごとの options に渡された args を確認
            def _has_headless_arg(args):
                return any(
                    str(a).strip().startswith("--headless") or str(a).strip() == "-headless"
                    for a in (args or [])
                )

            # Chromium (Chrome/Edge)
            for key in ("goog:chromeOptions", "ms:edgeOptions"):
                opts = caps.get(key) or {}
                if _has_headless_arg(opts.get("args")):
                    return True

            # Firefox
            ff_opts = caps.get("moz:firefoxOptions") or {}
            if _has_headless_arg(ff_opts.get("args")):
                return True

            # 3) Chromium 系: DevTools からコマンドラインを覗く（Remoteでも有効なことが多い）
            try:
                if hasattr(driver, "execute_cdp_cmd"):
                    info = driver.execute_cdp_cmd("Browser.getVersion", {})
                    cmdline = (info or {}).get("commandLine", "")
                    if "--headless" in cmdline:
                        return True
            except Exception:
                pass

            # Safari 等（ヘッドレス未対応）や情報が取れないケースは False
            return False


        # headless = _is_headless(driver)
        headless = cf.isheadless

        # 1) ページ全体サイズ（CSS基準）
        total_width = driver.execute_script("""
            return Math.max(
                document.documentElement.scrollWidth,
                document.body.scrollWidth,
                document.documentElement.offsetWidth,
                document.body.offsetWidth,
                document.documentElement.clientWidth
            );
        """)
        total_height = driver.execute_script("""
            return Math.max(
                document.documentElement.scrollHeight,
                document.body.scrollHeight,
                document.documentElement.offsetHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight
            );
        """)

        # 2) 表示安定化（lazy-load/アニメ抑止）
        try:
            try:
                driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {
                    "features": [{"name": "prefers-reduced-motion", "value": "reduce"}]
                })
            except Exception:
                pass
            driver.execute_script("""
                // 画像: eager & data-* -> src
                for (const img of document.images) {
                    try {
                        img.setAttribute('loading', 'eager');
                        if (!img.src) {
                            if (img.dataset && img.dataset.src) img.src = img.dataset.src;
                            if (img.dataset && img.dataset.original) img.src = img.dataset.original;
                        }
                    } catch(e){}
                }
                const st = document.createElement('style');
                st.id = '___sshot_helper___';
                st.textContent = `*{transition:none !important; animation:none !important}`;
                document.head.appendChild(st);
            """)
        except Exception:
            pass

        # IntersectionObserver を踏ませる
        try:
            driver.execute_cdp_cmd("Page.enable", {})
            driver.execute_cdp_cmd("Input.synthesizeScrollGesture", {
                "x": 0, "y": 0, "yDistance": int(total_height or 2000),
                "speed": 1500, "repeatCount": 1, "repeatDelayMs": 120
            })
            time.sleep(0.2)
            driver.execute_script("window.scrollTo(0, 0);")
        except Exception:
            try:
                viewport_h = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight;") or 800
                step = max(200, int(viewport_h * 0.8))
                for y in range(0, int(total_height or 0), step):
                    driver.execute_script(f"window.scrollTo(0, {y});")
                    time.sleep(0.05)
                driver.execute_script("window.scrollTo(0, 0);")
            except Exception:
                pass

        # 3) 画像ロード待ち（既存仕様を尊重）
        if uf.strstr('Black_Basta', groupName) or uf.strstr('MedusaBlog', groupName):
            isLoaded = True
        else:
            try:
                isLoaded = isLoadedAllImages()
            except Exception:
                isLoaded = True
        if not isLoaded:
            time.sleep(0.6)
            try:
                isLoaded = isLoadedAllImages()
            except Exception:
                isLoaded = True
        if not isLoaded:
            try:
                Log.LoggingWithFormat(groupName, logCategory='E', logtext='msg:画像のロード完了を待てずに中断しました')
            except Exception:
                pass
            return ''

        # 4) “最大化相当”の確保（ヘッドレスではサイズ指定）
        try:
            if uf.strstr('AKIRA', groupName) or forceMaximize:
                try:
                    if not headless:
                        driver.maximize_window()
                    else:
                        driver.set_window_size(max(int(forceWidth or 2400), 1600), max(int(forceHeight or 1600), 1000))
                except Exception:
                    pass
            else:
                if not headless:
                    try:
                        driver.maximize_window()
                    except Exception:
                        driver.set_window_size(max(int(forceWidth or 0), int(total_width or 1366), 1366),
                                               max(int(forceHeight or 0), 900))
                else:
                    driver.set_window_size(max(int(forceWidth or 2400), 1600), max(int(forceHeight or 1600), 1000))
        except Exception:
            pass

        # DPR（情報として取得するだけ。途中ではスケールしない）
        try:
            dpr = driver.execute_script("return window.devicePixelRatio || 1;") or 1
            dpr = max(1, float(dpr))
        except Exception:
            dpr = 1

        # ここから実際のキャプチャ。最終的に final_img に PIL.Image を入れる
        final_img = None

        # ---------- 5) CDP: 一発フルページ（captureBeyondViewport） ----------
        try:
            driver.execute_cdp_cmd("Page.enable", {})
            metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {}) or {}
            content_size = metrics.get("contentSize") or metrics.get("cssContentSize") or {}
            css_w = int(content_size.get("width") or total_width or 1200)
            css_h = int(content_size.get("height") or total_height or 2000)
            css_w = min(css_w, 16384)
            css_h = min(css_h, 16384)

            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                "mobile": False,
                "width": min(css_w, 2400),
                "height": min(css_h, 1200),
                "deviceScaleFactor": dpr,   # 途中での縮小/拡大はしない
            })
            time.sleep(0.05)

            shot = driver.execute_cdp_cmd("Page.captureScreenshot", {
                "format": "png",
                "fromSurface": True,
                "captureBeyondViewport": True
            })
            if shot and shot.get("data"):
                try:
                    from PIL import Image as _Image
                    final_img = _Image.open(BytesIO(base64.b64decode(shot["data"]))).convert("RGBA")
                except Exception:
                    # Pillowが無い・開けない場合はここでは保留（他ルートに回す）
                    final_img = None
        except Exception:
            pass
        finally:
            try:
                driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
            except Exception:
                pass
            try:
                driver.execute_script("window.scrollTo(0, 0);")
            except Exception:
                pass

        # ---------- 6) CDP: clip 指定の“非スクロール”タイル撮影 ----------
        if final_img is None:
            try:
                from PIL import Image as _Image
                driver.execute_cdp_cmd("Page.enable", {})
                metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {}) or {}
                content_size = metrics.get("contentSize") or metrics.get("cssContentSize") or {}
                css_w = int(content_size.get("width") or total_width or 1200)
                css_h = int(content_size.get("height") or total_height or 2000)
                css_w = min(css_w, 16384)
                css_h = min(css_h, 16384)

                driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                    "mobile": False,
                    "width": min(css_w, 2400),
                    "height": 1200,
                    "deviceScaleFactor": dpr,  # 途中での縮小/拡大はしない
                })
                time.sleep(0.05)

                TILE_H = 4000
                y = 0
                tiles = []

                while y < css_h:
                    h = min(TILE_H, css_h - y)
                    shot = driver.execute_cdp_cmd("Page.captureScreenshot", {
                        "format": "png",
                        "fromSurface": True,
                        "clip": {"x": 0.0, "y": float(y), "width": float(css_w), "height": float(h), "scale": 1.0}
                    })
                    if not shot or not shot.get("data"):
                        break
                    tiles.append(_Image.open(BytesIO(base64.b64decode(shot["data"]))).convert("RGBA"))
                    y += h

                if tiles:
                    W = max(im.width for im in tiles)
                    H = sum(im.height for im in tiles)
                    out = _Image.new("RGBA", (W, H), (255, 255, 255, 0))
                    cy = 0
                    for im in tiles:
                        out.paste(im, (0, cy))
                        cy += im.height
                    final_img = out  # ← ここでは保存しない（最後にだけリサイズ＆保存）
            except Exception:
                final_img = None
            finally:
                try:
                    driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
                except Exception:
                    pass
                try:
                    driver.execute_script("window.scrollTo(0, 0);")
                except Exception:
                    pass

        # ---------- 7) CDP不可: スクロール＋ビューポート撮影をPillowで結合 ----------
        if final_img is None:
            try:
                from PIL import Image as _Image, Image
                import io

                try:
                    sticky_top = driver.execute_script("""
                        const els = Array.from(document.querySelectorAll('body *'));
                        let m = 0;
                        for (const el of els) {
                            const s = window.getComputedStyle(el);
                            if (!s) continue;
                            if (s.position === 'fixed') {
                                const r = el.getBoundingClientRect();
                                if (r.top <= 0) m = Math.max(m, Math.round(r.height));
                            }
                        }
                        return m;
                    """) or 0
                except Exception:
                    sticky_top = 0

                viewport_h = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight;") or 1080
                TILE_H = max(400, min(int(viewport_h), 4000))
                overlap = max(0, min(sticky_top + 8, int(TILE_H * 0.2)))

                tiles = []
                y = 0
                while y < int(total_height or 0):
                    driver.execute_script(f"window.scrollTo(0, {y});")
                    time.sleep(0.15)
                    png_bytes = driver.get_screenshot_as_png()
                    im = _Image.open(io.BytesIO(png_bytes)).convert("RGBA")
                    if tiles and overlap > 0:
                        im = im.crop((0, overlap, im.width, im.height))
                    tiles.append(im)
                    if y + TILE_H >= int(total_height or 0):
                        break
                    y += (TILE_H - overlap if TILE_H > overlap else TILE_H)

                if tiles:
                    W = max(im.width for im in tiles)
                    H = sum(im.height for im in tiles)
                    out = Image.new("RGBA", (W, H), (255, 255, 255, 0))
                    cy = 0
                    for im in tiles:
                        out.paste(im, (0, cy)); cy += im.height
                    final_img = out
            except Exception:
                final_img = None

        # ---------- 8) 最終フォールバック：一枚撮り ----------
        if final_img is None:
            try:
                png_ok = driver.save_screenshot(file_pathTmp)
                if png_ok:
                    try:
                        from PIL import Image as _Image
                        final_img = _Image.open(file_pathTmp).convert("RGBA")
                        # ここで後続の共通リサイズ＆再保存を行う（直書きはしない）
                    except Exception:
                        # Pillowが無い場合は、そのまま返す
                        ret = file_pathTmp
                        return ret
                else:
                    try:
                        fo.Func_DeleteFile(file_pathTmp)
                    except Exception:
                        pass
                    return ''
            except Exception:
                return ''

        # ---------- 9) 共通：return 直前の“だけ”リサイズ → 保存 ----------
        try:
            from PIL import Image as _Image
            # 1) 倍率指定
            if isinstance(final_img, _Image.Image):
                if FINAL_SCALE and FINAL_SCALE != 1.0:
                    new_w = max(1, int(final_img.width  * float(FINAL_SCALE)))
                    new_h = max(1, int(final_img.height * float(FINAL_SCALE)))
                    final_img = final_img.resize((new_w, new_h), _Image.LANCZOS)

                # 2) 最大幅/高さでの制限（必要な方だけ有効化）
                if FINAL_MAX_WIDTH and final_img.width > FINAL_MAX_WIDTH:
                    new_h = int(final_img.height * (FINAL_MAX_WIDTH / final_img.width))
                    final_img = final_img.resize((FINAL_MAX_WIDTH, new_h), _Image.LANCZOS)

                if FINAL_MAX_HEIGHT and final_img.height > FINAL_MAX_HEIGHT:
                    new_w = int(final_img.width * (FINAL_MAX_HEIGHT / final_img.height))
                    final_img = final_img.resize((new_w, FINAL_MAX_HEIGHT), _Image.LANCZOS)

                # 3) そのままPNGで保存（途中の減色・圧縮はしない）
                final_img.convert("RGB").save(file_pathTmp, "PNG")
                ret = file_pathTmp
            else:
                # 万一 Image オブジェクトでない場合は何もせず終了
                ret = file_pathTmp if os.path.exists(file_pathTmp) else ''
        except Exception:
            # リサイズ・保存で失敗したら一旦生で返す（存在すれば）
            try:
                if os.path.exists(file_pathTmp):
                    ret = file_pathTmp
                else:
                    ret = ''
            except Exception:
                ret = ''

        return ret

    except Exception as e:
        try:
            Log.LoggingWithFormat(groupName, logCategory='E', logtext=f'args:{str(e.args)},msg:{getattr(e, "msg", str(e))}')
        except Exception:
            pass
        ret = ''

    return ret

from PIL import Image
import io
def save_fullscreenshot(groupName, driver, distDir = ''):
    try:
        ret = ''
        # なぜかこの関数でスクショがうまくとれないので旧式に戻す
        if groupName.startswith('Snatch') == False:
            forceWidth_ = 0
            forceHeight_ = 0
            # 詳細ページはなぜか見切れてしまうので強制的に幅をセット
            if groupName.startswith('CACTUS'):
                forceWidth_ = 1822

            ret = getScreenShot(groupName, driver, distDir, forceWidth = forceWidth_, forceHeight=forceHeight_)
        else:
            g_driverforisLoadedAllImages = driver
            if distDir == '':
                # スクリーンショット
                # 実際のget処理と離れてて気持ち悪いから本来getHTMLData関数内でやりたいけどファイル処理をやるのも嫌なのでこっちでやる。
                # TODO：まともに奇麗にするなら作り直さないとだめかな
                # dateTimeStr = fo.Func_GetFileUpdateTime(resultFile).replace('/','').replace(':', '').replace(' ', '_')
                dateTimeStr = uf.getDateTime('%Y%m%d%H%M')
                # BOXにアップする処理を実装するまでは日付がついたユニークなファイル名で保管してたけど容量するので
                # BOXにアップしている今は直近のしか保存しない
                file_pathTmp = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '_' + dateTimeStr + '.png')  
            else:
                file_pathTmp = os.path.join(distDir, groupName + '_' + dateTimeStr + '.png')  

            """ Capture a full-page screenshot using image stitching """
            orig_overflow = driver.execute_script("return document.body.style.overflow;")
            driver.execute_script("document.body.style.overflow = 'hidden';")  # scrollbar

            total_height = driver.execute_script("return document.body.scrollHeight;")
            total_width = driver.execute_script("return document.body.scrollWidth;")
            view_width = driver.execute_script("return window.innerWidth;")
            view_height = driver.execute_script("return window.innerHeight;")

            stitched_image = Image.new("RGB", (total_width, total_height))

            scroll_height = 0
            while scroll_height < total_height:
                col_count = 0
                scroll_width = 0
                driver.execute_script("window.scrollTo(%d, %d)" % (scroll_width, scroll_height))

                while scroll_width < total_width:
                    if col_count > 0:
                        driver.execute_script("window.scrollBy("+str(view_width)+",0)") 

                    img = Image.open(io.BytesIO(driver.get_screenshot_as_png()))

                    if scroll_width + view_width >= total_width \
                    or scroll_height + view_height >= total_height:  # need cropping
                        new_width = view_width
                        new_height = view_height
                        if scroll_width + view_width >= total_width:
                            new_width = total_width - scroll_width
                        if scroll_height + view_height >= total_height:
                            new_height = total_height - scroll_height

                        stitched_image.paste(
                            img.crop((view_width - new_width, view_height - new_height,
                                    view_width, view_height)),
                            (scroll_width, scroll_height)
                        )
                        scroll_width += new_width
                    else:  # no cropping
                        stitched_image.paste(img, (scroll_width, scroll_height))
                        scroll_width += view_width
                    col_count += 1

                scroll_height += view_height

            driver.execute_script("document.body.style.overflow = '" + orig_overflow + "';")
            stitched_image.save(file_pathTmp)

            if fo.Func_IsFileExist(file_pathTmp):
                ret = file_pathTmp

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    
    return ret

# from time import sleep
# import io
# from PIL import Image
# def get_full_screenshot_image(driver, reverse=False, driverss_contains_scrollbar=None):
#     # Scroll to the bottom of the page once
#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#     sleep(0.5)
#     scroll_height, document_client_width, document_client_height, inner_width, inner_height = driver.execute_script("return [document.body.scrollHeight, document.documentElement.clientWidth, document.documentElement.clientHeight, window.innerWidth, window.innerHeight]")
#     # type: List[io.BytesIO]
#     streams_to_be_closed = []
#     # type: List[Tuple[Image.Image, int]]
#     images = []
#     try:
#         # open
#         for y_coord in range(0, scroll_height, document_client_height):
#             driver.execute_script("window.scrollTo(0, arguments[0]);", y_coord)
#             stream = io.BytesIO(driver.get_screenshot_as_png())
#             streams_to_be_closed.append(stream)
#             img = Image.open(stream)
#             images.append((img, min(y_coord, scroll_height - inner_height)))
#         # load
#         scale = float(img.size[0]) / (inner_width if driverss_contains_scrollbar else document_client_width)
#         img_dst = Image.new(mode='RGBA', size=(int(document_client_width * scale), int(scroll_height * scale)))
#         for img, y_coord in (reversed(images) if reverse else images):
#             img_dst.paste(img, (0, int(y_coord * scale)))
#         return img_dst
#     finally:
#         # close
#         for stream in streams_to_be_closed:
#             stream.close()
#         for img, y_coord in images:
#             img.close()

def trim(img, x, y, width, height):
    return img[y:y+height, x:x+width]

#指定した割合（１がマックス）で縦にトリミングする（縦を短くする）
def TrimImage(groupName,img_path,kaishi_x,kaishi_y, width_minasu,trim_num):
    try:
        img = cv2.imread(img_path, 1)
        height = img.shape[0]
        width = img.shape[1]
        #トリミング
        ret_img = trim(img,kaishi_x,kaishi_y,width-width_minasu,round(height * trim_num))
        cv2.imwrite(img_path, ret_img)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

#指定した割合（１がマックス）で縦にトリミングする（縦を短くする）
# width_minasuは全体の幅からトリミング後の幅をマイナスした値をいれる
def TrimImage_takasa(groupName,img_path,kaishi_x,kaishi_y, width_minasu,takasa):
    try:
        img = cv2.imread(img_path, 1)
        height = img.shape[0]
        width = img.shape[1]
        takasa_ = takasa

        # takasaが0.1～0.9の場合は割合とみなす
        if takasa > 0:
            if takasa <= 1:
                # 整数渡し
                takasa_ = int(height*takasa)

        # takasaが０以下は不正なのでイメージの高さをそのまま渡す
        # それ以外は高さ指定
        else:
            takasa_ = height

        #トリミング
        ret_img = trim(img,kaishi_x,kaishi_y,width-width_minasu,takasa_)
        # ret_img_height = ret_img.shape[0]
        # ret_img_width = ret_img.shape[1]
        cv2.imwrite(img_path, ret_img)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

def TrimImage_takasa_DetailPage(groupName, path):

    if uf.strstr('LockBit', groupName):
        # TrimImage_takasa(groupName,path,0, 0, 0,1100)
        pass
    elif uf.strcmp('MedusaBlog', groupName):
        TrimImage_takasa(groupName,path,0, 0, 0,2000)

#テンプレートマッチングでの座標取得
def GetLogo_topLeft_XY(RansomName,logoimg,inputimg):
    top_left = 0
    if os.path.exists(logoimg) == True:
        img = cv2.imread(inputimg)
        template = cv2.imread(logoimg)
        _, w, h = template.shape[::-1]
        res = cv2.matchTemplate(img,template,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        btm_right = (top_left[0] + w, top_left[1] + h)
        #cv2.rectangle(img,top_left, btm_right, 255, 2)
        log_x = top_left[0]
        log_y = top_left[1]
        #cv2.imshow("test", img)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
    return top_left

def Triming_Screenshot(RansomName,FILENAME):
    #トリミングして保存

    img_wariai = check_img_bunkatu

    #ヘッドレスが無効の場合は見えているすべての範囲を撮影する
    if sb.headless_options == 0:
        img_wariai = 1.0

    #対象に合わせてトリミングの開始位置を調整
    if uf.strcmp("XING_Team", RansomName) == True\
         or uf.strcmp("Arvin_Club", RansomName) == True\
         or uf.strcmp("Black_Shadow", RansomName) == True\
         or uf.strcmp("Nefilim", RansomName) == True\
         or uf.strcmp("RansomEXX", RansomName) == True\
         or uf.strcmp("Suncrypt", RansomName) == True:

        if sb.headless_options == 1:
            img_wariai = 0.4
        TrimImage(RansomName,FILENAME,0,0,0,img_wariai) #高さ指定不要
                
    elif uf.strcmp("Royal", RansomName) == True:
        TrimImage_takasa(RansomName,FILENAME,180,0,379,2000) #高さ指定
        # TrimImage_takasa(RansomName,FILENAME,1400,0,2811,2000) #高さ指定

    elif uf.strcmp("RansomHouse", RansomName) == True:
        TrimImage_takasa(RansomName,FILENAME,350,0,722,0) #高さ指定        

    elif uf.strcmp("AlphV", RansomName) == True\
        or uf.strcmp("Snatch", RansomName) == True\
        or uf.strcmp("MosesStaff", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1820) #高さ指定

    elif uf.strcmp("Marketo", RansomName) == True\
        or uf.strstr("8BASE", RansomName) == True\
        or uf.strcmp("CLOP", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,2000) #高さ指定

    elif uf.strcmp("Midas_Leak", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1600) #高さ指定

    elif RansomName == "SynACK_File_Leaks"\
        or uf.strcmp("Karma_Leaks", RansomName) == True\
        or uf.strcmp("RansomEXX", RansomName) == True\
        or uf.strcmp("BlackMatter", RansomName) == True\
        or uf.strcmp("Ragnar_Locker", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1340) #高さ指定

    elif uf.strcmp("Hive", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1620) #高さ指定

    elif uf.strcmp("Babuk", RansomName) == True:
        # if sb.headless_options == 1:
        img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,660,390,1324,img_wariai) #高さ指定

    elif uf.strcmp("Haron", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1500) #高さ指定

    # elif uf.strstr("LockBit", RansomName) == True:
    #     if sb.headless_options == 1:
    #         img_wariai = 1
    #     TrimImage_takasa(RansomName,FILENAME,0,0,0,1030) #高さ指定

    elif uf.strcmp("Vice_Society", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1650) #高さ指定

    elif uf.strcmp("Grief", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,120) #高さ指定
        #TrimImage_takasa(RansomName,FILENAME,0,0,0,2275) #高さ指定

    elif uf.strcmp("Lorenz", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,2800) #高さ指定

    elif uf.strcmp("Prometheus", RansomName) == True\
        or uf.strcmp("Dark_Leak_Market", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,0,0,3000) #高さ指定

    # elif uf.strcmp("Dark_Leak_Market", RansomName) == True:
    #     if sb.headless_options == 1:
    #         img_wariai = 1
    #     TrimImage(RansomName,FILENAME,0,0,400,img_wariai) #高さ指定不要
    #     TrimImage_takasa(RansomName,FILENAME,0,0,0,1120) #高さ指定

    elif uf.strcmp("RAMP", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        #TrimImage(RansomName,FILENAME,0,0,0,img_wariai) #高さ指定不要
        TrimImage_takasa(RansomName,FILENAME,0,0,0,500) #高さ指定

    elif uf.strcmp("Mount_Locker", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.3
        #ロゴの位置をもとにトリミングを実施
        top_left = GetLogo_topLeft_XY(RansomName,"C:\\Users\\test\\Desktop\\Templete\\Mount_Locker_Templete.png",FILENAME)
        log_x = top_left[0]
        log_y = top_left[1]
        #TrimImage_takasa(RansomName,FILENAME,0,300,50,2500) #高さ指定
        TrimImage_takasa(RansomName,FILENAME,0,log_y,50,2500) #高さ指定

    elif uf.strcmp("Avaddon", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.2
        #TrimImage(FILENAME,0,0,0,img_wariai)
        TrimImage_takasa(RansomName,FILENAME,0,0,0,2700) #高さ指定

    elif uf.strcmp("Pysa", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.05
        #TrimImage(FILENAME,0,0,0,img_wariai)
        TrimImage_takasa(RansomName,FILENAME,0,0,0,1500) #高さ指定

    elif uf.strcmp("Darkside", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.05
        TrimImage(RansomName,FILENAME,0,0,0,img_wariai) 

    elif uf.strcmp("CONTI_Ryuk", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.3
        #TrimImage_takasa(RansomName,FILENAME,47,765,68,1500) #高さ指定
        #TrimImage_takasa(RansomName,FILENAME,47,765,68,800) #高さ指定
        TrimImage_takasa(RansomName,FILENAME,47,765,68,1500) #高さ指定

    # elif uf.strcmp("CON_TI_SANOH", RansomName) == True:
    #     if sb.headless_options == 1:
    #         img_wariai = 1
    #     TrimImage_takasa(RansomName,FILENAME,0,0,0,700) #高さ指定

    elif uf.strcmp("Cuba", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage(RansomName,FILENAME,0,500,0,img_wariai)    

    elif uf.strcmp("REvil_Sodinokibi", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.3
        #TrimImage(FILENAME,0,0,10,img_wariai) 
        TrimImage_takasa(RansomName,FILENAME,0,0,10,1800) #高さ指定

    elif uf.strcmp("Karakurt", RansomName) == True:
        if sb.headless_options == 0:
            TrimImage_takasa(RansomName,FILENAME,1330,0,2680,img_wariai)

    elif uf.strcmp("MedusaBlog", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 0.3
        TrimImage_takasa(RansomName,FILENAME,0,0,0,img_wariai)

    elif uf.strcmp("Black_Basta", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        # いったんトリミングしないでやってみる
        # TrimImage_takasa(RansomName,FILENAME,435,0,900,img_wariai)

    elif uf.strcmp("CipherLocker", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1
        TrimImage_takasa(RansomName,FILENAME,0,560,1,img_wariai)        

    elif uf.strcmp("AKIRA", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1        
        TrimImage_takasa(RansomName,FILENAME,260,70,521,img_wariai)
    # トリミングしないシリーズ
    elif uf.strcmp("Nevada_DLS", RansomName) == True\
        or uf.strcmp("BlackByte", RansomName) == True\
        or uf.strcmp("Donut_Files", RansomName) == True\
        or uf.strcmp("CRYPTNET", RansomName) == True\
        or uf.strcmp("Dunghill_Leak", RansomName) == True:
        if sb.headless_options == 1:
            img_wariai = 1        
        TrimImage_takasa(RansomName,FILENAME,0,0,0,img_wariai) 

    # 指定されてないやつは不用意にトリミングしない
    # else:
    #     if sb.headless_options == 1:
    #         img_wariai = check_img_bunkatu
    #     TrimImage(RansomName,FILENAME,0,0,0,img_wariai) #高さ指定不要
    Log.LoggingWithFormat(RansomName, logCategory = 'I', logtext = f'トリミング終了 End')

def wrap_Func_scraping(driver, soup, groupName, url, forDetail = False, value=None):
    ret = {}

    IsIndivisialScrapingTarget = True
    if uf.strstr('Lockbit5.0', groupName):
        ret = Func_scraping_Lockbit(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('LockBit', groupName):
        # ファイルサーバーなので別関数
        if uf.strcmp(groupName, 'LockBit3.0_2024_5'):
            ret = Func_scraping_Lockbit_FS(driver, soup, groupName, url, forDetail, value)
        else:
            IsIndivisialScrapingTarget = False
    elif uf.strcmp('Hive', groupName):
        ret = Func_scraping_HIVE(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Royal', groupName):
        ret = Func_scraping_Royal(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('PLAY', groupName):
        ret = Func_scraping_Play(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Karakurt', groupName):
        ret = Func_scraping_Karakurt(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('MedusaBlog', groupName):
        ret = Func_scraping_MedusaBlog(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('AlphV_BlackCat', groupName):
        ret = Func_scraping_AlphV_BlackCat(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('AlphV_BlackCat_Mirror1', groupName):
        ret = Func_scraping_AlphV_BlackCat_Mirror1(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('RansomHouse', groupName):
        ret = Func_scraping_RansomHouse(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('MALLOX', groupName):
        ret = Func_scraping_MALLOX(driver, soup, groupName, url, forDetail, value)        

    elif uf.strcmp('Black_Basta', groupName):
        ret = Func_scraping_BlackBasta(driver, soup, groupName, url, forDetail, value)  

    elif uf.strcmp('BlackByte', groupName):
        ret = Func_scraping_BlackByte(driver, soup, groupName, url, forDetail, value)  

    elif uf.strstr('BianLian', groupName):
        ret = Func_scraping_BianLian(driver, soup, groupName, url, forDetail, value)  

    elif uf.strcmp('Dark_Leak_Market_New', groupName):
        ret = Func_scraping_Dark_Leak_Market_New(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('RansomEXX', groupName):
        ret = Func_scraping_RansomExx(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('TRIGONA', groupName):
        ret = Func_scraping_TRIGONA(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('8BASE', groupName):
        ret = Func_scraping_8BASE(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('DarkRace', groupName):
        ret = Func_scraping_DarkRace(driver, soup, groupName, url, forDetail, value)        

    elif uf.strcmp('Nokoyawa_Leaks', groupName):
        ret = Func_scraping_Nokoyawa_Leaks(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Rhysida', groupName):
        ret = Func_scraping_Rhysida(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('NoEscape', groupName):
        ret = Func_scraping_NoEscape(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Qilin', groupName):
        ret = Func_scraping_Qilin(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Snatch', groupName):
        ret = Func_scraping_Snatch(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('CACTUS', groupName):
        ret = Func_scraping_CACTUS(driver, soup, groupName, url, forDetail, value)
    
    elif uf.strcmp('RANSOMWARE_BLOG', groupName):
        ret = Func_scraping_RANSOMWARE_BLOG(driver, soup, groupName, url, forDetail, value)  

    elif uf.strcmp('ABYSS', groupName):
        ret = Func_scraping_ABYSS(driver, soup, groupName, url, forDetail, value)  

    elif uf.strcmp('Dunghill_Leak', groupName):
        ret = Func_scraping_Dunghill_Leak(driver, soup, groupName, url, forDetail, value)  

    elif uf.strcmp('Everest', groupName):
        ret = Func_scraping_Everest(driver, soup, groupName, url, forDetail, value)
    elif uf.strcmp('Everest_FileServer', groupName):
        ret = Func_scraping_Everest_FileServer(driver, soup, groupName, url, forDetail, value)
    elif uf.strcmp('BLACKSUIT', groupName):
        ret = Func_scraping_BLACKSUIT(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('RA_GROUP', groupName):
        ret = Func_scraping_RA_GROUP(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('MONEYMESSAGE', groupName):
        ret = Func_scraping_MONEYMESSAGE(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Cyclops', groupName):
        ret = Func_scraping_Cyclops(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Knight', groupName):
        ret = Func_scraping_Cyclops(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Arvin_Club', groupName):
        ret = Func_scraping_Arvin_Club(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Ragnar_Locker', groupName):
        ret = Func_scraping_Ragnar_Locker(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Monti', groupName):
        ret = Func_scraping_Monti(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Donut_Leaks', groupName):
        ret = Func_scraping_Donut_Leaks(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('INC_Ransom', groupName):
        ret = Func_scraping_INC_Ransom(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('INC_Ransom_url2', groupName):
        ret = Func_scraping_INC_Ransom(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('INC_Ransom_New', groupName):
        ret = Func_scraping_INC_Ransom_New(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Metaencryptor', groupName):
        ret = Func_scraping_Metaencryptor(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('RansomedVC', groupName):
        ret = Func_scraping_RansomedVC(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Quantum', groupName):
        ret = Func_scraping_Quantum(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Cloak', groupName):
        ret = Func_scraping_Cloak(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Lorenz', groupName):
        ret = Func_scraping_Lorenz(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('CiphBit', groupName):
        ret = Func_scraping_CiphBit(driver, soup, groupName, url, forDetail, value)

    # Jsonが落ちてこなくなったのでいったん保留 2024/11/14
    elif uf.strcmp('AKIRA', groupName):
        ret = Func_scraping_AKIRA(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('CryptBB', groupName):
        ret = Func_scraping_CryptBB(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('ThreeAM', groupName):
        ret = Func_scraping_ThreeAM(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('LostTrust', groupName):
        ret = Func_scraping_LostTrust(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('HUNTERS_INTERNATIONAL', groupName):
        ret = Func_scraping_HUNTERS_INTERNATIONAL(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('V_IS_VENDETTA', groupName):
        ret = Func_scraping_V_IS_VENDETTA(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('MEOW', groupName):
        ret = Func_scraping_MEOW(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('DAIXIN', groupName):
        ret = Func_scraping_DAIXIN(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('SIEGEDSEC', groupName):
        ret = Func_scraping_SIEGEDSEC(driver, soup, groupName, url, forDetail, value) 
        
    elif uf.strcmp('Cuba', groupName):
        ret = Func_scraping_Cuba(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('DragonForce', groupName):
        ret = Func_scraping_DragonForce(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('WEREWOLVES', groupName):
        ret = Func_scraping_WEREWOLVES(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('NONAME', groupName):
        ret = Func_scraping_NONAME(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('SLUG', groupName):
        ret = Func_scraping_SLUG(driver, soup, groupName, url, forDetail, value) 

    elif uf.strstr('Omega', groupName):
        ret = Func_scraping_Omega(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('TRISEC', groupName):
        ret = Func_scraping_TRISEC(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('ransomhub', groupName):
        ret = Func_scraping_ransomhub(driver, soup, groupName, url, forDetail, value) 

    elif uf.strstr('STORMOUS', groupName):
        ret = Func_scraping_STORMOUS(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('Mogilevich', groupName):
        ret = Func_scraping_Mogilevich(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Blackout', groupName):
        ret = Func_scraping_Blackout(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Alpha(MYDATA)', groupName):
        ret = Func_scraping_MYDATA(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Donex', groupName):
        ret = Func_scraping_Donex(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('KILLSEC', groupName):
        ret = Func_scraping_KILLSEC(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('KILLSEC_2', groupName):
        ret = Func_scraping_KILLSEC_2(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('RED_RANSOMEWARE', groupName):
        ret = Func_scraping_RED_RANSOMEWARE(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('DARK_VAULT_3(LikeLockBit)', groupName):
        ret = Func_scraping_DarkVault(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('HelloGookie(HelloKitty)', groupName):
        ret = Func_scraping_HelloGookie(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('QIULONG', groupName):
        ret = Func_scraping_QIULONG(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('APT73(Eraleig)', groupName):
        ret = Func_scraping_APT73(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('APT73(BASHEE)', groupName):
        ret = Func_scraping_APT73_BASHEE(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('EMBARGO', groupName):
        ret = Func_scraping_EMBARGO(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('Dispossessor', groupName):
        ret = Func_scraping_Dispossessor(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('dAn0n(DANON)', groupName):
        ret = Func_scraping_dAn0n(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('SpaceBears', groupName):
        ret = Func_scraping_SpaceBears(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('UNDERGROUND', groupName):
        ret = Func_scraping_UNDERGROUND(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('FSOCIETY(FLOCKER)', groupName):
        ret = Func_scraping_FSOCIETY(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('ZeroTolerance', groupName):
        ret = Func_scraping_ZeroTolerance(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('ARCUS_MEDIA', groupName):
        ret = Func_scraping_ARCUS_MEDIA(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('RED_RANSOMWARE', groupName):
        ret = Func_scraping_RED_RANSOMWARE(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('HANDARA', groupName):
        ret = Func_scraping_HANDARA(driver, soup, groupName, url, forDetail, value)      

    elif uf.strcmp('SenSayQ', groupName):
        ret = Func_scraping_SenSayQ(driver, soup, groupName, url, forDetail, value)  
 
    elif uf.strcmp('BlackLock(EL_DORADO)', groupName):
        ret = Func_scraping_EL_DORADO(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('TRINITY', groupName):
        ret = Func_scraping_TRINITY(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('Cicada3301', groupName):
        ret = Func_scraping_Cicada3301(driver, soup, groupName, url, forDetail, value)
        
    elif uf.strcmp('PRYX', groupName):
        ret = Func_scraping_PRYX(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('BrainCipher', groupName):
        ret = Func_scraping_BrainCipher(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('VanirGroup', groupName):
        ret = Func_scraping_VanirGroup(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('RANSOMCORTEX', groupName):
        ret = Func_scraping_RANSOMCORTEX(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('MAD_LIBERATOR', groupName):
        ret = Func_scraping_MAD_LIBERATOR(driver, soup, groupName, url, forDetail, value) 
                  
    elif uf.strcmp('NULLBULGE', groupName):
        ret = Func_scraping_NULLBULGE(driver, soup, groupName, url, forDetail, value) 

    elif uf.strcmp('FOG', groupName):
        ret = Func_scraping_FOG(driver, soup, groupName, url, forDetail, value)   

    elif uf.strcmp('LYNX', groupName):
        ret = Func_scraping_LYNX(driver, soup, groupName, url, forDetail, value) 

    elif uf.strstr('HELLDOWN', groupName):
        ret = Func_scraping_HELLDOWN(driver, soup, groupName, url, forDetail, value) 
 
    elif uf.strcmp('ValenciaRansomware', groupName):
        ret = Func_scraping_ValenciaRansomware(driver, soup, groupName, url, forDetail, value)                  

    elif uf.strcmp('Orca', groupName):
        ret = Func_scraping_Orca(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('NITROGEN', groupName):
        ret = Func_scraping_NITROGEN(driver, soup, groupName, url, forDetail, value)

    elif uf.strcmp('SARCOMA', groupName):
        ret = Func_scraping_SARCOMA(driver, soup, groupName, url, forDetail, value)  

    elif uf.strstr('AposSecurity', groupName):
        ret = Func_scraping_AposSecurity(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('PLAYBOY', groupName):
        ret = Func_scraping_PLAYBOY(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('KAIROS', groupName):
        ret = Func_scraping_KAIROS(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('HELLCAT', groupName):
        ret = Func_scraping_HELLCAT(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('CHORT', groupName):
        ret = Func_scraping_CHORT(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('INTERLOCK', groupName):
        ret = Func_scraping_INTERLOCK(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('Termite', groupName):
        ret = Func_scraping_Termite(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('SAFEPAY', groupName):
        ret = Func_scraping_SAFEPAY(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('Argonauts', groupName):
        ret = Func_scraping_Argonauts(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('Funksec', groupName):
        ret = Func_scraping_Funksec(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('BLUEBOX', groupName):
        ret = Func_scraping_BLUEBOX(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('Morpheus', groupName):
        ret = Func_scraping_Morpheus(driver, soup, groupName, url, forDetail, value)

    elif uf.strstr('Kraken (HelloKitty)', groupName):
        ret = Func_scraping_Kraken_HelloKitty(driver, soup, groupName, url, forDetail, value)        
    elif uf.strstr('GD LockerSec', groupName):
        ret = Func_scraping_GDLockerSec(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('Linkc', groupName):
        ret = Func_scraping_Linkc(driver, soup, groupName, url, forDetail, value)  
    elif uf.strstr('RunSomeWares', groupName):
        ret = Func_scraping_RunSomeWares(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Secp0', groupName):
        ret = Func_scraping_Secp0(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('SKIRA TEAM', groupName):
        ret = Func_scraping_SKIRA(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Weyhro', groupName):
        ret = Func_scraping_Weyhro(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Crazy Hunter Team', groupName):
        ret = Func_scraping_CrazyHunterTeam(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Babuk(2025)', groupName):
        ret = Func_scraping_Babuk2025(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('NightSpire', groupName):
        ret = Func_scraping_NightSpire(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('VanHelsing', groupName):
        ret = Func_scraping_VanHelsing(driver, soup, groupName, url, forDetail, value)        
    elif uf.strstr('Mamona', groupName):
        ret = Func_scraping_Mamona(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Frag', groupName):
        ret = Func_scraping_Frag(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Arkana', groupName):
        ret = Func_scraping_Arkana(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('RALord', groupName) or uf.strstr('Nova', groupName):
        ret = Func_scraping_RALord(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('CHAOS(2025)', groupName):
        ret = Func_scraping_CHAOS2025(driver, soup, groupName, url, forDetail, value)  
    elif uf.strstr('BERT', groupName):
        ret = Func_scraping_BERT(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('DEVMAN', groupName):
        ret = Func_scraping_DEVMAN(driver, soup, groupName, url, forDetail, value)  
    elif uf.strstr('CRYPTO24', groupName):
        ret = Func_scraping_CRYPTO24(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('AzzaSec', groupName):
        ret = Func_scraping_AzzaSec(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('Gunra', groupName):
        ret = Func_scraping_Gunra(driver, soup, groupName, url, forDetail, value)
    elif uf.strcmp('Silent', groupName):
        ret = Func_scraping_Silent(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('J_GROUP', groupName):
        ret = Func_scraping_J_GROUP(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('IMN_Crew', groupName):
        ret = Func_scraping_IMN_Crew(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Anubis', groupName):
        ret = Func_scraping_Anubis(driver, soup, groupName, url, forDetail, value)    
    elif uf.strstr('WORLDLEAKS', groupName):
        ret = Func_scraping_WORLDLEAKS(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('DataCarry', groupName):
        ret = Func_scraping_DataCarry(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('DireWolf', groupName):
        ret = Func_scraping_DireWolf(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('SilentRansomGroup', groupName):
        ret = Func_scraping_SilentRansomGroup(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('GLOBAL', groupName):
        ret = Func_scraping_GLOBAL(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('WALocker', groupName):
        ret = Func_scraping_WALocker(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Warlock', groupName):
        ret = Func_scraping_Warlock(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('TeamXXX', groupName):
        ret = Func_scraping_TeamXXX(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Kawa4096', groupName):
        ret = Func_scraping_Kawa4096(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Sinobi', groupName):
        ret = Func_scraping_Sinobi(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('SATANLOCK V2', groupName):
        ret = Func_scraping_SATANLOCK_V2(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('SatanLock', groupName):
        ret = Func_scraping_SatanLock(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Payouts King', groupName):
        ret = Func_scraping_PayoutsKing(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('D4RK4RMY', groupName):
        ret = Func_scraping_D4RK4RMY(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Securotrop', groupName):
        ret = Func_scraping_Securotrop(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('BEAST', groupName):
        ret = Func_scraping_BEAST(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('BQTLOCK', groupName):
        ret = Func_scraping_BQTLOCK(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('PEAR', groupName):
        ret = Func_scraping_PEAR(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Black Nevas', groupName):
        ret = Func_scraping_BlackNevas(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('LEAKNET', groupName):
        ret = Func_scraping_LEAKNET(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Cephalus', groupName):
        ret = Func_scraping_Cephalus(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Desolator', groupName):
        ret = Func_scraping_Desolator(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Obscura', groupName):
        ret = Func_scraping_Obscura(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Yurei', groupName):
        ret = Func_scraping_Yurei(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('The Gentlemen', groupName):
        ret = Func_scraping_Gentlemen(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('RADAR', groupName):
        ret = Func_scraping_RADAR(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('COINBASE CARTEL', groupName):
        ret = Func_scraping_COINBASECARTEL(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('LunaLock', groupName):
        ret = Func_scraping_LunaLock(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('BLACKSHRANTAC', groupName):
        ret = Func_scraping_BLACKSHRANTAC(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('MIGA', groupName):
        ret = Func_scraping_MIGA(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('RADIANT', groupName):
        ret = Func_scraping_RADIANT(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('ARACHNA', groupName):
        ret = Func_scraping_ARACHNA(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Scattered LAPSUS$ Hunters', groupName):
        ret = Func_scraping_Scattered_LAPSUS_Hunters(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Kyber', groupName):
        ret = Func_scraping_Kyber(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Kryptos', groupName):
        ret = Func_scraping_Kryptos(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Brotherhood', groupName):
        ret = Func_scraping_Brotherhood(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('NASIR SECUTRIY', groupName):
        ret = Func_scraping_NASIRSECUTRIY(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('TENGU', groupName):
        ret = Func_scraping_TENGU(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Genesis', groupName):
        ret = Func_scraping_Genesis(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Kazu', groupName):
        ret = Func_scraping_Kazu(driver, soup, groupName, url, forDetail, value)
    elif uf.strstr('Benzona', groupName):
        ret = Func_scraping_Benzona(driver, soup, groupName, url, forDetail, value)  
    elif uf.strstr('TridentLocker', groupName):
        ret = Func_scraping_TridentLocker(driver, soup, groupName, url, forDetail, value)  
    elif uf.strstr('Minteye', groupName):
        ret = Func_scraping_Minteye(driver, soup, groupName, url, forDetail, value) 
    elif uf.strstr('root', groupName):
        ret = Func_scraping_root(driver, soup, groupName, url, forDetail, value) 
     
    # 超絶あほくさいけどsummaryのスペルミスでsummaryになっているが、
    # 今更戻せないのでつじつま合わせ用に新規取得したやつはここでsummaryを作成する。
    # 今スペル修正すると影響範囲デカすぎるのでそれはいつかやる
    if len(ret):
        for key in ret.keys():
            ret[key]['summary'] = ret[key].get('summary','')
    else:
        IsIndivisialScrapingTarget = False

    return ret, IsIndivisialScrapingTarget

# -------------------------------------------------------------------------------------------------------------------
# スクレイピング用
# -------------------------------------------------------------------------------------------------------------------

# Jsonデータもらえるならそっちをもらう
def Func_getJsonDataFromURL(groupName, driver, url):
    ret = {}
    try:
        if driver != None:
            isSuccess = False
            for i in range(5):
                driver.get(url)

                for j in range(10):
                    html = driver.page_source.encode('utf-8')
                    soup = BeautifulSoup(html, 'html.parser')

                    if soup != None:
                        bodyText = soup.get_text().strip()
                        if len(bodyText) > 0:
                            isSuccess = True
                            break
                    time.sleep(2)

                if isSuccess:
                    break

        # ステータスコードが200（成功）であるか確認
        if len(bodyText) > 0:
            # escaped_json_string = re.sub(r'(?<!\\)"', r'\"', bodyText)

            ret = json.loads(bodyText)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return ret

def scroll(driver, direction, intelval = 1):
    try:
        if direction == 'down':
            #ブラウザのウインドウ高を取得する
            win_height = driver.execute_script("return window.innerHeight")
            #スクロール開始位置の初期値（ページの先頭からスクロールを開始する）
            last_top = 1
            
            # Medusaはスクロールしないと古い情報が読み込まれないので取れない
            while True:
                #スクロール前のページの高さを取得
                last_height = driver.execute_script("return document.body.scrollHeight")
                
                #スクロール開始位置を設定
                top = last_top

                #ページ最下部まで、徐々にスクロールしていく
                while top < last_height:
                    top += int(win_height * 0.8)
                    driver.execute_script("window.scrollTo(0, %d)" % top)
                    time.sleep(intelval)

                #5秒待って、スクロール後のページの高さを取得する
                time.sleep(5)
                new_last_height = driver.execute_script("return document.body.scrollHeight")

                #スクロール前後でページの高さに変化がなくなったら無限スクロール終了とみなしてループを抜ける
                if last_height == new_last_height:
                    break

                #次のループのスクロール開始位置を設定
                last_top = last_height

        elif direction == 'up':
            driver.execute_script("window.scrollTo(0, 0)")

    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')

def is_display_none(elem):
    style = elem.get("style", "")

    ret = "display:none" in style
    if not ret:
        ret = "display: none;" in style
    return ret

def waitImageLoadComplete(groupName, driver):
    ret = False
    
    screenShotTmp = ''
    try:
        templateFile = os.path.join(cf.PATH_IMAGETEMPLATE_DIR, rf'{groupName}_Template.png')
        if fo.Func_IsFileExist(templateFile):
            screenShotTmp = getScreenShot(groupName, driver)
            ret = uf.Judge_TempleteMatching(templateFile, screenShotTmp)
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
    finally:
        fo.Func_DeleteFile(screenShotTmp)

    return ret


def convert_datetime_format(groupName, input_str):
    from datetime import datetime

    try:
        # ISO 8601形式の日時をdatetimeオブジェクトに変換
        dt = datetime.strptime(input_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        # 指定の形式にフォーマット
        formatted_str = dt.strftime("%Y/%m/%d %H:%M:%S")
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
        return input_str
    
    return formatted_str

def convert_timestamp_to_datetime(groupName, timestamp_str):
    from datetime import datetime
    try:
        # ミリ秒のタイムスタンプを秒に変換
        timestamp_sec = int(timestamp_str) / 1000
        # タイムスタンプをdatetimeオブジェクトに変換
        dt = datetime.fromtimestamp(timestamp_sec)
        # 指定の形式にフォーマット
        formatted_str = dt.strftime("%Y/%m/%d %H:%M:%S")
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', 
                            logtext = f'args:{str(e.args)},msg:{str(e)}')
        return timestamp_str
    
    return formatted_str


# 指定した要素のテキストを配列に入れて返す。各要素直下のテキストしか取得しない
# def getTextAll(groupName, elem, jointStr = '\n\n'):
    retArray = []
    retText = ''
    try:
        def has_direct_text(tag):
            if tag.string:  # Checks if the tag has a string directly
                return True
            if not any(tag.children):  # Checks if the tag has no children
                return True
            return False
        
        # 被害組織説明取得
        if elem != None:
            texts = []
            for element in elem.find_all(True):
                if has_direct_text(element):
                    text = element.text.strip()
                    if text:
                        retArray.append(text)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    
    finally:
        try:
            if retArray:
                retText = jointStr.join(retArray)
            else:
                retText = elem.get_text().strip()
        except Exception as e:
            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
            retArray = []
            retText = ''

    return retText

# def getTextAll(groupName, elem, jointStr='\n\n'):
#     retArray = []
#     retText = ''

#     try:
#         def has_direct_text(tag):
#             return tag.string is not None
        
#         # 被害組織説明取得
#         if elem is not None:
#             for element in elem.descendants:
#                 if has_direct_text(element):
#                     text = element.string.strip()
#                     if text:
#                         retArray.append(text)

#     except Exception as e:
#         Log.LoggingWithFormat(groupName, logCategory='E', logtext=f'args:{str(e.args)}, msg:{str(e)}')
    
#     finally:
#         try:
#             if retArray:
#                 retText = jointStr.join(retArray)
#             else:
#                 retText = elem.get_text().strip()
#         except Exception as e:
#             Log.LoggingWithFormat(groupName, logCategory='E', logtext=f'args:{str(e.args)}, msg:{str(e)}')
#             retArray = []
#             retText = ''


#     return retText

def getTextAll(groupName, elem, jointStr='\n\n'):
    retArray = []
    retText = ''

    try:
        if elem is not None:
            def get_direct_text(tag):
                direct_text = []
                if tag.string:
                    direct_text.append(tag.string.strip())
                for child in tag.children:
                    if child.name:  # Check if it's a tag
                        if child.string:
                            direct_text.append(child.string.strip())
                        else:
                            direct_text.extend(get_direct_text(child))
                    elif isinstance(child, str):
                        direct_text.append(child.strip())
                return direct_text

            retArray = get_direct_text(elem)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', logtext=f'args:{str(e.args)}, msg:{str(e)}')

    finally:
        try:
            if retArray:
                retText = jointStr.join(retArray)
            else:
                retText = elem.get_text()

            if retText:
                retText = retText.strip()

                # 改行コードが３つ以上あったら2つに減らす
                retText = re.sub(r'\n{3,}', '\n\n', retText)
        except Exception as e:
            Log.LoggingWithFormat(groupName, logCategory='E', logtext=f'args:{str(e.args)}, msg:{str(e)}')
            retArray = []
            retText = ''

    return retText
# -------------------------------------------------------------------------------------------------------------------
def Func_scraping_Lockbit(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='post-company-content')
                if elem != None:
                    elem = elem.find(class_='desc')
                    if elem != None:
                        summaryTmp = elem.get_text().strip()
                        if len(summaryTmp) > 0:
                            summary = summaryTmp.strip().replace('\n','')
                        
                        if len(summary) > len(value['summary']):
                            value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                    
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="post-title")
                        if elem != None:
                            victimNameTemp = elem.get_text()
                            if len(victimNameTemp) > 0:
                                victimName = victimNameTemp.strip()
                        
                        elem = i.find(class_="post-block-text")
                        if elem != None:
                            summaryTmp = elem.get_text().strip()
                            if len(summaryTmp) > 0:
                                summary = summaryTmp.strip().replace('\n','')
                            
                        urlStr = victimName
                        
                        elem = i.find(class_="updated-post-date")
                        if elem != None:
                            updateDateTmp = elem.get_text().strip()
                            if len(updateDateTmp) > 0:
                                updateDate = updateDateTmp.strip()

                        detailUrl = i.get('href')

                        if detailUrl != None:
                            # detailUrl = uf.extractStrging('\'','\'',detailUrl)
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Lockbit_FS(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                tr_elements = soup.find_all('tr')
                for tr in tr_elements:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
  
                    folder_name = tr.find('span', class_='folder-name')
                    date = tr.find('td', class_='date')
                    
                    if folder_name and date:
                        victimName = folder_name.text
                        updateDate = date.text
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
     
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_HIVE(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if soup != None:
            # 各被害組織情報のまとまりブロックを列挙
            victimBlockList = soup.find_all(class_="blog-card-main")

            for i in victimBlockList:
                victimName = ''
                summary = ''
                urlStr = ''
                updateDate = ''
                detailUrl = ''  

                #　被害組織名取得
                elem = i.select_one('div:nth-child(1) > h2:nth-child(1)')
                if elem != None:
                    victimName = elem.get_text().strip()

                # 被害組織HP取得
                elem = i.find("a")
                if elem != None:
                    urlStr = elem.get('href')

                # 被害組織説明取得
                elem = i.find(class_="description")
                if elem != None:
                    summary = elem.get_text().strip()

                # 公開時刻取得
                elem = i.find(class_="blog-card-time")
                if elem != None:
                    timeBlock = elem.find(class_='blog-card-time-end')
                    if timeBlock != None:
                        updateDate = timeBlock.find('span').get_text().strip()

                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                if len(victimName) > 0:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_Royal(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if driver != None and soup != None:
            # スクロールしないと古い情報とれないので下までスクロール
            scroll(driver, 'down', intelval=3)

            # スクロールでHtml更新されたはずなので読み込みなおし
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser') 

            cards = soup.find_all(class_='post active') + soup.find_all(class_='post')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.select_one('div:nth-child(2) > h2:nth-child(1)')
                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find("main")
                    if elem != None:
                        summaryTmp = elem.get_text().strip()
                        if len(summaryTmp) > 0:
                            summary = summaryTmp.strip().replace('\xa0', ' ')
                        
                    # 被害組織HP取得
                    elem = i.find("a")
                    if elem != None:
                        urlStr = elem.get('href')
                    
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_="time")
                    if elem != None:
                        updateDateTmp = elem.find_all(True)
                        
                        allText = []
                        for iContent in updateDateTmp:
                            contentsCnt = len(iContent.contents)
                            if contentsCnt > 0:
                                for i in range(contentsCnt):
                                    if type(iContent.contents[i]) is NavigableString:
                                        text = iContent.contents[i].text
                                        if len(text) > 0:
                                            text2 = text.strip().replace('\xa0', ' ')

                                            if len(text2) > 0:
                                                allText.append(text2)
                        if len(allText) > 0:
                            updateDate=" ".join(allText)

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

        # スクショのために最上部まで戻す
        scroll(driver, 'up')

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Play(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if soup != None:
            # 3ページ目まで
            for pageCount in range(1,4):
                if pageCount > 1:
                    targetUrl = urllib.parse.urljoin(url, f'index.php?page={str(pageCount)}')
                    driver.get(targetUrl)

                    html = driver.page_source.encode('utf-8')
                    soup = BeautifulSoup(html, 'html.parser')

                cards = soup.find_all(class_='News')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        victimName = i.contents[0]
                        
                        # 被害組織説明取得
                        elem = i.find(class_ = 'location')
                        if elem and elem.next:
                            summary = elem.next.strip()
                            
                        # 被害組織HP取得
                        elem = i.find(class_ = 'link')
                        if elem != None and elem.next != None:
                            urlStrTmp = elem.next.get_text()

                            if len(urlStrTmp) > 0:
                                urlStr = urlStrTmp.replace('\xa0','')
                        
                        # 掲載時刻、更新時刻取得
                        elem = i.select_one('th:nth-child(1) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1)')
                        if elem != None and elem.next != None:
                            updateDateTmp = elem.next.get_text()

                            if len(updateDateTmp) > 0:
                                updateDate = updateDateTmp.replace('publication date: ', '')
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    finally:
        wrap_getURL(driver, url, groupName)

    return retDict

def Func_scraping_Karakurt(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if soup != None:
            # Karakurtは2タイプあるので別々に取得
            cards_pre = soup.find_all(class_="ciz-post")
            cards_released = soup.find_all(class_="category-mid-post-two")
                
            if len(cards_pre) > 0:
                for i in cards_pre:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_="post-title")
                    if elem != None:
                        victimNameTemp = elem.get_text().strip()
                        if len(victimNameTemp) > 0:
                            victimName = victimNameTemp.strip()

                    # 関連URL取得
                    elem = i.find(class_="post-category")
                    if elem != None:
                        elem = elem.find('a')
                        if elem != None:
                            urlStr = elem.get('href')                        

                    # 被害組織説明取得
                    elem = i.find(class_="post-des")
                    if elem != None:
                        summary = elem.get_text().strip()
                        if len(summary) > 0:
                            summary = summary.strip().strip('\nexpand\n\n')

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

            if len(cards_released) > 0:
                for i in cards_released:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_="post-title")
                    if elem != None:
                        elem = elem.find('a')
                        if elem != None:                        
                            victimNameTemp = elem.get_text().strip()
                            if len(victimNameTemp) > 0:
                                victimName = victimNameTemp.strip()
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_="post-date")
                    if elem != None:
                        updateDate = elem.get_text().strip()

                        if len(updateDate) > 0:
                            updateDate = updateDate.strip()

                    # 関連URL取得
                    elem = i.find(class_="post-category")
                    if elem != None:
                        elem = elem.find('a')
                        if elem != None:
                            urlStr = elem.get('href')

                    # 被害組織説明取得
                    elem = i.find(class_="post-des dropcap")
                    if elem != None:
                        summary = elem.get_text().strip()
                        if len(summary) > 0:
                            summary = summary.strip().strip('\nexpand\n\n')

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

# Jsonバージョン。値の中にダブルコートがエスケープできてないくていったん保留
# def Func_scraping_MedusaBlog(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    templateFile = ''

    try:
        if driver != None and soup != None:
            pageNum = 0
            dataList = []

            while True:
                subUrl = f'/api/search?company=&page={pageNum}'
                databaseUrl = urllib.parse.urljoin(url, subUrl)

                jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if jsonData != None:
                    tmpList = jsonData.get('list', [])
                    isEnd = jsonData.get('end', True)
                    
                    if len(tmpList) > 0:
                        dataList.extend(tmpList)
                    elif isEnd == False:
                        break
                    else:
                        break
                        
                pageNum += 1

            for i in dataList:
                victimName = ''
                summary = ''
                urlStr = ''
                updateDate = ''
                detailUrl = ''

                victimName = i.get('company_name', '').strip()
                summary = i.get('description', '').strip()
                updateDate = i.get('updated_date', '').strip()
                id = i.get('id', '')
                if id != '':
                    detailUrl = urllib.parse.urljoin(url, f'/detail?id={id}')

                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

            wrap_getURL(driver, url, groupName)
           
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

# スクロールバージョン
def Func_scraping_MedusaBlog(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    templateFile = ''

    try:
        if driver != None and soup != None:
            cnt = 0
            while True:
                # スクロールしないと古い情報とれないので下までスクロール
                scroll(driver, 'down')

                # isDisplayNone = waitImageLoadComplete(groupName, driver)
                
                # if isDisplayNone:
                # スクロールでHtml更新されたはずなので読み込みなおし
                html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, 'html.parser') 

                circularProgress = soup.find('progress', id='circular-progress')

                if circularProgress != None:
                    style = circularProgress.get('style')

                    if uf.strstr('display: none;', style):
                        break

                cnt += 1
                if cnt >= 300:
                    break
                else:
                    time.sleep(10)
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scroll Roop')
            
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scroll Roop End')

            # スクロールでHtml更新されたはずなので読み込みなおし
            # Whileの中でやってるからいらんとは思うが念のため
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')    

            cards = soup.find_all(class_='card')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'card-title')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'card-text text-left')
                    if elem != None:
                        summary = elem.get_text().strip()
                        
                    # 被害組織HP取得
                    urlStr = ''
                    
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'text-muted')
                    if elem != None:
                        updateDate = elem.get_text().strip()

                    # 詳細ページURL
                    id = i.get('data-id')
                    if id != None:
                        detailUrl = f'{url}/detail?id={id}'
                        
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

        # スクショのために最上部まで戻す
        scroll(driver, 'up')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def convert_epoch_to_datetime_string(epoch_time_millis, milliseconds = True):
    import datetime

    if epoch_time_millis > 0:
        # エポックタイムをミリ秒から秒に変換
        if milliseconds:
            epoch_time_seconds = epoch_time_millis / 1000
        else:
            epoch_time_seconds = epoch_time_millis

        # datetimeオブジェクトに変換
        date_time = datetime.datetime.fromtimestamp(epoch_time_seconds)

        # 指定されたフォーマットの文字列に変換
        return date_time.strftime('%Y/%m/%d %H:%M:%S')
    else:
        return ''

def Func_scraping_AlphV_BlackCat(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinaiYooooooo = 0

        else:
            # AlphVは読み込み遅いのでJsonデータ直接とりいく
            # 1ページ目～3ページくらいはとっておく
            databaseUrlArray = ['/api/blog/all/0/9', '/api/blog/all/9/9', '/api/blog/all/18/9']

            for item in databaseUrlArray:
                databaseUrl = urllib.parse.urljoin(url, item)

                jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if len(jsonData) == 0:
                    break

                if len(jsonData.get('items',[])) > 0:
                    dataArray = jsonData['items']

                    for data in dataArray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        victimName = data.get('title', '')
                        updateDate = convert_epoch_to_datetime_string(data.get('createdDt', 0))
                        
                        detailUrlTmp = data.get('id', '')
                        if len(detailUrlTmp) > 0:
                            detailUrl = urllib.parse.urljoin(url, detailUrlTmp)
                        publication = data.get('publication', {})

                        if publication != None and len(publication) > 0:
                            urlStr = publication.get('url', '')
                            
                            description = publication.get('description', '').strip()
                            message = publication.get('message', '').strip()

                            if description and message:
                                summary = description + '\n\n' + message
                            else:
                                summary = description + message

                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

        wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_AlphV_BlackCat_Mirror1(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinaiYooooooo = 0

        else:
            # AlphVは読み込み遅いのでJsonデータ直接とりいく
            # 1ページ目～3ページくらいはとっておく
            databaseUrlArray = ['/api/blog/all/0/9', '/api/blog/all/9/9', '/api/blog/all/18/9']

            for item in databaseUrlArray:
                databaseUrl = urllib.parse.urljoin(url, item)

                jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if len(jsonData) > 0 and len(jsonData.get('items',[])) > 0:
                    dataArray = jsonData['items']

                    for data in dataArray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        victimName = data.get('title', '')
                        updateDate = convert_epoch_to_datetime_string(data.get('createdDt', 0))
                        
                        detailUrlTmp = data.get('id', '')
                        if len(detailUrlTmp) > 0:
                            detailUrl = urllib.parse.urljoin(url, detailUrlTmp)
                        publication = data.get('publication', {})

                        if publication != None and len(publication) > 0:
                            urlStr = publication.get('url', '')
                            
                            description = publication.get('description', '').strip()
                            message = publication.get('message', '').strip()

                            if description and message:
                                summary = description + '\n\n' + message
                            else:
                                summary = description + message

                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

        wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RansomHouse(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            # http://zohlm7ahjwegcedoz7lrdrti7bvpofymcayotp744qhx6gjmxbuo2yid.onion/a
            databaseUrl = urllib.parse.urljoin(url, 'a')
            response = sb.getHtmlResponseByRequest(databaseUrl)
            if len(response.content) > 0:
                text = response.content.decode("utf-8")
                dataArray = json.loads(text).get('data', []) 

            for i in dataArray:
                victimName = i.get('header','')
                summary = i.get('info','')
                urlStr = i.get('url','')
                updateDate = i.get('actionDate','')
                id = i.get('id','')
                detailUrl = ''
                if id:
                    detailUrl = f'{url}/r/{id}'

                if victimName:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_MALLOX(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            # scroll(driver, 'down')

            cards = soup.find_all(class_='card')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'fs-3 fw-bold text-gray-900 mb-2')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'text-gray-500 fw-semibold fs-5 mt-1 mb-7 Mmaoyun mjCZzxSNQrmF')

                    if elem == None:
                        elem = i.find(class_ = 'card-text JeTZTnSDufewPYXPeWrY')
                    
                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    urlStr = ''
                    
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'card-toolbar')
                    if elem != None:
                        updateDate = elem.get_text().strip()

                    # 詳細ページURL
                    elem = i.find('a')
                    if elem != None:
                        detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
            # scroll(driver, 'up')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BlackBasta(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 組織説明
                elem = soup.find(class_="vuepress-markdown-body")

                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            while(True):
                if soup != None:
                    cards = soup.find_all(class_='card')

                    if len(cards) > 0:
                        for i in cards:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            #　被害組織名取得
                            elem = i.find(class_ = 'blog_name_link')

                            if elem != None:
                                victimName = elem.get_text().strip()
                                detailUrl = elem.get('href')
                            
                            # 被害組織説明取得
                            elem = i.find(class_ = 'vuepress-markdown-body')

                            if elem != None:
                                summary = elem.get_text().strip()

                            # 被害組織HP取得
                            urlStr = ''
                            
                            # 掲載時刻、更新時刻取得
                            updateDate = ''
                                
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
                # 次のページ
                # find_elementは要素がないときの探索遅いので先に
                btnElem = soup.find(class_='next-page-btn')
                if btnElem != None:
                    btnElem = driver.find_element(By.CLASS_NAME, 'next-page-btn')
                    if btnElem != None:
                        btnElem.click()
                        waitObject(driver, groupName)
                        html = driver.page_source.encode('utf-8')
                        soup = BeautifulSoup(html, 'html.parser')
                else:
                    # 1ページめに戻す
                    driver.refresh()
                    waitObject(driver, groupName)
                    break

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BlackByte(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        # if driver:
        #     close_button = driver.find_element(By.CLASS_NAME, "closes")
        #     close_button.click()
        if soup != None:
            cards = soup.find_all(class_='table table-bordered table-content')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'target-name')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'description')

                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    elem = i.find(class_="website fa fa-globe")
                    if elem != None:
                        urlStr = elem.get('href')
                    
                    # 掲載時刻、更新時刻取得
                    updateDate = ''
                        
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BianLian(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            page = 2
            while(True):
                cards = soup.find_all(class_='list-item')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'title')

                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        # 被害組織説明取得
                        elem = i.find(class_ = 'description')

                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織HP取得
                        urlStr = ''
                        
                        # 掲載時刻、更新時刻取得
                        updateDate = ''
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

                # Nextボタンがなくなるまで取得
                NextBtn = soup.find(class_='page-item page-next')
                pageLink = None
                if NextBtn != None:
                    pageLink = NextBtn.find(class_='page-link')
                    if pageLink != None:
                        nextPageUrl = url + f'/page/{str(page)}/'
                        driver.get(nextPageUrl)
                        waitObject(driver, groupName)

                        html = driver.page_source.encode('utf-8')
                        soup = BeautifulSoup(html, 'html.parser')                    
                        page += 1
                if pageLink == None:
                    # 最初のページに戻す
                    driver.get(url)
                    waitObject(driver, groupName)
                    break

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Snatch(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if driver != None and soup != None:
            readMoreBtn = driver.find_elements_by_class_name('a-b-b-r-l-button')
            for btnElem in readMoreBtn:
                btnElem.click()
            
            page = 2
            while(True):
                cards = soup.find_all(class_='list-item')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'title')

                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        # 被害組織説明取得
                        elem = i.find(class_ = 'description')

                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織HP取得
                        urlStr = ''
                        
                        # 掲載時刻、更新時刻取得
                        updateDate = ''
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

                # Nextボタンがなくなるまで取得
                NextBtn = soup.find(class_='page-item page-next')
                pageLink = None
                if NextBtn != None:
                    pageLink = NextBtn.find(class_='page-link')
                    if pageLink != None:
                        nextPageUrl = url + f'/page/{str(page)}/'
                        driver.get(nextPageUrl)
                        waitObject(driver, groupName)

                        html = driver.page_source.encode('utf-8')
                        soup = BeautifulSoup(html, 'html.parser')                    
                        page += 1
                if pageLink == None:
                    break

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Dark_Leak_Market_New(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='card-text')
                if elem != None:
                    summaryTmp = elem.get_text().strip()
                    if len(summaryTmp) > 0:
                        summary = summaryTmp.strip().replace('\n','')
                    
                    if len(summary) > len(value['summary']):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_='table-responsive')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elems = i.find_all('a')

                        if len(elems) > 1:
                            elem = elems[1]
                            victimName = elem.get_text().strip()
                            detailUrl = elem.get('href')
                            if detailUrl != None:
                                detailUrl = urllib.parse.urljoin(url, detailUrl)
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RansomExx(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='entry-content')
                if elem != None:
                    summaryTmp = elem.get_text().strip()
                    if len(summaryTmp) > 0:
                        summary = summaryTmp.strip().replace('\n','')
                    
                    if len(summary) > len(value['summary']):
                        value['summary'] = summary
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='inside-article')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'entry-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            elem = elem.find('a')
                            if elem != None:
                                detailUrl = elem.get('href')
                                if detailUrl != None:
                                    detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        # 被害組織説明取得 → マーケットなので値段いれとく。他に情報ないし
                        # 被害組織HP取得
                        elem = i.find(class_ = 'entry-summary')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 掲載時刻、更新時刻取得
                        elem = i.find(class_ = 'entry-date published')
                        if elem != None:
                            updateDate = elem.get_text().strip()
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_TRIGONA(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinaiYooooooo = 0
        else:
            if driver != None and soup != None:
                # AlphVは読み込み遅いのでJsonデータ直接とりいく
                # 1ページ目～3ページくらいはとっておく
                databaseUrlArray = ['/api?page=1']

                for item in databaseUrlArray:
                    databaseUrl = urllib.parse.urljoin(url, item)

                    jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                    data = jsonData.get('data',[])
                    if len(jsonData) > 0 and len(data) > 0:
                        dataArray = data['leaks']

                        for data in dataArray:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            victimName = data.get('title', '').strip()
                            
                            id = data.get('rndid', '')
                            if len(id) > 0:
                                detailUrl = urllib.parse.urljoin(url, f'/leak/{id}')

                            updateDate = data.get('created_at', '').strip()
                            summary = data.get('descryption', '').strip()
                            urlStr = data.get('external_link', '').strip()

                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

            wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_8BASE(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            cards = soup.find_all(class_='list-group-item rounded-3 py-3 bg-body-secondary text-bg-dark mb-2 position-relative')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'stretched-link')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得 → マーケットなので値段いれとく。他に情報ないし
                    elems = i.find_all(class_ = 'small opacity-50')

                    if len(elems) > 0:
                        for  elem in elems:
                            summary = summary + elem.get_text().strip() + '\n'
                        summary = summary.strip()

                    # 被害組織HP取得
                    urlStr = ''
                    
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'd-flex gap-2 small mt-1 opacity-25')

                    if elem != None:
                        updateDate = elem.get_text().strip()
                        
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Nokoyawa_Leaks(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if driver != None and soup != None:
            scroll(driver, 'down')

            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser') 

            cards = soup.find_all(class_='flex flex-col space-y-8')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'text-5xl font-semibold')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'text-xl font-normal')

                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    urlStr = ''
                    
                    # 掲載時刻、更新時刻取得
                    updateDate = ''
                        
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
            scroll(driver, 'up')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_DarkRace(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            cards = soup.find_all(class_='post-list-item')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl=''

                    #　被害組織名取得
                    elem = i.find(class_ = 'post-title')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'post-content')

                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    urlStr = ''
                    
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'post-info')

                    if elem != None:
                        updateDate = elem.get_text().strip()

                    # elem = i.find(class_ = 'read-more')
                    # if elem != None:
                    #     elem = elem.find('a')
                    #     if elem != None:
                    #         detailUrl = elem.get('href') 

                    # if detailUrl != None:
                    #     detailUrl = uf.extractStrging('\'','\'',detailUrl)
                    #     detailUrl = urllib.parse.urljoin(url, detailUrl)

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Rhysida(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if driver != None:
            # 先にオークション取得
            # http://rhysidafohrhyy2aszi7bm32tnjat5xri65fopcxkdfxhi4tidsg7cad.onion/archive.php?last&auction
            archiveUrlArray = ['archive.php?auction', 'archive.php']

            for archiveUrl in archiveUrlArray:
                targetUrl = urllib.parse.urljoin(url, archiveUrl)
                driver.get(targetUrl)

                html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')

                if soup != None:
                    cards = soup.find_all(class_='border m-2 p-2')

                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl=''

                        #　被害組織名取得
                        elem = i.find(class_ = 'm-2 h4')

                        if elem != None:
                            victimName = elem.get_text().strip()

                            # 被害組織HP取得
                            elem = elem.find('a')
                            if elem != None:
                                urlStr = elem.get('href') 
                        # 被害組織説明取得
                        elem = i.select_one('div.col-10 > div:nth-child(2)')
                        if elem != None:
                            summary = elem.get_text().strip()

                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

            driver.get(url)
            waitObject(driver, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

# 詳細ページから情報取るようにしてるけど、NoEscape回すたびに全被害組織の詳細ページ見に行くから効率悪い
# 次からはやはり全体から情報取得→差分あるものだけMonitorSub.pyからの呼び出しで詳細ページの情報とスクショ取る
# 気持ち悪いけどそれが最効率
def Func_scraping_NoEscape(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if driver != None and soup != None:
            # NoEscapeは詳細ページのほうが情報取りやすいのでまず詳細ページのURLリストつくる
            # cards = soup.find_all(class_="col-lg-4 my-3 d-flex flex-column justify-content-between")
            cards = soup.find_all(class_="col-xxl-3 col-xl-4 col-md-6 px-2 mb-3 d-flex")
            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'fw-bold fs-5 mb-0')
                    if elem != None:
                        victimName = elem.get_text().strip()

                        detailUrl = elem.get('href')
                        if detailUrl != None:
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'text-justify')

                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    elem = i.select_one('div > div.d-flex.flex-column.justify-content-between.flex-fill > div.mb-1 > div:nth-child(3) > a')
                    if elem != None:
                        urlStr = elem.get('href')

                    # 掲載時刻、更新時刻取得
                    elem = i.select_one('div > div.d-flex.flex-column.justify-content-between.flex-fill > div:nth-child(2) > div.d-flex.align-items-center.justify-content-between > div > div.me-4.d-flex.align-items-center > small')
                    if elem != None:
                        updateDate = elem.get_text().strip()

                    elem = i.find(class_ = 'btn btn-sm btn-primary h2 mb-0')
                    if elem != None:
                        detailUrl = elem.get('href')
                        if detailUrl != None:
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Qilin(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 組織説明
                elem = soup.find('div', class_="col-md-8 col-xl-6")

                if elem != None:
                    div_text = ''.join([t.strip() for t in elem.contents if type(t) == NavigableString])
                    if len(div_text) > len(value['summary']):
                        value['summary'] = div_text
        else:
            if driver != None and soup != None:
                # scroll(driver, 'down')

                # html = driver.page_source.encode('utf-8')
                # soup = BeautifulSoup(html, 'html.parser') 

                # cards = soup.find_all(class_='flex flex /-col space-y-8')
                cards = soup.select('div[class="item_box"]')
                # cards = soup.find_all(class_="item_box")
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'item_box-title mb-2 mt-1')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            detailUrl = elem.get('href')
                            if detailUrl != None:
                                detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        # 被害組織説明取得
                        elem = i.find(class_ = 'item_box_text')

                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織HP取得
                        elem = i.find(class_ = 'item_box-info__link')
                        if elem != None:
                            # urlStr = elem.get_text().strip()
                            # elem = i.find("a")
                            # if elem != None:
                            try:
                                urlStr = elem.get('href')
                            except Exception as e:
                                print(str(e))
                                urlStr = ''
                        
                        # 掲載時刻、更新時刻取得
                        elem = i.select_one('div.row.align-items-center > div.col-md-9 > div > div.col-md-10.mb-2 > div.item_box-info.uppercase.d-flex.mb-2 > div:nth-child(2)')
                        if elem != None:
                            updateDate = elem.get_text().strip()
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
                scroll(driver, 'up')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Snatch(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織HP取得
                elem = soup.find(class_='n-n-c-e-n-m-mark mark')
                if elem != None:
                    urlStr = elem.get_text().strip()
                    if len(urlStr) > len(value['url']):
                        value['url'] = urlStr
                
                # 被害組織説明取得
                elem = soup.find(class_='n-n-c-e-text')
                if elem != None:
                    summary = elem.get_text().strip()
                    if len(summary) > len(value['summary']):
                        value['summary'] = summary

                # 掲載時刻、更新時刻取得
                elem = soup.find(class_='n-n-c-e-t-time')
                if elem != None:
                    updateDate = elem.get_text().strip()
                    if len(updateDate) > len(value['updateDate']):
                        value['updateDate'] = updateDate
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='ann-block')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'a-b-name')
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        # 被害組織説明取得
                        elem = i.find(class_ = 'a-b-text')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織HP取得
                        urlStr = ''
                        
                        # 掲載時刻、更新時刻取得
                        elem = i.find(class_ = 'a-b-h-time')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 詳細ページURL
                        elem = i.find(class_ = 'a-b-b-r-l-button')
                        if elem != None:
                            onclick_value = elem['onclick']
                            detailUrl = uf.extractStrging('\'', '\'', onclick_value)
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
                scroll(driver, 'up')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_CACTUS(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織HP取得 CACTUSは詳細説明に含まれてる１
                # elem = soup.find(class_='n-n-c-e-n-m-mark mark')
                # if elem != None:
                #     urlStr = elem.get_text().strip()
                #     if len(urlStr) > len(value['url']):
                #         value['url'] = urlStr
                
                # 被害組織説明取得
                elem = soup.find(class_='prose prose-a:text-[#DADADA] prose-img:w-full lg:prose-lg prose-headings:text-[#DADADA] mt-10 max-w-full text-[#DADADA]')
                if elem != None:
                    summary = elem.get_text().strip()
                    if len(summary) > len(value['summary']):
                        value['summary'] = summary

        else:
            if driver != None and soup != None:
                while(True):
                    cards = soup.find_all(class_='grid bg-[#222E34] relative')

                    if len(cards) > 0:
                        for i in cards:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            #　被害組織名取得
                            elem = i.find(class_ = 'text-[16px] font-bold leading-6 text-white')

                            if elem != None:
                                victimName = elem.get_text().strip()
                            
                            # 被害組織説明取得
                            elem = i.find(class_ = 'text-[14px] leading-5 text-[#DADADA]')

                            if elem != None:
                                summary = elem.get_text().strip()

                            # 掲載時刻、更新時刻取得
                            elem = i.find(class_ = 'text-[12px] leading-tight')

                            if elem != None:
                                updateDate = elem.get_text().strip()

                            # 詳細ページURL
                            elem = i.find("a")
                            if elem != None:
                                detailUrl = elem.get('href')
                                detailUrl = urllib.parse.urljoin(url, detailUrl)
                                
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    break
                    # Nextボタンがなくなるまで取得→無限ループしてる？からいったん保留2023.12.25
                    # NextBtn = driver.find_element(by=By.XPATH,value="//button[normalize-space()='Next page']")
                    # if NextBtn != None and NextBtn.is_enabled():
                    #     Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'NextBtn.click() Before')
                    #     NextBtn.click()
                    #     Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'NextBtn.click() After')

                    #     time.sleep(10)

                    #     html = driver.page_source.encode('utf-8')
                    #     soup = BeautifulSoup(html, 'html.parser')         
                    # else:
                    #     break

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    
    # finally:
    #     driver.get(url)
    #     waitObject(driver, groupName)

    return retDict

def Func_scraping_RANSOMWARE_BLOG(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        # 詳細ページはあるけど特に取得するものないのでHTML取得はしない

        if driver != None and soup != None:
            cards = soup.find_all(class_=re.compile('.*post type-post.*'))

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'entry-title default-max-width')
                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                        # 詳細ページURL
                        elem = i.find("a")
                        if elem != None:
                            detailUrl = elem.get('href')

                            if detailUrl.startswith('http') == False:
                                detailUrl = ''

                    # 被害組織説明取得
                    elem = i.find(class_ = 'entry-content')

                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    # 掲載時刻、更新時刻取得

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ABYSS(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if driver != None and soup != None:
            cards = soup.select('div[class="col"]')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'card-title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'card-text')

                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織HP取得
                    # 掲載時刻、更新時刻取得
                    
                    # 詳細ページURL取得
                    # detailUrl = elem.get('href')
                    # if detailUrl != None:
                    #     detailUrl = urllib.parse.urljoin(url, detailUrl)

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Dunghill_Leak(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if driver != None and soup != None:
            # cards = soup.select('div[class="custom-container"]')
            cards = soup.find_all(class_='elem_ibody')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'ibody_title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    # 被害組織説明取得
                    elem = i.find(class_ = 'ibody_body')

                    if elem != None:
                        summary = elem.get_text().strip()

                        # 被害組織HP取得
                        elem = i.find("a")
                        if elem != None:
                            urlStr = elem.get('href')

                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'ibody_ft_left')
                    if elem != None:
                        # body > main > section > div:nth-child(1) > div > div.ibody_footer > div.ibody_ft_left > p:nth-child(1) > b
                        elem = elem.select_one('p:nth-child(1)')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                    # 詳細ページURL取得
                    elem = i.find(class_ = 'ibody_ft_right')
                    if elem != None:
                        elem = elem.find("a")
                        if elem != None:
                            detailUrl = elem.get('href')
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Everest(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='timeline')
                if elem != None:
                    summary = elem.get_text().strip()
                    if len(summary) > len(value['summary']):
                        value['summary'] = summary
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='category-item js-open-chat')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'category-title')
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        if victimName:
                            elem = i.find(class_ = 'category-date w-25')
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            # 詳細ページURL
                            value = i['data-translit']
                            detailUrl = url + f'/{value}/'

                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Everest_FileServer(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            if driver != None and soup != None:
                databaseUrl = urllib.parse.urljoin(url, '?api=roots')
                socks_port = sb.find_unused_port()
                sb.reset_tor_port()
                torProc, torConfFile = sb.start_tor(socks_port)  # Torを起動
                session = sb.getSession(socks_port)
                response = session.get(databaseUrl,  verify=False, timeout=30)
                raw_bytes = response.content
                if len(raw_bytes) > 0:
                    text = raw_bytes.decode("utf-8")
                    dataArray = json.loads(text)  

                if torProc:
                    torProc.terminate()
                    torProc.wait()  # プロセスが終了するのを待つ

                sb.cleanup_torrc(torConfFile)

                dataArray = dataArray.get('roots', [])
                for i in dataArray:
                    victimName = i.get('title', '')
                    summary = ''
                    urlStr = ''
                    updateDate = i.get('mtime', '')
                    detailUrl = ''
           
                    if victimName:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BLACKSUIT(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            # 詳細ページなし
            NoDetail = ''

        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='card')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 被害組織説明取得
                        elem = i.find(class_ = 'text')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織HP取得
                        elem = i.find(class_ = 'url')
                        if elem != None:
                            elem = elem.find("a")
                            if elem != None:
                                urlStr = elem.get('href')

                        # 掲載時刻、更新時刻取得

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RA_GROUP(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織URL
                elems= soup.find_all(class_='black-background')

                # 被害組織名取得
                if elems != None:
                    elems[0].get_text().strip()

                # 被害組織URL取得
                if elems != None:
                    value['url'] = elems[1].get_text().strip()

                # 被害組織説明取得
                if elems != None:
                    value['summary'] = elems[3].get_text().strip()

        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='portfolio-content')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        # 被害組織名取得
                        # 詳細ページURL
                        elem = i.find("a")
                        if elem != None:
                            victimName = elem.get_text().strip()
                            detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_MONEYMESSAGE(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elems = soup.find_all(class_='MuiBox-root css-4h4iek')
                
                if len(elems) > 0:
                    text = ''
                    for elem in elems:
                        text = text + elem.get_text().strip() + '\n'

                    value['summary'] = text.strip()
        else:
            if driver != None and soup != None:
                # cards = soup.find_all(class_='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineNone css-xvpw3o')
                cards = soup.find_all(class_=re.compile('.*MuiTypography-root MuiTypography-inherit.*'))

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.select_one('div:nth-child(1)')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 詳細ページURL
                        detailUrl = urllib.parse.urljoin(url, i.get('href'))

                        # 掲載時刻、更新時刻取得
                        elem = i.select_one('div:nth-child(2)')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Cyclops(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     elems = soup.find_all(class_='MuiBox-root css-4h4iek')
                
            #     if len(elems) > 0:
            #         text = ''
            #         for elem in elems:
            #             text = text + elem.get_text().strip() + '\n'

            #         value['summary'] = text.strip()
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='col-sm-6 col-lg-4')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'card-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            # 詳細ページURL
                            elem = elem.find("a")
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                        # 被害組織説明
                        elem = i.find(class_ = 'card-text blog-content-truncate')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Arvin_Club(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     elems = soup.find_all(class_='MuiBox-root css-4h4iek')
                
            #     if len(elems) > 0:
            #         text = ''
            #         for elem in elems:
            #             text = text + elem.get_text().strip() + '\n'

            #         value['summary'] = text.strip()
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='post-content markdown-body')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        # Arvinはクラス名が共通、language-textが四つあり、順番が決まってるのでそちらから取得
                        elems = i.find_all(class_ = 'language-text')
                        
                        #　被害組織名取得
                        victimName = elems[0].get_text().strip()

                        # 被害組織URL
                        urlStr = elems[1].get_text().strip()

                        # 掲載時刻、更新時刻取得
                        prev_elem = i.find_previous_sibling()
                        if prev_elem != None:
                            className =  prev_elem.get('class')
                            if len(className) > 0 and uf.strstr(className[0], 'post-header'):
                                updateDate = prev_elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
        retDict = {}

    return retDict

def Func_scraping_Ragnar_Locker(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='tl_article_content')
                
                if elem != None:
                    value['summary'] = elem.get_text().strip()
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='card')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.select_one('p:nth-child(1)')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 掲載時刻、更新時刻取得
                        elem = i.select_one('p:nth-child(2)')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 詳細ページURL
                        elem = i.find("a")
                        if elem != None:
                            detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Monti(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     elems = soup.find_all(class_='MuiBox-root css-4h4iek')
                
            #     if len(elems) > 0:
            #         text = ''
            #         for elem in elems:
            #             text = text + elem.get_text().strip() + '\n'

            #         value['summary'] = text.strip()
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='col-lg-4 col-sm-6 mb-4')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.select_one('div[class="col"]')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 被害組織説明
                        elem = i.find(class_ = 'col-12')
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find(class_ = 'col-auto published')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 詳細ページURL
                        elem = i.find("a")
                        if elem != None:
                            detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Donut_Leaks(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='post-content')
                
                if elem != None:
                    value['summary'] = elem.get_text().strip()
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='box post-box')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'post-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            # 詳細ページURL
                            elem = elem.find("a")
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                        # 被害組織説明
                        elem = i.find(class_ = 'post-excerpt')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 掲載時刻、更新時刻取得
                        elem = i.find(class_ = 'post-meta')
                        if elem != None:
                            elem = i.find('time')
                            if elem != None:
                                updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_INC_Ransom(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 掲載時刻、更新時刻取得
                cards = soup.select('span[class="text-gray-600 dark:text-gray-700"]')

                if len(cards) > 0:
                    updateDate = ''
                    for i in cards:
                        updateDate += i.get_text().strip() + '\n'

                    value['updateDate'] = updateDate.strip()
                
                # 掲載時刻、更新時刻取得
                elem = soup.find(class_ = 'bg-blueSecondary')
                if elem != None:
                        value['url'] = elem.get_text().strip()
        else:
            if driver != None and soup != None:
                if groupName == 'INC_Ransom':
                    databaseUrl = 'http://incbackrlasjesgpfu5brktfjknbqoahe2hhmqfhasc5fb56mtukn4yd.onion/api/blog/get-leaks'
                elif groupName == 'INC_Ransom_url2':
                    databaseUrl = 'http://incbackend.top/api/blog/get-leaks'
                jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if len(jsonData) > 0 and len(jsonData.get('payload',[])) > 0:
                    dataArray = jsonData['payload']

                    for data in dataArray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        victimName = data.get('title', '')
                        if len(victimName) > 0:
                            victimName = urllib.parse.unquote(victimName)
                        summary = data.get('description', '')
                        updateDate = convert_epoch_to_datetime_string(data.get('createdAt', 0))
                        urlStr = data.get('url', 0)
                        id = data.get('id', '')
                        if len(id) > 0:
                            detailUrl = urllib.parse.urljoin(url, f'blog/leak/{id}')

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

                # cards = soup.find_all(class_=re.compile('.*flex flex-col justify-between.*'))

                # if len(cards) > 0:
                #     for i in cards:
                #         victimName = ''
                #         summary = ''
                #         urlStr = ''
                #         updateDate = ''
                #         detailUrl = ''

                #         #　被害組織名取得
                #         elem = i.find(class_ = 'dark:text-gray-600')
                #         if elem != None:
                #             victimName = elem.get_text().strip()

                #         # 詳細ページURL
                #         # elem = elem.find("a")
                #         # if elem != None:
                #         detailUrl = urllib.parse.urljoin(url, i.get('href'))

                #         # 被害組織説明
                #         elem = i.find(class_ = 'text-sm dark:text-gray-600')
                #         if elem != None:
                #             summary = elem.get_text().strip()

                #         # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                #         if len(victimName) > 0:
                #             retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Metaencryptor(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='col d-flex align-items-stretch mb-3')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'card-header')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 被害組織説明
                        elem = i.find(class_ = 'card-body')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 掲載時刻、更新時刻取得
                        elem = i.find(class_ = 'text-muted')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織URL
                        elems= i.find_all(class_ = 'btn btn-secondary btn-sm')

                        if len(elems) > 0:
                            for elem in elems:
                                tmpStr = elem.get_text().strip()
                                
                                if tmpStr == 'Visit site':
                                    urlStr = elem.get('href')
                                    break
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RansomedVC(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            Nanimoshinai = 0
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')

            # elem = soup.find('main')
            # if elem != None:
            #     value['summary'] = elem.get_text().strip()
        else:
            if soup != None:
                cards = soup.find_all(class_='card')
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        extraData = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'company-header')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find(class_ = 'revenue')
                        if elem != None:
                            extraData = elem.get_text().strip()

                        # 被害組織説明
                        elem = i.find(class_ = 'victim-details')
                        if elem != None:
                            summary = extraData + '\n\n' + elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Quantum(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # summaryは入ってるやつと結合
                tmpsummary = value['summary']

                elem = soup.find(class_ = 'blog-post-content')
                if elem != None:
                    summary = elem.get_text().strip()
                    value['summary'] = tmpsummary + '\n\n' + summary

                elems = soup.find_all(class_ = 'col-sm-9')
                if len(elems) > 0:
                    for elem in elems:
                        tmp = elem.get_text().strip()

                        if tmp == 'Official Link':
                            value['url'] = elem.find('a').get('href')
                            break

        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='panel panel-default')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'blog-post-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 被害組織説明
                        elem = i.find(class_ = 'blog-post-content')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 掲載時刻、更新時刻取得
                        elem = i.find(class_ = 'blog-post-date pull-right')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 詳細ページURL
                        elem= i.find(class_ = 'btn btn-info')
                        if elem != None:
                            detailUrl = urllib.parse.urljoin(url, elem.get('href'))
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Cloak(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # summaryは入ってるやつと結合
                tmpsummary = value['summary']
                elem = soup.find(class_ = 'main__client')
                if elem != None:
                    summary = elem.get_text().strip()
                    value['summary'] = tmpsummary + '\n\n' + summary
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='main__items')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'main__name')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        # 被害組織説明(国名)
                        elem = i.find(class_ = 'main__country')
                        if elem != None:
                            summary = elem.get_text().strip()


                        # Cloakの詳細は特殊
                        # Expieredじゃないと詳細見れないのでチェック
                        elem = i.find(class_ = 'main__timer expired')
                        if elem != None:
                            # 詳細ページURL
                            elem= i.find(class_ = 'main__link')
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))
                                
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Lorenz(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='panel panel-default') + soup.find_all(class_='panel panel-primary')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find('h4')
                        if elem != None:
                            victimName = elem.get_text().strip()
                        elif i.attrs != None and len(i.attrs['class']) > 1 and 'panel-primary' in  i.attrs['class']:
                            elem = i.find('h3')
                            if elem != None:
                                victimName = elem.get_text().strip()

                        #　掲載時刻、更新時刻取得
                        elem = i.find(class_ = 'glyphicon glyphicon-time')
                        if elem != None and elem.next != None:
                            updateDate = elem.next.get_text().strip()

                        #　url
                        elem = i.find('a')
                        if elem != None:
                            urlStr = elem.get('href') 

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_CiphBit(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='post')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_='title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            urlStr = elem.get('href') 
                        
                        #　掲載時刻、更新時刻取得
                        elem = i.find('h5')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織説明
                        elems = i.find_all('p')
                        for elem in elems:
                            summary += elem.get_text().strip().replace('\n', '')

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

import json
def Func_scraping_AKIRA(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        # HTTP GETリクエストを送信
        # "leaks"ではなく"news"から取得すればOKっぽいので/nで取得
        # databaseUrl = urllib.parse.urljoin(url, '/l')
        databaseUrl = urllib.parse.urljoin(url, '/n')
        headers = {
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
        }

        groupLogger.log(groupName, 'Func_scraping_AKIRA_request', 'starting request to AKIRA API', {
            'url': databaseUrl,
            'headers': {
                'User-Agent': headers.get('User-Agent'),
                'Accept': headers.get('Accept')
            }
        })
        response = sb.getHtmlResponseByRequest(databaseUrl, headers=headers, verify=False, group_name=groupName)
        
        if response is None:
            groupLogger.log(groupName, 'Func_scraping_AKIRA_response', 'no response returned', {'url': databaseUrl})
            return retDict

        groupLogger.log(groupName, 'Func_scraping_AKIRA_response', 'received response', {
            'status_code': getattr(response, 'status_code', None),
            'reason': getattr(response, 'reason', None),
            'url': getattr(response, 'url', databaseUrl)
        })

        raw_bytes = response.content
        groupLogger.log(groupName, 'Func_scraping_AKIRA_raw', 'raw bytes retrieved', {'length': len(raw_bytes)})

        if len(raw_bytes) > 0:
            text = raw_bytes.decode("utf-8")
            dataArray = json.loads(text).get('objects', [])
     
            for i in dataArray:
                victimName = i.get('title', '').strip().replace('\n', '')
                if victimName:
                    summary = i.get('content', '').strip().replace('\n', '')
                    urlStr = ''
                    updateDate = i.get('date', '').strip().replace('\n', '')
                    detailUrl = ''

                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

        else:
            groupLogger.log(groupName, 'Func_scraping_AKIRA_raw', 'empty response body', {})
        # 戻す
        # wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_CryptBB(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            cards = soup.find_all(class_='list-group-item rounded-3 py-3 bg-body-secondary text-bg-dark mb-2 position-relative')

            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'stretched-link')

                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得 → マーケットなので値段いれとく。他に情報ないし
                    elems = i.find_all(class_ = 'small opacity-50')

                    if len(elems) > 0:
                        for  elem in elems:
                            summary = summary + elem.get_text().strip() + '\n'
                        summary = summary.strip()

                    # 被害組織HP取得
                    urlStr = ''
                    
                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'd-flex gap-2 small mt-1 opacity-25')

                    if elem != None:
                        updateDate = elem.get_text().strip()
                        
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ThreeAM(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            # cards = soup.find_all(class_='post bad') + soup.find_all(class_='post good')
            cards = soup.find_all(class_=re.compile('post (bad|good)'))
            
            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'post-title-block')
                    if elem != None:
                        victimName = elem.find('div').get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'post-text')
                    if elem != None:
                        summary = elem.get_text().strip()

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_LostTrust(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            # cards = soup.find_all(class_='post bad') + soup.find_all(class_='post good')
            cards = soup.find_all(class_='card shadow-sm border-info shadow-lg')
            
            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'card-header')
                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elem = i.find(class_ = 'card-body')
                    if elem != None:
                        summary = elem.get_text().strip()

                    # 掲載時刻、更新時刻取得
                    elem = i.find(class_ = 'text-muted')
                    if elem != None:
                        updateDate = elem.get_text().strip()

                    elem = i.find(class_ = 'btn-group d-flex')
                    if elem != None:
                        elems = elem.find_all('a')
                        if len(elems) > 1:
                            urlStr = elems[1].get('href') 
                            
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_HUNTERS_INTERNATIONAL(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'details ng-star-inserted')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            # 'https://hunters55rdxciehoqzwv7vgyv6nt37tbwax2reroyzxhou7my5ejyid.onion/api/public/companies'
            if driver != None:
                databaseUrl = urllib.parse.urljoin(url, '/api/public/companies')

                data = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if len(data) > 0:
                    for i in data:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        if i['title']:
                            victimName = i['title'].strip()

                            if i['website']:
                                urlStr = i['website'].strip()
                            if i.get('updated_at', 0):
                                updateDate = convert_epoch_to_datetime_string(i.get('updated_at', 0), milliseconds=False)
        
                            id = i.get('id', '')
                            if id != '':
                                detailUrl = urllib.parse.urljoin(url, f'/companies/{id}')

                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_V_IS_VENDETTA(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                i = soup.find(class_ = 'post')
                if i != None:
                    summary = i.get_text().strip()
                    value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_='post')
                
                if len(cards) > 0:
                    victimsCnt = 1
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        # elem = i.find(class_ = 'content')
                        # if elem != None:
                        #     victimName = elem.get_text().strip()

                        
                        # 被害組織説明取得
                        elem = i.find(class_ = 'text')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 詳細ページURL
                        elem = i.find('a')
                        if elem != None:
                            detailUrl = urllib.parse.urljoin(url, elem.get('href') )

                        # 詳細ページURLが被害組織名なのでそこから抜粋
                        # 最初のページで被害組織名取れないので
                        victimName = detailUrl.split('/')[-1]
                                
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_MEOW(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True

        else:
            if driver != None:
                # databaseUrl = urllib.parse.urljoin(url, '/api/public/companies')
                databaseUrl = 'http://meow6xanhzfci2gbkn3lmbqq7xjjufskkdfocqdngt3ltvzgqpsg5mid.onion/backend/post/getPosts?'

                data = Func_getJsonDataFromURL(groupName, driver, databaseUrl)
                dataArray = data.get('data', [])

                if len(dataArray) > 0:
                    for i in dataArray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        if i['title']:
                            victimName = i['title'].strip()
                            summary = i['description'].strip().replace('<p>', '\n')
                            updateDate = i['createdAt'].strip().replace('<p>', '\n')
                      
                            id = i.get('id', '')
                            if id != '':
                                detailUrl = urllib.parse.urljoin(url, f'/product/{id}')

                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_DAIXIN(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            cards = soup.find_all(class_='border border-warning card-body shadow-lg')
            
            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'border-danger card-title text-start text-white')
                    if elem != None:
                        victimName = elem.get_text().strip()
                    
                    # 被害組織説明取得
                    elems = i.find_all(class_ = 'card-text text-start text-white')
                    if len(elems) > 0:
                        for elem in elems:
                            if summary != '':
                                summary = summary + '\n\n' + elem.get_text().strip()
                            else:
                                summary = elem.get_text().strip()

                    # 詳細ページURL
                    elem = i.find(class_ = 'card-subtitle mb-2 text-muted text-start')
                    if elem != None and ('Web Site' in elem.get_text().strip()):
                        elem = elem.find("a")
                        if elem != None:
                            urlStr = urllib.parse.urljoin(url, elem.get('href'))
                            
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_SIEGEDSEC(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            table = soup.find('table', attrs={'id': 'DataTable'})
            
            if table != None:
                tableRows = table.find_all('tr')
                # 一番目はヘッダ
                if len(tableRows) > 0:
                    tableRows = tableRows[1:]
                
                for row in tableRows:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    columns = row.find_all(['td', 'th'])

                    column_texts = [col.text.strip() for col in columns]

                    victimName = column_texts[0]
                    summary = column_texts[2]
                    updateDate = column_texts[4]

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
      
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Cuba(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            if soup != None:
                i = soup.find(class_ = 'page-list-right')
                if i != None:
                    summary = i.get_text().strip()
                    value['summary'] = summary
        else:
            if driver != None:
                targetUrlArray = ['/ajax/page_free/', '/ajax/page_paid/']
                for urlItem in targetUrlArray:
                    pageCount = 0
                    while True: 
                        try:
                            targetUrl = urllib.parse.urljoin(url, f'{urlItem}{str(pageCount)}')
                            driver.get(targetUrl)

                            html = driver.page_source.encode('utf-8')
                            soup = BeautifulSoup(html, 'html.parser')

                            if soup != None:
                                cards = soup.find_all(class_='list-text')

                                if len(cards) > 0:
                                    for i in cards:
                                        victimName = ''
                                        summary = ''
                                        urlStr = ''
                                        updateDate = ''
                                        detailUrl = ''

                                        elem = i.find('a')
                                        if elem != None:
                                            detailUrl = elem.get('href') 
                                            detailUrl = urllib.parse.urljoin(url, detailUrl) 
                                            victimName = detailUrl.split('/')[-1]
                                            summary = elem.get_text().strip()

                                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                            if len(victimName) > 0:
                                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                                else:
                                    break
                            pageCount += 1
                        except Exception as e:
                            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_DragonForce(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if driver != None:
            databaseUrl = urllib.parse.urljoin(url, '/api/guest/blog/posts?page=1')

            data = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

            if len(data) > 0:
                dataArray = data['data']['publications']
                for i in dataArray:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    victimName = i.get('name','')
                    if victimName:
                        summary = i.get('description','')
                        summaryExtra = i.get('address','')
                        if summaryExtra:
                            summary += '\n\nAddress:'+ summaryExtra

                        urlStr = i.get('site','')
                        updateDate = convert_datetime_format(groupName, i.get('created_at',''))
        
                        id = i.get('id', '')
                        if id != '':
                            detailUrl = urllib.parse.urljoin(url, f'/companies/{id}')

                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            # 戻す
            wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_WEREWOLVES(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if soup != None:
            cards = soup.find_all(class_=re.compile('carts-section__item*'))
            
            if len(cards) > 0:
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    #　被害組織名取得
                    elem = i.find(class_ = 'cart-block__title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    elem = i.find(class_ = 'cart-block__content')
                    if elem != None:
                        summary = elem.get_text().strip()

                    elem = i.find(class_ = 'cart-block__bottom-date')
                    if elem != None:
                        updateDate = elem.get_text().strip()

                    elem = i.find('a')
                    if elem != None:
                        detailUrl = elem.get('href') 
                        detailUrl = urllib.parse.urljoin(url, detailUrl) 

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_NONAME(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            summary = ''
            if soup != None:
                i = soup.find(class_ = 'has-figtree-font-family has-small-font-size')
                if i != None:
                    summary = i.get_text().strip()
                    value['summary'] = summary
             
            elem = soup.find(class_ = 'has-fixed-layout')

            if elem != None:
                table_data = []
                for row in soup.find_all('tr'):
                    cols = row.find_all('td')
                    table_data.append([col.text.strip() for col in cols])

                if len(table_data) > 0:
                    strTmp = '\n'.join(' '.join(row) for row in table_data)

                    value['summary'] = summary + '\n\n' + strTmp
        else:
            if soup != None:
                cards = soup.find_all(class_='uagb-post__inner-wrap')
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'uagb-post__title uagb-post__text')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            # NEGOTIATEDの場合はなんの情報も取れないのでスキップ
                            if 'NEGOTIATED' in victimName:
                                continue

                            elem = elem.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 

                        elem = i.find(class_ = 'uagb-post__text uagb-post__excerpt')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_SLUG(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            summary = ''
            if soup != None:
                i = soup.find(class_ = 'post-content')
                if i != None:
                    summary = i.get_text().strip()
                    value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_='content')
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'post-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find('a')
                        if elem != None:
                            detailUrl = elem.get('href') 

                        elem = i.find(class_ = 'post-abstract')
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find(class_ = 'post-info')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_Omega(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai=False
        else:
            if soup != None:
                elem = soup.find_all(class_='datatable center')
                if elem != None:
                    table_data = []
                    for row in soup.find_all('tr'):
                        cols = row.find_all('td')
                        table_data.append([col.text.strip() for col in cols])

                    if len(table_data) > 1:
                        table_data = table_data[1:]

                        for item in table_data:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            victimName = item[0]
                            summary = item[2]
                            updateDate = item[4]

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                             retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_TRISEC(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            summary = ''
            if soup != None:
                main_element = soup.find('main')
                if main_element != None:
                    value['summary'] = text_lines = '\n'.join([element.text for element in main_element.find_all(recursive=False)])
        else:
            if soup != None:
                anchors = [a for td in soup.find_all('td') for a in td.find_all('a')]

                for elem in anchors:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    detailUrl = elem.get('href') 
                    if detailUrl != '#' and detailUrl != 'index.html':
                        victimName = elem.get_text().strip()
                        detailUrl = urllib.parse.urljoin(url, detailUrl) 

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ransomhub(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='post-content')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_="col-12 col-md-6 col-lg-4")
                    
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        cardHeader = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-title text-center")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find(class_="card-footer")
                        if elem != None:
                            updateDate = elem.get_text().strip()
                        
                        elem = i.find(class_="card-body")
                        if elem != None:
                            summary = getTextAll(groupName, elem)

                        elem = i.find('a')
                        if elem != None:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl) 

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_STORMOUS(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_='post-card')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h4')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find(class_='date')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find(class_='subtitle')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    finally:
        return retDict

def Func_scraping_STORMOUS_Portal(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     elem = soup.find(class_='content')
            #     if elem != None:
            #         value['summary'] = elem.get_text().strip()
        else:
            if soup != None:
                cards = soup.find_all(class_="w3-card-4 w3-margin info-box")

                for item in  cards:
                    
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = item.find('h3')
                    if elem:
                        victimName = elem.text.strip()
                        if victimName and len(victimName) > 0:
                            elems = item.find_all('a')
                            if elems:
                                urlStr = elems[0].get('href')
                                # detailUrl = urllib.parse.urljoin(url, detailUrl)  
                            
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    finally:
        return retDict
    
def Func_scraping_Mogilevich(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                contact = soup.find(class_="contact")

                if contact != None:
                    cards = soup.find_all('h3')
                    
                    if len(cards) > 0:
                        for i in cards:
                            victimName = ''
                            cardHeader = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            elems = i.find_all('a')

                            # タイトル（被害組織URL）と詳細用のアンカー
                            if len(elems) >= 2:
                                elem = elems[0]
                                victimName = elem.get_text().strip()
                                urlStr = elem.get('href')

                                elem = elems[1]
                                detailUrl = elem.get('href')

                            
                            elem = i.find('li')
                            if elem != None:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Blackout(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                def has_direct_text(tag):
                    if tag.string:  # Checks if the tag has a string directly
                        return True
                    if not any(tag.children):  # Checks if the tag has no children
                        return True
                    return False
                
                # 被害組織説明取得
                elem = soup.find(class_='d-flex flex-column justify-content-between')
                if elem != None:
                    texts = []
                    for element in elem.find_all(True):
                        if has_direct_text(element):
                            text = element.text.strip()
                            if text:
                                texts.append(text)

                    value['summary'] = '\n'.join(texts)
        else:
            if soup != None:
                cards = soup.find_all(class_=re.compile('card text-white.*'))
                    
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        cardHeader = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-header")
                        if elem != None:
                            victimName = elem.get_text().strip()
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                        elem = i.find(class_="card-body")
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find('a')
                        if elem != None:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl) 

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_MYDATA(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            summary = ''
            if soup != None:
                i = soup.find(class_ = 'news_div')
                if i != None:
                    summary = i.get_text().strip()
                    value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_='news_div')
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'a_title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl) 
       
                        summary = i.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

# def Func_scraping_MYDATA(driver, soup, groupName, url, forDetail, value):
#     retDict = {}
#     try:
#         if forDetail:
#             nanimoshinai = True
#         else:
#             if soup != None:
#                 cards = soup.find_all(class_='news_div')
                    
#                 if len(cards) > 0:
#                     for i in cards:
#                         victimName = ''
#                         cardHeader = ''
#                         summary = ''
#                         urlStr = ''
#                         updateDate = ''
#                         detailUrl = ''

#                         elem = i.find(class_='news_title')
#                         if elem != None:
#                             victimName = elem.get_text().strip()
#                             elem = i.find('a')
#                             if elem != None:
#                                 detailUrl = elem.get('href') 
#                                 detailUrl = urllib.parse.urljoin(url, detailUrl)

#                         texts = getTextAll(i)
#                         if texts:
#                             summary = '\n\n'.join(texts)

#                         # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
#                         if len(victimName) > 0:
#                             retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
#     except Exception as e:
#         Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

#     return retDict

def Func_scraping_Donex(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            summary = ''
            if soup != None:
                i = soup.find(class_ = 'post-md')
                if i != None:
                    summary = i.get_text().strip()
                    value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_='post')
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'post-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl) 

                        elem = i.find(class_ = 'post-except')
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find(class_ = 'post-date')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_KILLSEC(driver, soup, groupName, url, forDetail, value):

    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_=re.compile('post-block.*'))

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'post-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        detailUrl = i.get('href')
                        if detailUrl != None:
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                    
                        elem = i.find(class_ = 'post-block-text')
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_KILLSEC_2(driver, soup, groupName, url, forDetail, value):

    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')
            
            # summary = ''
            # if soup != None:
            #     i = soup.find('card')
            #     if i != None:
            #         summary = i.get_text().strip()
            #         value['summary'] = summary

        else:
            databaseUrl = 'http://ks5424y3wpr5zlug5c7i6svvxweinhbdcqcfnptkfcutrncfazzgz5id.onion/api/data-x7g9k2.php?force_db=1'
            databaseUrl = urllib.parse.urljoin(url, 'api/data-x7g9k2.php?force_db=1')
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
                "Accept": "*/*",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Referer": "http://ks5424y3wpr5zlug5c7i6svvxweinhbdcqcfnptkfcutrncfazzgz5id.onion/posts.php",
                "X-API-Token": "ks-blog-x7g9k2-2024",
                "Connection": "keep-alive"
            }

            response = sb.getHtmlResponseByRequest(databaseUrl, headers=headers, verify=False)

            raw_bytes = response.content
            if len(raw_bytes) > 0:
                text = raw_bytes.decode("utf-8")
                dataArray = json.loads(text).get('posts', [])
        
                for i in dataArray:
                    victimName = i.get('name', '').strip().replace('\n', ' ')
                    if victimName:
                        summary = i.get('description', '')
                        urlStr = i.get('domain', '')
                        updateDate = i.get('createdAt', '')
                        id_ = i.get('id', '')
                        # http://ks5424y3wpr5zlug5c7i6svvxweinhbdcqcfnptkfcutrncfazzgz5id.onion/?view=BTnGq2jhqB7xNEXgZIzfvxq5
                        detailUrl = urllib.parse.urljoin(url, f'/?view={id_}')
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict


def Func_scraping_RED_RANSOMEWARE(driver, soup, groupName, url, forDetail, value):

    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            if driver != None and soup != None:
                cards = soup.find_all(class_='card border border-warning')

                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        #　被害組織名取得
                        elem = i.find(class_ = 'card-header')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find(class_ = 'card-body')
                        if elem != None:
                            summary = elem.get_text().strip()    

                        elem = i.find(class_ = 'card-footer text-muted text-center')
                        if elem != None:
                            updateDate = elem.get_text().strip()       

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_DarkVault(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='post-company-content')
                if elem != None:
                    elem = elem.find(class_='desc')
                    if elem != None:
                        summaryTmp = elem.get_text().strip()
                        if len(summaryTmp) > 0:
                            summary = summaryTmp.strip().replace('\n','')
                        
                        if len(summary) > len(value['summary']):
                            value['summary'] = summary
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_=re.compile('post-block\s.*'))
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="post-title")
                        if elem != None:
                            victimNameTemp = elem.get_text()
                            if len(victimNameTemp) > 0:
                                victimName = victimNameTemp.strip()
                        
                        elem = i.find(class_="post-block-text")
                        if elem != None:
                            summaryTmp = elem.get_text().strip()
                            if len(summaryTmp) > 0:
                                summary = summaryTmp.strip().replace('\n','')
                            
                        urlStr = victimName
                        
                        elem = i.find(class_="updated-post-date")
                        if elem != None:
                            updateDateTmp = elem.get_text().strip()
                            if len(updateDateTmp) > 0:
                                updateDate = updateDateTmp.strip()

                        onclick_content = i.get('onclick')
                        url_match = re.search(r"go\('(.+)'\)", onclick_content)
                        if url_match:
                            # URLを取得
                            url_path = url_match.group(1)
                            if url_path:
                                detailUrl = urllib.parse.urljoin(url, url_path)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_HelloGookie(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elems = soup.find_all(class_="card-text")
                if elems != None and len(elems) > 1:
                    elem = elems[1]
                    summaryTmp = elem.get_text().strip()
                    if len(summaryTmp) > 0:
                        summary = summaryTmp.strip().replace('\n','')
                    
                    if len(summary) > len(value['summary']):
                        value['summary'] = summary
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_="card")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        elem = i.find(class_="card-text")
                        if elem != None:
                            summary = elem.get_text().strip()
                            
                        elem = i.find(class_="btn btn-primary")
                        if elem != None:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_QIULONG(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all('article')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="entry-title")
                        if elem != None:
                            victimName = elem.get_text().strip()

                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                # detailUrl = urllib.parse.urljoin(url, detailUrl)

                        elem = i.find(class_="entry-date published")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find(class_="entry-content")
                        if elem != None:
                            summary = getTextAll(groupName, elem)
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_APT73(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='offer__box__text')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_ = 'segment')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="segment__text__off")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if i['onclick']:
                            urlTmp = re.findall(r"'([^']*)'", i['onclick'])[0]
                            if urlTmp != None:
                                detailUrl = urllib.parse.urljoin(url, urlTmp)

                        elem = i.find(class_="segment__date")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find(class_="segment__text__dsc")
                        if elem != None:
                            summary = getTextAll(groupName, elem)
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_APT73_BASHEE(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='offer__box__text')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                elem = soup.find(class_ = 'segment__box')

                if elem:
                    # cards = soup.find_all(class_=re.compile('segment.*'))
                    cards = soup.find_all(class_='segment') 
                    if len(cards) > 0:
                        for i in cards:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            elem = i.find(class_="segment__text__off")
                            if elem != None:
                                victimName = elem.get_text().strip()

                            if i['onclick']:
                                urlTmp = re.findall(r"'([^']*)'", i['onclick'])[0]
                                if urlTmp != None:
                                    detailUrl = urllib.parse.urljoin(url, urlTmp)

                            elem = i.find(class_="segment__date")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            elem = i.find(class_="segment__text__dsc")
                            if elem != None:
                                summary = getTextAll(groupName, elem)
                                
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_EMBARGO(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinaiYooooooo = 0

        else:
            # AlphVは読み込み遅いのでJsonデータ直接とりいく
            # 1ページ目～3ページくらいはとっておく
            databaseUrlArray = ['/api/blog/get']

            for item in databaseUrlArray:
                databaseUrl = urllib.parse.urljoin(url, item)

                jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if len(jsonData) == 0:
                    break

                dataArray = jsonData

                for data in dataArray:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    victimName = data.get('comname', '')
                    comments = data.get('comments', '')
                    summary = data.get('descr', '') + '\n\n' + comments
                    updateDate = data.get('date_created', '')
                    
                    id = data.get('_id', -1)
                    if id > -1:
                        detailUrl = urllib.parse.urljoin(url, f'/#/post/{str(id)}')

                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

        wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Dispossessor(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinaiYooooooo = 0

        else:
            currentPage = 1
            # 一ページ目をとると何ページあるか取得できる
            databaseUrl = urllib.parse.urljoin(url, f'/back/getallblogs?search=&page=1')
            jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)
            if jsonData != None:
                totalPages = jsonData['data']['totalPages']

                # for currentPage in range(1,totalPages+1):
                for currentPage in range(1,2):
                    # 一ページ目はもう取得済みなのでやらない
                    if currentPage > 1:
                        databaseUrl = urllib.parse.urljoin(url, f'/back/getallblogs?search=&page={currentPage}')
                        jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                    if len(jsonData) == 0:
                        break

                    dataArray = jsonData['data']['items']
                    for data in dataArray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        victimName = data.get('company_name', '')
                        summary = data.get('description', '')
                        updateDate = data.get('uploaded_date', '')
                        
                        id = data.get('id', -1)
                        if id > -1:
                            detailUrl = urllib.parse.urljoin(url, f'/blogs/{str(id)}')

                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

        wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_dAn0n(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_="body")
                if elem:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_="card mb-3")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        elem = i.find(class_="card-text text-muted")
                        if elem != None:
                            summary = elem.get_text().strip()
                            
                        elem = i.find(class_="card-text h6")
                        if elem != None:
                            updateDate = elem.get_text().strip()
                            
                        elem = i.find(class_="btn btn-primary")
                        if elem != None:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
   
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_SpaceBears(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True

        else:
            if soup != None:
                cards = soup.find_all(class_="companies-list__item")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="name")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                            elem = elem.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 

                        elem = i.find(class_="text")
                        if elem != None:
                            summary = elem.get_text().strip()

                            elem = elem.find('a')
                            if elem != None:
                                urlStr = elem.get('href')
                            
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_AposSecurity(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                divs = soup.find_all('div', style=re.compile(r'border: 2px solid grey; border-radius: 7px; padding: 10px;.*'))
                
                for div in divs:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    # Company name
                    victimName = div.find('h2').text.strip()

                    if victimName:
                        try:
                            # Website, revenue, country
                            details = div.find_all('div', style=re.compile(r'grid-column: 1 / 3;.*font-size: 18px;.*'))[0].find_all('div')
                            urlStr = details[0].text.strip().replace('🌐 ', '')
                            # company['revenue'] = details[1].text.strip().replace('💲 ', '')
                            summary = details[2].text.strip().replace('📍 ', '')

                            # Description
                            summary = summary + '\n\n'+ div.find('div', style=re.compile(r'grid-column: 1 / 3;.*grid-row: 3 / 4;.*')).text.strip()

                            # Last update
                            updateDate = div.find('div', style=re.compile(r'grid-column: 1 / 3;.*grid-row: 4 / 5;.*')).text.strip().replace('🕑 Last update: ', '')
                        finally:
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_UNDERGROUND(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_="d-flex")
                if elem:
                    value['summary'] = getTextAll(groupName, elem)

                elem = soup.find(class_="filling")
                if elem:
                    value['summary'] = value['summary'] + '\n\n' + getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_="filling")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        # 特殊。一個目のblock__infoのしたの一個目のDivのpに会社名
                        elem = i.find(class_="block__info")
                        if elem != None:
                            elem = i.find('div')
                            if elem != None:
                                elem = i.find('p')
                                if elem != None:
                                    victimName = elem.get_text().strip()

                        if victimName:
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_INC_Ransom_New(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            # 'https://hunters55rdxciehoqzwv7vgyv6nt37tbwax2reroyzxhou7my5ejyid.onion/api/public/companies'
            if driver != None:
                # とりあえず100件分とってみる
                # databaseUrl = urllib.parse.urljoin(url, '/api/v1/blog/get/announcements?page=1&perPage=100')
                if 'INC_Ransom_New_Dark' == groupName:
                    databaseUrl = 'http://incbacg6bfwtrlzwdbqc55gsfl763s3twdtwhp27dzuik6s6rwdcityd.onion/api/v1/blog/get/announcements?page=1&perPage=100'
                else:
                    databaseUrl = 'http://incback.su/api/v1/blog/get/announcements?page=1&perPage=100'
                data = Func_getJsonDataFromURL(groupName, driver, databaseUrl)

                if len(data) > 0:
                    dataAarray = data['payload']['announcements']
                    for i in dataAarray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        companyBlock = i['company']
                        victimName = companyBlock['company_name']
                        victimName = urllib.parse.unquote(victimName)
                        if victimName:
                            country = companyBlock.get('country', '')

                            try:
                                revenue = str(companyBlock.get('revenue', ''))
                            except:
                                revenue = ''

                            if country:
                                summary = country + '\n'
                            if revenue:
                                summary = summary + revenue + '\n'

                            descriptionBlock = i.get('description', [])
                            if len(descriptionBlock) > 0:
                                summary = summary + '\n'.join(descriptionBlock)

                            # URLエンコードをデコードしてASCII文字に戻す
                            summary = urllib.parse.unquote(summary)
                            
                            if i.get('createdAt', 0):
                                updateDate = convert_epoch_to_datetime_string(i.get('createdAt', 0), milliseconds=True)
        
                            id = i.get('_id', '')
                            if id != '':
                                detailUrl = urllib.parse.urljoin(url, f'blog/disclosures/{id}')

                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_FSOCIETY(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_="ast-post-format- single-layout-1")
                if elem:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_="post-content ast-grid-common-col")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_="entry-title ast-blog-single-element")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                        elem = i.find(class_="ast-excerpt-container ast-blog-single-element")
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find(class_="posted-on")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ZeroTolerance(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai=True
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     elem = soup.find(class_="ast-post-format- single-layout-1")
            #     if elem:
            #         value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_="card")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_="text-center card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        parent_element = i.parent
                        if parent_element != None:
                            detailUrl = parent_element.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        elem = i.find(class_="text-center card-text")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elems = i.find_all(class_="card-text")
                        if elems != None and len(elems) >= 2:
                            summary = elems[1].get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ARCUS_MEDIA(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_="flex-grow max-w-full")
                if elem:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_="card-content")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_="entry-title mb-half-gutter last:mb-0")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                            elem = elem.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                
                        elem = i.find(class_="published")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find(class_="entry-excerpt yuki-raw-html mb-gutter last:mb-0")
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RED_RANSOMWARE(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai=True

        else:
            if soup != None:
                cards = soup.find_all(class_="p-2 w-25")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_="card-header")
                        if elem != None:
                            victimName = elem.get_text().strip()
                                
                        elem = i.find(class_="card-footer text-muted text-center")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find(class_="card-body")
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_HANDARA(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_="entry-content wp-block-post-content has-global-padding is-layout-constrained wp-block-post-content-is-layout-constrained")
                if elem:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_=re.compile('wp-block-post post.*'))
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_="wp-block-post-title")
                        if elem != None:
                            victimName = elem.get_text().strip()
                                
                            elem = elem.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 

                            elem = i.find(class_="wp-block-post-date")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            elem = i.find(class_="wp-block-post-excerpt__excerpt")
                            if elem != None:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                        
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

    
def Func_scraping_SenSayQ(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_='cls_scrollingInfo')
                if elem:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_='cls_record card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find('a')
                        if elem != None:
                            detailUrl = elem.get('href') 

                        elem = i.find(class_="cls_recordTop")
                        if elem != None:
                            victimName = elem.get_text().strip()

                            elem = i.find(class_="cls_recordMiddle")
                            if elem != None:
                                summary = urlStr = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                        
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_EL_DORADO(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     elem = soup.find(class_ = 'text-center')
            #     if elem != None:
            #         value['summary'] += '\n\n' + getTextAll(groupName, elem)

        else:
                elems = soup.find_all(class_='project')
                if len(elems) > 0:
                    for i in elems:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_="desc")
                        if elem != None:
                            summary = getTextAll(groupName, elem)
                            victimName = elem.find('h3').get_text().strip()

                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_EL_DORADO_old(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'text-center')
                if elem != None:
                    value['summary'] += '\n\n' + getTextAll(groupName, elem)

        else:
            if driver != None:
                index = 1
                while True:
                    if index > 1:
                        targetUrl = urllib.parse.urljoin(url, f'/page/{str(index)}/')
                        driver.get(targetUrl)

                        html = driver.page_source.encode('utf-8')
                        soup = BeautifulSoup(html, 'html.parser')

                    if soup:
                        index += 1
                        cards = soup.find_all(class_='lg:ml-8')
                        if len(cards) > 0:
                            for i in cards:
                                victimName = ''
                                summary = ''
                                urlStr = ''
                                updateDate = ''
                                detailUrl = ''
                                
                                elem = i.find('a')
                                if elem != None:
                                    detailUrl = elem.get('href') 

                                elem = i.find(class_="text-xl mb-2 text-decoration-underline")
                                if elem != None:
                                    victimName = elem.get_text().strip()

                                    elem = i.find(id="tags")
                                    if elem != None:
                                        summary = elem.get_text().strip()

                                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                    if len(victimName) > 0:
                                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                        else:
                            break
                    else:
                        break
                # 戻す
                wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_TRINITY(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True

        else:
            if driver != None and soup:
                cards = soup.find_all(class_='bg-secondary rounded h-60 p-4')
                
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        strongTags = soup.find_all('strong')

                        if len(strongTags) >= 5 and strongTags[4].next_sibling:
                            victimName = strongTags[4].next_sibling.strip()
                            if victimName:
                                summary = getTextAll(groupName, i)
                                updateDate = strongTags[2].next_sibling.strip()
                                urlStr = strongTags[0].next_sibling.strip()

                                elem = i.find('a')
                                if elem != None:
                                    detailUrl = elem.get('href') 
                                    detailUrl = urllib.parse.urljoin(url, detailUrl)

                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                if len(victimName) > 0:
                                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Cicada3301(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'pr-10 flex-grow')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if driver != None and soup:
                cards = soup.find_all(class_='w-full sm:w-1/2 md:w-1/2 lg:w-1/3 xl:w-1/3 px-6 mb-12')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elems = i.find_all('a')
                    if elems != None and len(elems) > 1:
                        detailUrl = elems[1].get('href') 
                        detailUrl = urllib.parse.urljoin(url, detailUrl)

                    elem = i.find(class_="font-bold text-yellow-500 mb-4 break-words uppercase")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_="mt-2 mb-1")
                        if elem != None:
                            elem = i.find('a')
                            if elem != None:
                                urlStr = elem.get('href') 

                        elem = i.find(class_="p-2 mt-1 text-gray-400 text-mg mb-6 overflow-y-auto whitespace-pre-wrap border border-gray-700 rounded-lg")
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
from datetime import datetime
def Func_scraping_PRYX(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find('body')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if driver != None and soup:
                cards = soup.find_all('a')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    detailUrl = i.get('href') 
                    detailUrl = urllib.parse.urljoin(url, detailUrl)

                    victimName = i.get_text().strip()

                    # 未公表は全て"[*] soon"になるっぽいのでカウントして後ろにわかるように数字つける
                    count = sum(1 for key in retDict if '[*] soon' in key)

                    if count > 0:
                        current_date = datetime.now()
                        formatted_date = current_date.strftime("%Y%m%d")
                        victimName = victimName + f'_{formatted_date}_{str(count)}(記載名重複のためのカウント)'

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    if len(victimName) > 0:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    

def Func_scraping_BrainCipher(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'card-body ql-editor')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if driver != None and soup:
                cards = soup.find_all(class_='card-body p-3 pt-2')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find('a')
                    if elem:
                        victimName = elem.get_text().strip()
                        detailUrl = elem.get('href') 

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_VanirGroup(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True

        else:
            if driver != None and soup:
                cards = soup.find_all(class_='sub-project m-30')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="main-content-heading")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find('a')
                        if elem != None:
                            urlStr = elem.get('href') 

                        summary = getTextAll(groupName, i)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RANSOMCORTEX(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'site-main')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup:
                cards = soup.find_all(class_='post-item-content')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="entry-title")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = elem.find('a')
                        if elem != None:
                            detailUrl = elem.get('href') 

                        elem = i.find(class_="post-content")
                        if elem != None:
                            summary = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict


def Func_scraping_NULLBULGE(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True

        else:
            if soup:
                cards = soup.find_all(class_='elem')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="hacked__font")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        summary = getTextAll(groupName, i)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_FOG(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True

        else:
            if soup:
                cards = soup.find_all(class_='mb-4 basis-1 last:mb-0')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="pb-4 text-lg font-bold")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_="flex justify-between pb-4 text-xs")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find('a')
                        if elem:
                            detailUrl = elem.get('href')
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_MAD_LIBERATOR(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True

        else:
            if soup:
                cards = soup.find_all(class_='col-md-6')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find('h3')
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_="blog-list--desc p-3 cnt")
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find('a')
                        if elem:
                            detailUrl = elem.get('href')
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_LYNX(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinaiYooooooo = 0

        else:
            # targetUrl = f'{url}/api/v1/blog/get/announcements?page=1&perPage=100'
            targetUrl = 'http://lynxblogco7r37jt7p5wrmfxzqze7ghxw6rihzkqc455qluacwotciyd.onion/api/v1/blog/get/announcements?page=1&perPage=100'
            jsonData = Func_getJsonDataFromURL(groupName, driver, targetUrl)
            dataArray = jsonData['payload']['announcements']
            for data in dataArray:
                victimName = ''
                summary = ''
                urlStr = ''
                updateDate = ''
                detailUrl = ''

                companyInfo = data.get('company', {})
                victimName = companyInfo['company_name']
                victimName = urllib.parse.unquote(victimName)
                country = companyInfo.get('country', '')

                summaryArray = data.get('description', '')
                summaryArrayTmp = []
                summaryArrayTmp.append(country)
                for i in summaryArray:
                    summaryArrayTmp.append(urllib.parse.unquote(i))

                summary = ('\n').join(summaryArrayTmp)

                updateDate = convert_epoch_to_datetime_string(data.get('leakAt', 0))

                detailUrlTmp = data.get('_id', '')
                if len(detailUrlTmp) > 0:
                    detailUrl = f'{url}/{detailUrlTmp}'

                if len(victimName) > 0:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

            # targetUrl = 'http://lynxba5y5juv3c4de2bftamjkbxvcuujr5c5wn4hq2fwmt66pxb7qqad.onion/api/v1/blog/get/news'
            # jsonData = Func_getJsonDataFromURL(groupName, driver, targetUrl)
            # dataArray = jsonData['payload']
            # for data in dataArray:
            #     victimName = data['title']
            #     victimName = urllib.parse.unquote(victimName)
            #     summaryArray = data['content']
            #     summaryArrayTmp = []
            #     for i in summaryArray:
            #         summaryArrayTmp.append(urllib.parse.unquote(i))
            #     summary = ('\n').join(summaryArrayTmp)

            #     updateDate = convert_epoch_to_datetime_string(data.get('1721827043298', 0))
            #     retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl, 'onlyDetailSnap':True}

        wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_HELLDOWN(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'post-content')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup:
                cards = soup.find_all(class_='card-container')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="card-title")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_="card-summary")
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find('a')
                        if elem:
                            detailUrl = elem.get('href')
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ValenciaRansomware(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'card-body')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup:
                cards = soup.find_all(class_='card-body')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="card-title")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_="btn btn-sm btn-outline-secondary custom-link")
                        if elem != None:
                            detailUrl = elem.get('href')
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Orca(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'card__description-content')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup:
                cards = soup.find_all(class_='blog__card')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_="blog__card-top-info-title")
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_="blog__card-description-text")
                        if elem != None:
                            summary = elem.get_text().strip()
                        
                        elem = i.find(class_="blog__card-details-item --blog__card-details-item-link --text-uppercase")
                        if elem != None:
                            elem = i.find('a')
                            if elem:
                                url = elem.get('href')
                                # detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        elem = i.find(class_="blog__card-top-date --small-title")
                        if elem != None:
                            elem = i.find('span')
                            if elem != None:
                                updateDate = elem.get_text().strip()
                        
                        elem = i.find(class_="blog__card-btn --button")
                        if elem != None:
                            detailUrl = elem.get('href')
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_NITROGEN(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            # 詳細ページはあるが現状何も表示されない
            nanimoshinai = True

        else:
            if soup:
                cards = soup.find_all(class_='w3-card-4 w3-margin w3-white w3-padding-16')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find('h3')
                    if elem != None:
                        victimName = elem.get_text().strip()

                        summary = getTextAll(groupName, i)

                        ankerArray = i.find_all('a')

                        if len(ankerArray) > 0:
                            urlStr = ankerArray[0].get('href')
                            if len(ankerArray) > 1:
                                detailUrl = ankerArray[1].get('href')
                                detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict


def Func_scraping_SARCOMA(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            # 詳細ページはあるが現状何も表示されない
            nanimoshinai = True

        else:
            if soup:
                # elem = soup.find('text-center text-white')
                # 動的に取ろうと思ったけどうまくいかないのでとりあえず先頭2ページ
                pages = [urllib.parse.urljoin(url, '/?page=1'), urllib.parse.urljoin(url, '/?page=2')]
                # if elem:
                #     elems = elem.find_all('a')
                #     if elems:
                #         for item in elems:
                #             pages.append(urllib.parse.urljoin(url, item.get('href')))
                
                for targetUrl in pages:
                    driver.get(targetUrl)
                    html = driver.page_source.encode('utf-8')
                    soup = BeautifulSoup(html, 'html.parser')

                    cards = soup.find_all(class_='card-body p-2')
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_='card-title text-center fs-5')
                        if elem != None:
                            elem = elem.find('hr')
                            if elem != None:
                                victimName = elem.next_sibling.strip()

                                elem = i.find(class_='card-text')
                                if elem != None:
                                    summary = elem.get_text().strip()

                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                if len(victimName) > 0:
                                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

        wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_INTERLOCK(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            # 詳細ページはあるが現状何も表示されない
            nanimoshinai = True

        else:
            if soup:
                cards = soup.find_all(class_='advert_col')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_='advert_info_title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                        elem = i.find(class_='advert_info_p')
                        if elem != None:
                            summary = elem.get_text().strip()

                            if elem:
                                elem = elem.get('a')
                                if elem:
                                    urlStr = elem.get('href')

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

    
def Func_scraping_PLAYBOY(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
                html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')

                if soup != None:
                    elem = soup.find(class_ = 'post-details')
                    if elem != None:
                        value['summary'] = getTextAll(groupName, elem)
        else:
            if soup:
                elem = soup.find(class_='home-body')

                if elem:
                    cards = elem.find_all(class_=re.compile('card-item.*'))
                    
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        elem = i.find(class_='card-title')
                        if elem != None:
                            victimName = elem.get_text().strip()

                            elem = i.find(class_='card-text')
                            if elem:
                                summary = getTextAll(groupName, i)

                            updateDate = convert_epoch_to_datetime_string(int(i['data-server-time']))

                            elem = i.find(class_='btn-primary')
                            if elem:
                                detailUrl = elem.get('href')
                                detailUrl = urllib.parse.urljoin(url, '/blog/'+detailUrl)
                            
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            if len(victimName) > 0:
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_KAIROS(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
                html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')

                if soup != None:
                    elem = soup.find(class_ = 'text-block')
                    if elem != None:
                        value['summary'] = getTextAll(groupName, elem)
        else:
            if soup:
                cards = soup.find_all(class_='card')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find('div', class_=re.compile('title*'))
                    if elem != None:
                        # .find() を使用して 'span' タグを除外し、テキストのみ取得する
                        victimName = elem.find(text=True, recursive=False).strip()

                        elem = i.find(class_='desc')
                        if elem:
                            summary = getTextAll(groupName, i)

                        elem = i.find(class_='date')
                        if elem:
                            updateDate = elem.get_text().strip()

                        detailUrl = i.get('href')
                        if detailUrl:
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_HELLCAT(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup:
                cards = soup.find_all(class_='post-head')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_='post-title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    if victimName:
                        elem = i.find(class_='domain')
                        if elem != None:
                            urlStr = elem.get_text().strip()

                        elem = i.find(class_='post-block-body')
                        if elem:
                            summary = getTextAll(groupName, i)

                        elem = i.find(class_='updated-post-date')
                        if elem:
                            updateDate = elem.get_text().strip()
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_CHORT(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup:
                cards = soup.find_all(class_='card-body')
                
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_='card-title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    if victimName:
                        summary = getTextAll(groupName, i)
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Termite(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup:
                # Find all card elements (each victim organization)
                cards = soup.find_all(class_='min-h-36')
                
                for card in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    try:
                        # Get victim name (h2 tag with font-bold class)
                        name_element = card.find('h2', class_='font-bold')
                        if name_element:
                            victimName = name_element.text.strip()
                            
                            # Get organization description (h3 tag with text-gray-500 class)
                            summary_element = card.find('h3', class_='text-sm text-gray-500 no-overflow')
                            if summary_element:
                                summary = summary_element.text.strip()
                                
                            # Get organization URL (same as h2 content, but clean it)
                            if name_element:
                                urlStr = name_element.text.strip()
                                if urlStr.startswith('https://'):
                                    urlStr = urlStr.strip()
                                    
                            # Get update date (div with ml-auto class)
                            date_element = card.find('div', class_='inline-flex items-end place-items-end ml-auto')
                            if date_element:
                                updateDate = date_element.text.strip()
                                
                            # Get detail page URL (href attribute of card)
                            # if card.get('href'):
                            #     detailUrl = url.rstrip('/') + card['href']
                                
                            # Store information if victim name exists
                            if len(victimName) > 0:
                                retDict[victimName] = {
                                    'updateDate': updateDate,
                                    'url': urlStr,
                                    'summary': summary,
                                    'detectedDate': uf.getDateTime('%Y/%m/%d %H:%M'),
                                    'detailUrl': detailUrl
                                }
                            
                    except Exception as e:
                        # Log individual card parsing errors but continue processing
                        Log.LoggingWithFormat(groupName, logCategory='E', 
                                           logtext=f'Card parsing error: {str(e)}')
                        continue
                        
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', 
                           logtext=f'args:{str(e.args)},msg:{str(e)}')
    
    return retDict

def Func_scraping_SAFEPAY(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
           nanimoshinai = True
        else:
            if soup:
                cards = soup.find_all(class_ = 'col-md-4 mb-4')
                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    elem = i.find(class_='card-title text-center mb-0')
                    if elem:
                        victimName = elem.text.strip()

                    if victimName:
                        elem = i.find(class_='card-text')
                        if elem:
                            summary = elem.text.strip()

                        elem = i.find(class_='btn btn-sm btn-primary')
                        if elem:
                            detailUrl = urllib.parse.urljoin(url, elem.get('href'))
   
                        retDict[victimName] = {
                            'updateDate': updateDate,
                            'url': urlStr,
                            'summary': summary,
                            'detectedDate': uf.getDateTime('%Y/%m/%d %H:%M'),
                            'detailUrl': detailUrl
                        }
                        
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', 
                        logtext=f'args:{str(e.args)},msg:{str(e)}')
    
    return retDict

def Func_scraping_Argonauts(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elems = soup.find_all(class_=re.compile('wp-block-column has-global-padding.*'))
                if elems != None:
                    value['summary'] = getTextAll(groupName, elems[0])
        else:
            if soup:
                cards = soup.find_all(class_=re.compile('wp-block-post post-.*'))

                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_='alignwide wp-block-post-title')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    if victimName:
                        elem = i.find(class_='wp-block-post-excerpt')
                        if elem:
                            summary = getTextAll(groupName, i)

                        elem = i.find('a')
                        if elem != None:
                            detailUrl = elem.get('href')   

                        elem = i.find(class_='wp-block-post-date')
                        if elem:
                            updateDate = elem.get_text().strip()
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', 
                        logtext=f'args:{str(e.args)},msg:{str(e)}')
    
    return retDict
    
def Func_scraping_Funksec(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'product-details')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup:
                cards = soup.find_all(class_='product-card')

                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find('h2')
                    if elem != None:
                        victimName = elem.get_text().strip()

                    if victimName:
                        detailUrl = urllib.parse.urljoin(url, i.get('href'))

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', 
                        logtext=f'args:{str(e.args)},msg:{str(e)}')
    
    return retDict
    
def Func_scraping_BLUEBOX(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find(class_ = 'article-entry')
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup:
                cards = soup.find_all(class_='post-wrapper')

                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_='shake shake-little')
                    if elem != None:
                        victimName = elem.get_text().strip()
                        detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                    if victimName:
                        elem = i.find(class_='meta meta_date')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', 
                        logtext=f'args:{str(e.args)},msg:{str(e)}')
    
    return retDict

def Func_scraping_Morpheus(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup:
                cards = soup.find_all(class_='post')

                for i in cards:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''
                    
                    elem = i.find(class_='post__header__title vkuiDiv vkuiRootComponent')
                    if elem != None:
                        victimName = elem.get_text().strip()
                        # detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                    if victimName:
                        elem = i.find(class_='post__text parsed-post-text vkuiDiv vkuiRootComponent')
                        if elem != None:
                            summary = elem.get_text().strip()

                            pArray = elem.find_all('p')
                            if pArray:
                                urlText = pArray[0].get_text().strip()
                                if urlText:
                                    urlStr = urlText.replace("Website: ", "").strip()

                        elem = i.find(class_='formatted-date')
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', 
                        logtext=f'args:{str(e.args)},msg:{str(e)}')
    
    return retDict

def Func_scraping_Kraken_HelloKitty(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_="container")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_="card")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        elem = i.find(class_="card-text")
                        if elem != None:
                            summary = elem.get_text().strip()
                            
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_GDLockerSec(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_="container")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_="card")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        elem = i.find(class_="card-text")
                        if elem != None:
                            summary = elem.get_text().strip()
                            
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Linkc(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_="article")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_="card")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="cart-text card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find(class_="card-text")
                        if elem != None:
                            updateDate = elem.get_text().strip()
                        
                        elem = i.find(class_="card-text card-description")
                        if elem != None:
                            summary = elem.get_text().strip()

                        elem = i.find(class_="card-logo")
                        if elem != None:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict


def Func_scraping_RunSomeWares(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_="section")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                # cards = soup.find_all(class_="post-block bad") + soup.find_all(class_="post-block good")
                cards = soup.find_all(class_="col")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="card-title")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        elem = i.find(class_="card-text")
                        if elem != None:
                            summary = elem.get_text().strip()
                        
                        elem = i.find('a')
                        if elem != None:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict


def Func_scraping_Secp0(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_="post post-in")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_="post")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="header-a")
                        noDetailUrl = False
                        if not elem:
                            elem = i.find("h2")
                            noDetailUrl = True
                        if elem != None:
                            victimName = elem.get_text().strip()

                            if not noDetailUrl:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                        elem = i.find(class_="metadata")
                        if elem != None:
                            updateDate = elem.get_text().strip()

                        elem = i.find(class_="text")
                        if elem != None:
                            summary = elem.get_text().strip()
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_SKIRA(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find("body")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

                    match = re.search(r'Website:\s*(https?://[^\s<]+)', value['summary'])
                    if match:
                        value['url'] = match.group(1)
        else:
            if soup != None:
                cards = soup.find_all("a")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        detailUrl = i.get('href') 
                        if detailUrl and detailUrl.startswith('/news/'):
                            victimName = i.get_text().strip()
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        if len(victimName) > 0:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Weyhro(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find("body")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

                    elems = elem.find_all("a")
                    for i in elems:
                        tmpText = i.get_text().strip()
                        if 'website' in tmpText.lower():
                            value['url'] = i.get('href') 
                            break

        else:
            if soup != None:
                cards = soup.find_all("a")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find("h2")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        if len(victimName) > 0:
                            detailUrl = i.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="flex justify-between gap-2 items-center")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            elem = i.find(class_="z-20 mt-4 text-sm  duration-1000 text-zinc-400 group-hover:text-zinc-200")
                            if elem != None:
                                summary = elem.get_text().strip()
                            
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict
    
def Func_scraping_CrazyHunterTeam(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find("flex-1")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if driver != None:
                # databaseUrl = urllib.parse.urljoin(url, ':8088/api/v1/product?page=')
                databaseUrl = url + ':8088/api/v1/product?page='

                data = Func_getJsonDataFromURL(groupName, driver, databaseUrl)
                data = data.get('data', {})
                if data:
                    dataArray = data.get('list', [])
                    for i in dataArray:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        victimName = i.get('productName','')
                        if victimName:
                            summary = i.get('productDesc','')
                            updateDate = convert_datetime_format(groupName, i.get('CreatedAt',''))
                            id = i.get('ID',0)
                            if id > 0:
                                detailUrl = urllib.parse.urljoin(url, f'/product/{id}')

                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Babuk2025(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "col mx-auto")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)

        else:
            if soup != None:
                cards = soup.find_all(class_ = "leak-card p-3")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find("h5")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        if len(victimName) > 0:
                            detailUrl = i.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="col-auto published")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            elem = i.find(class_="col-12")
                            if elem != None:
                                summary = elem.get_text().strip()
                            
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_NightSpire(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "description-container")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_=re.compile('^company-item.*'))
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="name")
                        if elem != None:
                            victimName = elem.get_text().strip()
                        
                        if len(victimName) > 0:
                            elem = i.find(class_="url")
                            if elem != None:
                                elem = i.find("a")
                                if elem != None:
                                     urlStr = elem.get('href') 

                            elem = i.find(class_="leak_at")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            value = i['dir']
                            # detailUrl = f'{url}?id={value}'
                            detailUrl = urllib.parse.urljoin(url, f'details.php?id={value}')

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_VanHelsing(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "card")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "card-body project-box")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="text-light")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="text-muted font-15")
                            if elem != None:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Mamona(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "card")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "card-body project-box")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_="text-light")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="text-muted font-15")
                            if elem != None:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Frag(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if driver and soup != None:
                pageNo = 1
                while True:
                    databaseUrl = f'http://34o4m3f26ucyeddzpf53bksy76wd737nf2fytslovwd3viac3by5chad.onion/tada/posts/leaks?page={str(pageNo)}'
                    jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)
                    items = jsonData.get('items', [])

                    if items:
                        for i in items:
                            victimName = i.get('title', '')
                            summary = i.get('text', '')
                            urlStr = ''
                            updateDate = i.get('date', '')
                            detailUrl = ''

                            if len(victimName) > 0:
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                    else:
                        break
                    pageNo += 1

                wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Arkana(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "ghost-content prose md:prose-lg prose-theme")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all('article')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('a')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            detailUrl = elem.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="text-sm text-typ-tone mt-2 mb-4")
                            if elem != None:
                                summary = elem.get_text().strip()

                            elem = i.find('time')
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RALord(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            pass
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'post-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'logo')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            victimName = victimName.replace('\u200b', '')

                            # detailUrl = elem.get('href') 
                            # detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="post-date")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            elem = i.find(class_="post-excerpt")
                            if elem != None:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_CHAOS2025(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
           nanimoshinai = True
        else:
            if driver != None:
                databaseUrl = 'http://hptqq2o2qjva7lcaaq67w36jihzivkaitkexorauw7b2yul2z6zozpqd.onion/api/post/list'

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Content-Type": "application/json",
                    "Host": "hptqq2o2qjva7lcaaq67w36jihzivkaitkexorauw7b2yul2z6zozpqd.onion",
                    "Origin": "http://hptqq2o2qjva7lcaaq67w36jihzivkaitkexorauw7b2yul2z6zozpqd.onion",
                    "Referer": "http://hptqq2o2qjva7lcaaq67w36jihzivkaitkexorauw7b2yul2z6zozpqd.onion/list"
                }

                # JSONペイロードを指定
                payload = {"page": 0}

                socks_port = sb.find_unused_port()
                sb.reset_tor_port()
                torProc, torConfFile = sb.start_tor(socks_port)
                session = sb.getSession(socks_port)

                response = session.post(databaseUrl, headers=headers, json=payload, verify=False, timeout=30)  # GETからPOSTに変更
                raw_bytes = response.content

                if len(raw_bytes) > 0:
                    text = raw_bytes.decode("utf-8")
                    data = [json.loads(line) for line in text.strip().split('\n')]
                    totalItems = data[0].get('totalItems', 0)
                    dataArray = data[0].get('items', [])
                    
                    # 返ってきたデータ数が合計より少なかったら
                    if len(dataArray) < totalItems:
                        current_page = 1  # 0起源なので次は1
                        
                        while len(dataArray) < totalItems:
                            # 次のページのペイロードを作成
                            next_payload = {"page": current_page}
                            
                            try:
                                # 次のページを取得
                                next_response = session.post(databaseUrl, headers=headers, json=next_payload, verify=False, timeout=30)
                                next_raw_bytes = next_response.content
                                
                                if len(next_raw_bytes) > 0:
                                    next_text = next_raw_bytes.decode("utf-8")
                                    next_data = [json.loads(line) for line in next_text.strip().split('\n')]
                                    next_items = next_data[0].get('items', [])
                                    
                                    # データがなくなったら終了
                                    if not next_items:
                                        break
                                    
                                    # データを追加
                                    dataArray.extend(next_items)
                                    print(f"Page {current_page}: {len(next_items)} items retrieved. Total: {len(dataArray)}/{totalItems}")
                                    
                                else:
                                    print(f"No data returned for page {current_page}")
                                    break
                                    
                            except Exception as e:
                                print(f"Error retrieving page {current_page}: {e}")
                                break
                            
                            current_page += 1
                            
                            # 無限ループ防止（オプション）
                            if current_page > 5:  # 適切な上限を設定
                                print("Maximum page limit reached")
                                break

                if torProc:
                    torProc.terminate()
                    torProc.wait()  # プロセスが終了するのを待つ

                sb.cleanup_torrc(torConfFile)

                for i in dataArray:
                    ignoreChk = i.get('h',-1)	
                    # hはおそらく公開までの残り時間なので、これがあるキーは無視（情報が何もないので）
                    if ignoreChk == -1:
                        victimName = i.get('title','')
                        summary =  i.get('text','')
                        urlStr = i.get('link','')
                        updateDate = ''
                        detailUrl = ''

                        if victimName:
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BERT(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
           
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "main")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if driver != None:
                databaseUrl = 'http://hahahasrzrdb6bbg6aoxbgd47fxd4icuvucncmeldsjgnvdzoze2egid.onion/api/publications/s'
                dataArray = Func_getJsonDataFromURL(groupName, driver, databaseUrl)
                for i in dataArray:
                    victimName = i.get('title','')
                    summary =  i.get('text','')
                    urlStr = i.get('link','')
                    updateDate = i.get('createdAt','')
                    detailUrl = ''
                    id = i.get('id','')

                    if id:
                        detailUrl = urllib.parse.urljoin(url, f'post/{id}')

                    if victimName:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    return retDict

def Func_scraping_DEVMAN(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     # elem = soup.find(class_='card-text')
            #     elem = soup.find(class_ = "post-content")
            #     if elem != None:
            #         value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'article')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            summary = getTextAll(groupName, i)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_CRYPTO24(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
           
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                # elem = soup.find(class_='card-text')
                elem = soup.find(class_ = "main")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if driver != None:
                databaseUrl = url + '/api/data'

                headers = {
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                    "Connection": "keep-alive",
                    "Referer": "http://j5o5y2feotmhvr7cbcp2j2ewayv5mn5zenl3joqwx67gtfchhezjznad.onion/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
                    # 必要であれば明示的に Host を上書き
                    # "Host": "j5o5y2feotmhvr7cbcp2j2ewayv5mn5zenl3joqwx67gtfchhezjznad.onion",
                }
                socks_port = sb.find_unused_port()
                sb.reset_tor_port()
                torProc, torConfFile = sb.start_tor(socks_port)  # Torを起動
                session = sb.getSession(socks_port)
                response = session.get(databaseUrl, headers=headers, verify=False, timeout=30)
                dataArray = response.json()

                if torProc:
                    torProc.terminate()
                    torProc.wait()  # プロセスが終了するのを待つ

                sb.cleanup_torrc(torConfFile)
                dataArray = dataArray.get('items', {})
                for i in dataArray:
                    victimName = i.get('company','')
                    summary = i.get('comment','')
                    urlStr = i.get('domain','')
                    updateDate = ''
                    detailUrl = ''
                    extraData1 = i.get('country','')

                    summary = extraData1 + '\n\n' + summary
                    
                    if victimName:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                # wrap_getURL(driver, url, groupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    return retDict

def Func_scraping_SatanLock(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "col mx-auto")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "leak-card p-3")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h5')
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            detailUrl = i.get('href') 
                            detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="col-12")
                            if elem != None:
                                summary = elem.get_text().strip()

                            elem = i.find(class_="col-auto published")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_AzzaSec(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "post-content formatted-content")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "post")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = "post-title")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            elem = elem.find('a') 
                            if elem:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_="post-content formatted-content")
                            if elem != None:
                                summary = elem.get_text().strip()

                            elem = i.find(class_="col-auto published")
                            if elem != None:
                                updateDate = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Gunra(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "col mx-auto")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all('div', class_='companyName')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                     # 会社名を取得
                        victimName = i.find('a').text.strip()
                        if victimName:
                            # 親ブロックを取得（各情報を含む）
                            parent_block = i.parent
                            if parent_block:
                                # industry, location, dueDateを取得
                                summary = parent_block.find('div', class_='industry').text.strip().replace('Industry: ', '') + '\n'
                                summary += parent_block.find('div', class_='location').text.strip().replace('Location: ', '') + '\n'
                                
                                # dueDateに関連する要素を取得（2つある）
                                due_dates = parent_block.find_all('div', class_='dueDate')
                                if due_dates:
                                    summary += due_dates[0].text.strip() + '\n'
                                    summary += due_dates[1].text.strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Silent(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
           nanimoshinai = True
        else:
            if driver != None:
                databaseUrl = url + '/api/company/?'
                jsonData = Func_getJsonDataFromURL(groupName, driver, databaseUrl)
                dataArray = jsonData.get('companies', [])
                for i in dataArray:
                    victimName = i.get('company_name','')
                    urlStr = i.get('link','')
                    updateDate = i.get('date','')
                    detailUrl = ''
                    id = i.get('id','')
                    summary =  i.get('comment','')
                    extraData1 = i.get('country','')
                    extraData2 = i.get('revenue','')

                    summary = extraData1 + '\n\n' + extraData2 + '\n\n' + summary

                    if id:
                        detailUrl = urllib.parse.urljoin(url, f'post/{id}')

                    if victimName:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                # 戻す
                wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')
    return retDict

def Func_scraping_J_GROUP(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "page-content")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_='post-item')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        # 会社名を取得
                        elem = i.find(class_ = "post-item-title")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if len(victimName) > 0:
                            elem = elem.find('a') 
                            if elem:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_ = "post-item-meta")
                            if elem != None:
                                updateDate = elem.get_text().strip()
                    
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_IMN_Crew(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_='content')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        # 会社名を取得
                        elem = i.find(class_ = "yellow-text")
                        if elem != None:
                            victimName = elem.get_text().strip()

                        if victimName:
                            elem = i.find('p')

                            if elem:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Anubis(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "ql-editor")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "col-sm-4 p-2")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elems = i.find_all('h5')
                        if elems != None:
                            victimName = elems[0].get_text().strip()
                            summary = elems[1].get_text().strip()

                        if len(victimName) > 0:
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_WORLDLEAKS(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            databaseUrl = urllib.parse.urljoin(url, 'api/companies')
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
                "Accept": "application/json, text/plain, */*"
            }
            response = sb.getHtmlResponseByRequest(databaseUrl, headers=headers, verify=False)
            
            raw_bytes = response.content
            if len(raw_bytes) > 0:
                text = raw_bytes.decode("utf-8")
                # dataArray = json.loads(text).get('objects', [])
                dataArray = [json.loads(line) for line in text.strip().split('\n')]

            for i in dataArray:
                victimName = i.get('title','')
                summary = ''
                urlStr = i.get('website','')
                updateDate = convert_epoch_to_datetime_string(i.get('updated_at', 0), milliseconds=False)
                itemId = i.get('id','')
                detailUrl = urllib.parse.urljoin(url, f'companies/{itemId}')
                extraData1 = i.get('country','')
                extraData2 = i.get('revenue','')
                summary = extraData1 + '\n\n' + str(extraData2)
                
                if victimName:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_DataCarry(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "ql-editor")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                elem_home = soup.find(class_ = "home")
                if elem_home:
                    cards = soup.find_all('a')
                    if len(cards) > 0:
                        for i in cards:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            elem = i.find('div')
                            if elem != None:
                                # 改行区切りで被害組織名と国コードが入っているので分ける
                                try:
                                    victimName = elem.contents[0]
                                    content = elem.contents[2]
                                    # 文字列（テキスト）かどうかをチェックしてから代入
                                    if isinstance(content, NavigableString):
                                        summary = content.strip()
                                except:
                                    victimName = elem.get_text()

                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_DireWolf(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "article-content")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] += f'\n\n{summary}'
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'article-content')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            elem = elem.find('a')
                            if elem != None:
                                detailUrl = elem.get('href') 
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                            elem = i.find(class_ = "date")
                            if elem:
                                updateDate = elem.get_text().strip()

                            elem = i.find('p')
                            if elem:
                                summary = elem.get_text().strip()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_SilentRansomGroup(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all('div', class_ = 'block_1')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        table = i.find('table')
                        if table:
                            extracted_data = {}

                            # すべてのtr要素を取得（コメントアウトされた行は自動的に除外される）
                            rows = table.find_all('tr')
                            
                            for row in rows:
                                cells = row.find_all('td')
                                if len(cells) >= 2:
                                    # 左側のセル（項目名）からテキストを取得し、コロンを除去
                                    key = cells[0].get_text(strip=True).rstrip(':')
                                    
                                    # 右側のセル（値）の処理
                                    value_cell = cells[1]
                                    
                                    if key == "COMPANY":
                                        # bタグ内のテキストを優先取得
                                        b_tag = value_cell.find('b')
                                        if b_tag:
                                            victimName = b_tag.get_text(strip=True)
                                        else:
                                            victimName = value_cell.get_text(strip=True)
                                    elif key != "DOWNLOAD LINK" and key != "STATUS":
                                        summary = value_cell.get_text(strip=True)
                                    
                                    # 辞書に追加
                                    extracted_data[key] = value

                            if victimName:
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_GLOBAL(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            databaseUrl = urllib.parse.urljoin(url, 'api/posts')
            socks_port = sb.find_unused_port()
            sb.reset_tor_port()
            torProc, torConfFile = sb.start_tor(socks_port)  # Torを起動
            session = sb.getSession(socks_port)
            # response = session.get(databaseUrl, headers=headers, verify=False, timeout=30)
            response = session.get(databaseUrl,  verify=False, timeout=30)
            raw_bytes = response.content
            if len(raw_bytes) > 0:
                text = raw_bytes.decode("utf-8")
                dataArray = [json.loads(line) for line in text.strip().split('\n')][0]

            if torProc:
                torProc.terminate()
                torProc.wait()  # プロセスが終了するのを待つ

            sb.cleanup_torrc(torConfFile)

            for i in dataArray:
                victimName = i.get('title','')
                summary = i.get('content','')
                urlStr = ''	
                updateDate = i.get('createdAt','')	
                detailUrl = ''
                
                if victimName:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_WALocker(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "detail-container fade-in")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] += f'\n\n{summary}'
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'company-card fade-in')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'company-name')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            if victimName:
                                elem = i.find(class_ = 'company-info')
                                if elem:
                                    summary = elem.get_text().strip()
                                
                                elem = i.find(class_ = 'website')
                                if elem:
                                    urlStr = elem.get_text().strip()

                                elem = i.find(class_ = 'date-item')
                                if elem:
                                    updateDate = elem.get_text().strip()

                                # onclick属性の取得
                                div = soup.find('div', class_='company-card')
                                if div:
                                    onclick = div.get('onclick')

                                    if onclick:
                                        # クオート部分からURLパスを抽出
                                        match = re.search(r"'(.*?)'", onclick)
                                        relative_url = match.group(1) if match else ''
                                       
                                        if relative_url:
                                            # フルURLに変換
                                            detailUrl = urllib.parse.urljoin(url, relative_url)
   
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Warlock(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            databaseUrl = urllib.parse.urljoin(url, 'api?action=get_public_clients')

            response = sb.getHtmlResponseByRequest(databaseUrl, headers=None, verify=False)

            raw_bytes = response.content
            if len(raw_bytes) > 0:
                text = raw_bytes.decode("utf-8")
                dataArray = json.loads(text)  
     
            for i in dataArray:
                victimName = i.get('name', '')
                summary = i.get('description', '')
                urlStr = ''
                updateDate = ''
                detailUrl = ''

                if victimName:
                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_TeamXXX(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(id = "TextColor")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'center1')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(id = 'father')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            if victimName:
                                elem = i.find(id = 'TextColor')
                                if elem:
                                    summary = elem.get_text().strip()

                                elem = soup.find('a', string='Read more')
                                if elem:
                                    detailUrl = elem.get('href') 
   
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Kawa4096(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        # HTTP GETリクエストを送信
        databaseUrl = 'http://kawasa2qo7345dt7ogxmx7qmn6z2hnwaoi3h5aeosupozkddqwp6lqqd.onion/js/leaks-data.min.5d25b254c76230cb3ecb79487e0957b21d3a1dc1197355900d4523678729b782.js'

        socks_port = sb.find_unused_port()
        sb.reset_tor_port()
        torProc, torConfFile = sb.start_tor(socks_port)  # Torを起動
        session = sb.getSession(socks_port)
        response = session.get(databaseUrl, headers=None, verify=False, timeout=30)
        match = re.search(r"leaks\s*=\s*(\[\{.*?\}\])", response.text)

        data = None
        if match:
            json_like_str = match.group(1)
            # JSONとしてパース
            import demjson3
            data = demjson3.decode(json_like_str)

        if torProc:
            torProc.terminate()
            torProc.wait()  # プロセスが終了するのを待つ

        sb.cleanup_torrc(torConfFile)

        if data:
            for i in data:
                victimName = i.get('title', '').strip().replace('\n', '')
                if victimName:
                    summary = i.get('description', '').strip().replace('\n', '')
                    urlStr = ''
                    updateDate = i.get('date', '').strip().replace('\n', '')
                    detailUrl = ''

                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

        # 戻す
        # wrap_getURL(driver, url, groupName)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Sinobi(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        # HTTP GETリクエストを送信
        databaseUrl = urllib.parse.urljoin(url, 'api/v1/blog/get/announcements?page=1&perPage=100')
        response = sb.getHtmlResponseByRequest(databaseUrl, headers=None, verify=False)
        
        raw_bytes = response.content
        if len(raw_bytes) > 0:
            text = raw_bytes.decode("utf-8")
            dataArray = json.loads(text)  

        if dataArray:
            data = dataArray.get('payload', {}).get('announcements', [])
            for i in data:
                companyDic = i.get('company', {})
                victimName = unquote(companyDic.get('company_name', '').strip().replace('\n', ''))
                country = unquote(companyDic.get('country', '').strip().replace('\n', ''))
		
                if victimName:
                    if country.lower() == 'jp':
                        country = 'Japan'

                    summary = country + '\n\n' + unquote(i.get('description', {})[0])
                    urlStr = ''
                    updateDate = convert_timestamp_to_datetime(groupName, str(i.get('createdAt', 0)))
                    detailUrl = ''
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_SATANLOCK_V2(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "article-content")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "leak-card")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('p')
                        if elem != None:
                            victimName = elem.get_text()

                        detailUrl = i.get('href')
                        if detailUrl != None:
                            detailUrl = urllib.parse.urljoin(url, detailUrl)
                        
                        elem = i.find(class_ = "published")
                        if elem != None:
                            updateDate = elem.get_text()

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_PayoutsKing(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "article-content")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                table_container = soup.find('div', id='table_container')
                
                tbody = soup.find('tbody', id='table')
                if tbody:
                    
                    # 各行を処理
                    for row in tbody.find_all('tr'):
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        
                        cells = row.find_all('td')
                        if len(cells) >= 9:  # 全カラムが存在する場合
                            victimName = cells[0].get_text(strip=True)
                            updateDate = cells[1].get_text(strip=True)
                            urlStr = cells[2].get_text(strip=True)
                            summary = cells[4].get_text(strip=True) #country
                            
                            # Company（リンクチェック）
                            # link = cells[1].find('a')
                            # if link:
                            #     row_data['company'] = link.get_text(strip=True)
                            #     row_data['detail_url'] = link.get('hx-post', '')
                            # else:
                            #     row_data['company'] = cells[1].get_text(strip=True)
                            #     row_data['detail_url'] = ''
                
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_D4RK4RMY(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "entry-content clear")
                if elem != None:
                    value['summary'] = getTextAll(groupName, elem)
        else:
            if soup != None:
                cards = soup.find_all(class_ = "ultp-block-content-wrap")
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'ultp-block-title')
                        if elem != None:
                            victimName = elem.get_text()
                            detailUrl = elem.get('href')

                            elem = i.find(class_ = 'ultp-block-excerpt')
                            if elem != None:
                                summary = elem.get_text()
                            
                            elem = i.find(class_ = "ultp-block-date ultp-block-meta-element")
                            if elem != None:
                                updateDate = elem.get_text()

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Securotrop(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                tbody = soup.find('tbody')

                # すべての行を取得
                rows = tbody.find_all('tr')

                # 各行を処理（ヘッダー行と区切り線の行をスキップ）
                for row in rows:
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    # td要素を持つ行のみ処理（ヘッダー行はthなのでスキップされる）
                    tds = row.find_all('td')
                    if len(tds) >= 5:  # データ行は5つのtd要素を持つ
                        # Name: 2番目のtdのリンクテキスト
                        victimName = tds[1].find('a').text.strip('/').strip()
                        
                        # Last Modified: 3番目のtdのテキスト
                        updateDate = tds[2].text.strip()
                        
                        # Description: 5番目のtdのテキスト（&nbsp;は空文字として扱う）
                        summary = tds[4].text.strip()
                        if summary == '\xa0' or summary == '':  # \xa0は&nbsp;
                            summary = ''
                        
                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BEAST(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "card-text")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'card hover-effect')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h3')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            if victimName:
                                elem = i.find(class_ = 'card-text')
                                if elem:
                                    summary = elem.get_text().strip()
                                
                                card_info = i.find('div', class_='card-info')
                                if card_info:
                                    updateDate = card_info.find('span', class_='date').text
                                    urlStr = card_info.find('span', class_='website').text

                                detailUrl = i.get('href')
                                if detailUrl != None:
                                    detailUrl = urllib.parse.urljoin(url, detailUrl)
   
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BQTLOCK(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'company-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h3')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            if victimName:
                                elem = i.find(class_ = 'company-info')
                                if elem:
                                    summary = elem.get_text().strip()
   
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_PEAR(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                # すべてのdetailsタグを取得
                details_elements = soup.find_all('details')
                
                for details in details_elements:
                    victim_info = {}
                    victimName = ''
                    summary = ''
                    urlStr = ''
                    updateDate = ''
                    detailUrl = ''

                    # summaryタグから基本情報を取得
                    summary = details.find('summary')
                    if summary:
                        # 企業名を取得（<u><strong>タグ内のテキスト）
                        name_tag = summary.find('u')
                        if name_tag:
                            victimName = name_tag.get_text(strip=True)
                        
                        # 日付を取得（企業名の後のspanタグ内）
                        date_span = summary.find('span', style=re.compile('color:#333333'))
                        if date_span:
                            updateDate = date_span.get_text(strip=True)
                        
                        # 説明文を取得（最初のpタグ）
                        summary_p = summary.find('p', style=re.compile('color:#333333.*font-size: 16px'))
                        if summary_p:
                            summary = summary_p.get_text(strip=True)
                        
                        # # ステータス（LeakedまたはSamples Posted）を取得
                        # status_p = summary.find('p', style=re.compile('color:#(1f820d|cc0000)'))
                        # if status_p:
                        #     victim_info['status'] = status_p.get_text(strip=True)
                    
                    # 詳細情報を含むpタグを取得
                    detail_p = details.find('p', style=re.compile('background-color:#ffffff'))
                    if detail_p:
                        detail_text = detail_p.get_text()
                        
                        # # 各フィールドを抽出
                        # # Site
                        # site_match = re.search(r'Site:\s*([^\n]+)', detail_text)
                        # if site_match:
                        #     urlStr = site_match.group(1).strip()
                        
                        # # Industry
                        # industry_match = re.search(r'Industry:\s*([^\n]+)', detail_text)
                        # if industry_match:
                        #     summary += '\n' + industry_match.group(1).strip()
                        
                        # # Location
                        # location_match = re.search(r'Location:\s*([^\n]+)', detail_text)
                        # if location_match:
                        #     summary += '\n' + location_match.group(1).strip()
                        
                        # # Revenue
                        # revenue_match = re.search(r'Revenue:\s*([^\n]+)', detail_text)
                        # if revenue_match:
                        #     summary += '\n' + revenue_match.group(1).strip()
                        
                        # # ダウンロードリンクを取得
                        # download_links = detail_p.find_all('a')
                        # victim_info['download_links'] = []
                        # for link in download_links:
                        #     link_text = link.get_text(strip=True)
                        #     victim_info['download_links'].append(link_text)
                        
                        # 全体のテキストも保存
                        summary += '\n' + detail_text.strip()
                    

                    # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BlackNevas(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        # HTTP GETリクエストを送信
        databaseUrl = urllib.parse.urljoin(url, 'api/publication')

        socks_port = sb.find_unused_port()
        sb.reset_tor_port()
        torProc, torConfFile = sb.start_tor(socks_port)  # Torを起動
        session = sb.getSession(socks_port)
        response = session.get(databaseUrl,  verify=False, timeout=30)
        raw_bytes = response.content
        if len(raw_bytes) > 0:
            text = raw_bytes.decode("utf-8")
            dataArray = json.loads(text)  

        if torProc:
            torProc.terminate()
            torProc.wait()  # プロセスが終了するのを待つ

        sb.cleanup_torrc(torConfFile)

        if dataArray:
            for i in dataArray:
                victimName = i.get('company', '')
		
                if victimName:
                    description = i.get('description', '')
                    soupTemp = BeautifulSoup(description, 'html.parser')
                    summary = soupTemp.get_text()
                    urlStr = ''
                    updateDate = i.get('createdAt', '')
                    id = i.get('id', '')
                    detailUrl = urllib.parse.urljoin(url, f'publications/details/{id}')

                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_LEAKNET(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "ql-editor")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        
                        value['summary'] = value['country'] + '\n\n' + summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'card-body')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        country = ''

                        elem = i.find(class_ = 'card-title')
                        if elem != None:
                            victimName = elem.get_text().strip()
                            if victimName:
                                elem = i.find(class_ = 'card-text')
                                if elem:
                                    summary = elem.get_text().strip()

                                elem = i.find(class_ = 'card-text mb-3 d-flex justify-content-center')
                                if elem:
                                    elems = elem.find_all(class_ = 'd-inline-block px-2')
                                    if elems and len(elems) > 2:
                                        country = elems[1].get_text().strip()
                                        urlStr = elems[2].get_text().strip()

                                        summary = country + '\n\n' + summary
                                
                                elem = i.find(class_ = 'card-text text-body-secondary small d-flex justify-content-center')
                                if elem:
                                    elems = elem.find_all(class_ = 'd-inline-block px-2')
                                    if elems and len(elems) > 1:
                                        updateDate = elems[0].get_text().strip()
                                        # urlStr = elems[1].get_text().strip()

                                elem = i.find(class_ = 'card-text text-center mb-4')
                                if elem:
                                    elem = elem.find('a')
                                    if elem:
                                        detailUrl = elem.get('href')
                                        if detailUrl != None:
                                            detailUrl = urllib.parse.urljoin(url, detailUrl)
   
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'country':country, 'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Cephalus(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "post_body scaleimages")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            databaseUrl = urllib.parse.urljoin(url, 'api/domains')
            socks_port = sb.find_unused_port()
            sb.reset_tor_port()
            torProc, torConfFile = sb.start_tor(socks_port)  # Torを起動
            session = sb.getSession(socks_port)
            response = session.get(databaseUrl,  verify=False, timeout=30)
            raw_bytes = response.content
            if len(raw_bytes) > 0:
                text = raw_bytes.decode("utf-8")
                dataArray = json.loads(text) 

            if torProc:
                torProc.terminate()
                torProc.wait()  # プロセスが終了するのを待つ

            sb.cleanup_torrc(torConfFile)

            for i in dataArray:
                victimName = i.get('company','')
                summary = i.get('description','')
                urlStr = i.get('domain','')
                updateDate = ''
                detailUrl =i.get('dataLink','')	
                	
                if victimName:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Desolator(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            if driver != None and soup != None:
                # databaseUrl = urllib.parse.urljoin(url, 'api/victims?page=1&rowsPerPage=9')
                databaseUrl = urllib.parse.urljoin(url, 'api/victims')
                response = sb.getHtmlResponseByRequest(databaseUrl)
                
                raw_bytes = response.content
                if len(raw_bytes) > 0:
                    text = raw_bytes.decode("utf-8")
                    dataArray = json.loads(text).get('victims', [])
        
                for i in dataArray:
                    victimName = i.get('display_name', '')
                    summary = ''
                    urlStr = ''
                    updateDate = i.get('infection_date', '')
                    detailUrl = ''
                    id = i.get('victim_id', '')

                    if id:
                        detailUrl = urllib.parse.urljoin(url, f'victim/{id}')

                    # さらに詳細ページもJsonが用意されてるので説明はそちらから取得
                    # http://po4tq2brx4rgwbdx4mac24fz34uuuf7oigosebp32n2462m2vxl6biqd.onion/api/victim/3f3f4013-f375-4279-8089-0a7d185b3fd6
                    detailJsonUrl = urllib.parse.urljoin(url, f'api/victim/{id}')
                    response = sb.getHtmlResponseByRequest(detailJsonUrl)
                    raw_bytes = response.content
                    if len(raw_bytes) > 0:
                        text = raw_bytes.decode("utf-8")
                        data = json.loads(text).get('victim', [])
                        summary = data.get('description', '').strip()

                    if victimName:
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Obscura(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            pass
        else:
            if soup != None:
                cards = soup.find_all(class_='card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''
                        country = ''

                        # 組織名称（タイトル） - h2タグから取得
                        elem = i.find(class_ = 'title')
                        if elem:
                            victimName = elem.get_text(strip=True)
                        
                        if victimName:
                            elem = i.find(class_ = 'domain')
                            if elem:
                                urlStr = elem.get_text(strip=True)

                            elem = i.find(class_ = 'created')
                            if elem:
                                updateDate = elem.get_text(strip=True)

                            elem = i.find(class_ = 'industry')
                            if elem:
                                summary = elem.get_text(strip=True)

                            elem = i.find(class_ = 'card-desc')
                            if elem:
                                summary = summary + '\n\n' + elem.get_text(strip=True)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'country':country, 'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Yurei(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "article-content")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'leak-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h5')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find('p')
                            if elem:
                                summary = elem.get_text(strip=True)
                        
                            detailUrl = i.get('href')
                            if detailUrl != None:
                                detailUrl = urllib.parse.urljoin(url, detailUrl)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Gentlemen(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            databaseUrl = urllib.parse.urljoin(url, 'api/companies')
            response = sb.getHtmlResponseByRequest(databaseUrl)
            if len(response.content) > 0:
                text = response.content.decode("utf-8")
                dataArray = json.loads(text) 

            for i in dataArray:
                victimName = i.get('title','')
                summary = i.get('description','')
                urlStr = ''
                updateDate = ''
                detailUrl = ''
                	
                if victimName:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RADAR(driver, soup, groupName, url, forDetail, value):
    retDict = {}

    try:
        if forDetail:
            nanimoshinai = True
        else:
            databaseUrl = urllib.parse.urljoin(url, '/api/leakeds_a')
            databaseUrl = 'http://3bnusfu2lgk5at43ceu7cdok5yv4gfbono2jv57ho74ucjvc7czirfid.onion/api/leakeds_a'
            response = sb.getHtmlResponseByRequest(databaseUrl)

            databaseUrl = 'http://3bnusfu2lgk5at43ceu7cdok5yv4gfbono2jv57ho74ucjvc7czirfid.onion/api/leakeds_u'
            responseWatingLeak = sb.getHtmlResponseByRequest(databaseUrl)

            dataArray = []
            if len(response.content) > 0:
                text = response.content.decode("utf-8")
                dataArray = json.loads(text) 

            if len(responseWatingLeak.content) > 0:
                text = responseWatingLeak.content.decode("utf-8")
                dataArray += json.loads(text) 

            for i in dataArray:
                victimName = i.get('company_name','')
                summary = i.get('description','')
                urlStr = i.get('website','')
                updateDate = i.get('created_at','')
                detailUrl = ''
                		
                if victimName:
                    retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
            
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_COINBASECARTEL(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'card-name')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'card-meta')
                            if elem:
                                summary = elem.get_text(strip=True)

                                elem = elem.find('a')
                                if elem:
                                    urlStr = elem.get('href')

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_LunaLock(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "prose content")
                if elem != None:
                    elem = elem.find('a')
                    if elem != None:
                        value['url'] = elem.get('href')
        else:
            if soup != None:
                cards = soup.find_all('article')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'mb-4 line-clamp-3 text-sm text-neutral-600')
                            if elem:
                                summary = elem.get_text(strip=True)
                            
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                            # elems = i.find_all('time')
                            # if elems:
                            #     updateDateTest = elems[0].get_text(strip=True)

                            elem = i.find('time')
                            if elem:
                                updateDate = elem.get_text(strip=True)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_BLACKSHRANTAC(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "book-card")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'book-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h3')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            detailUrl = i.get('data-href', '')

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_MIGA(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'victim')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('p')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_RADIANT(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "company-box")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'landing-text')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'company-title')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'company-description')
                            if elem != None:
                                summary = elem.get_text(strip=True)
                            
                            elem = i.find('a')
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_ARACHNA(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'post')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Scattered_LAPSUS_Hunters(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
            # html = driver.page_source.encode('utf-8')
            # soup = BeautifulSoup(html, 'html.parser')

            # if soup != None:
            #     # 被害組織説明取得
            #     elem = soup.find(class_ = "company-box")
            #     if elem != None:
            #         summary = getTextAll(groupName, elem)
            #         if len(summary):
            #             value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'bulba-banner')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'bulba-title')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'bulba-message')
                            if elem != None:
                                summary = elem.get_text(strip=True)

                        # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                        retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
                while True:
                    cards = soup.find_all(class_ = 'Magi-kard')
                    if len(cards) > 0:
                        for i in cards:
                            victimName = ''
                            summary = ''
                            urlStr = ''
                            updateDate = ''
                            detailUrl = ''

                            elem = i.find(class_ = 'vting-name')
                            if elem != None:
                                victimName = elem.get_text(strip=True)

                            if victimName:
                                elems = i.find_all(class_ = 'data-value')
                                if elems != None and len(elems) > 1:
                                    updateDate = elems[1].get_text(strip=True)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
                
                    next_button = driver.find_element(By.ID, "pager-next")
                    # 有効な場合のみクリック
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)
                    else:
                        break
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Kyber(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = "post-content")
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'post-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'post-header')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'post-excerpt')
                            if elem != None:
                                summary = elem.get_text(strip=True)

                            elem = i.find(class_ = 'post-footer')
                            if elem != None:
                                elem = elem.find('a')
                                if elem != None:
                                    detailUrl = urllib.parse.urljoin(url, elem.get('href'))
                            
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Kryptos(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'leak')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        block = i.find(class_ = 'locked')
                        if block:
                            elem = block.find('strong')
                            if elem != None:
                                victimName = elem.get_text(strip=True)

                            if victimName:
                                elem = block.find('em')
                                if elem != None:
                                    summary = elem.get_text(strip=True)

                                elem = block.find('code')
                                if elem != None:
                                    urlStr = elem.get_text(strip=True)
                                
                                # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                                retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Brotherhood(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            nanimoshinai = True
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'accordion-item border')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'accordion-header')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'accordion-body')
                            if elem != None:
                                summary = elem.get_text(strip=True)

                                elem = elem.find('a')
                                if elem != None:
                                    urlStr = elem.get('href')

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_NASIRSECUTRIY(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                elem = soup.find('h3')
                if elem != None:
                    value['updateDate'] = elem.get_text(strip=True)

                # 被害組織説明取得
                elem = soup.find(class_ = 'main')
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'news-content')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h3')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'news-summary')
                            if elem != None:
                                summary = elem.get_text(strip=True)

                            elem = i.find('a')
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))
                                    
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Genesis(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find('section')
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all('section')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'not-prose my-1 truncate')
                            if elem != None:
                                summary = elem.get_text(strip=True)

                            elem = i.find(class_ = 'text-sm antialiased opacity-60')
                            if elem != None:
                                updateDate = elem.get_text(strip=True)

                            elem = i.find('a')
                            if elem != None:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))
                                    
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_TENGU(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                elem = soup.find(class_ = 'content')
                if elem != None:
                    summary = getTextAll(groupName, elem)
                    if len(summary):
                        value['summary'] = summary
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h5')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find('p')
                            if elem != None:
                                summary = elem.get_text(strip=True)
                
                            detailUrl = urllib.parse.urljoin(url, i.get('href'))
                                    
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Kazu(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            pass
        else:
            if soup != None:
                cards = soup.find_all(class_ = 'database-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find(class_ = 'company-name')
                        if elem != None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find(class_ = 'company-url')
                            if elem != None:
                                summary = elem.get_text(strip=True)
                                    
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {'updateDate':updateDate, 'url': urlStr, 'summary':summary, 'detectedDate':uf.getDateTime('%Y/%m/%d %H:%M'), 'detailUrl':detailUrl}
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'args:{str(e.args)},msg:{str(e.msg)}')

    return retDict

def Func_scraping_Benzona(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            pass
        else:
            if soup is not None:
                cards = soup.find_all(class_='victim-card')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h3')
                        if elem is not None:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            # 「Leak Date」を含む <p> を探す
                            leak_p = None
                            for p in i.find_all('p'):
                                strong_tag = p.find('strong')
                                if strong_tag and 'Leak Date' in strong_tag.get_text():
                                    leak_p = p
                                    break

                            if leak_p is not None:
                                # 例: "<strong>Leak Date:</strong> 30.11.2025"
                                text = leak_p.get_text(" ", strip=True)
                                # 「Leak Date: 30.11.2025」→「30.11.2025」にする
                                if ':' in text:
                                    updateDate = text.split(':', 1)[1].strip()
                                else:
                                    updateDate = text

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,
                            # その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {
                                'updateDate': updateDate,
                                'url': urlStr,
                                'summary': summary,
                                'detectedDate': uf.getDateTime('%Y/%m/%d %H:%M'),
                                'detailUrl': detailUrl
                            }
    except Exception as e:
        Log.LoggingWithFormat(
            groupName,
            logCategory='E',
            logtext=f'args:{str(e.args)},msg:{str(e.msg)}'
        )

    return retDict

def Func_scraping_TridentLocker(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            if soup != None:
                # 被害組織説明取得
                    elem = soup.find(class_ = 'blog-article')
                    if elem != None:
                        summary = getTextAll(groupName, elem)
                        if len(summary):
                            value['summary'] = summary
        else:
            if soup is not None:
                cards = soup.find_all(class_='article')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            elem = i.find('p')
                            updateDate = elem.get_text(strip=True)
                            updateDate = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})',updateDate).group(0)
                            elem = i.find('a')
                            if elem:
                                detailUrl = urllib.parse.urljoin(url, elem.get('href'))
                            
                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,
                            # その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {
                                'updateDate': updateDate,
                                'url': urlStr,
                                'summary': summary,
                                'detectedDate': uf.getDateTime('%Y/%m/%d %H:%M'),
                                'detailUrl': detailUrl
                            }
    except Exception as e:
        Log.LoggingWithFormat(
            groupName,
            logCategory='E',
            logtext=f'args:{str(e.args)},msg:{str(e.msg)}'
        )

    return retDict


def Func_scraping_Minteye(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            pass
        else:
            if soup is not None:
                cards = soup.find_all('article')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        elem = i.find('h2')
                        if elem:
                            victimName = elem.get_text(strip=True)

                        if victimName:
                            p_children = i.find_all('p', recursive=False)
                            summary_candidates = [p.get_text(" ", strip=True) for p in p_children if p.get_text(strip=True)]
                            if summary_candidates:
                                summary = max(summary_candidates, key=len)

                            link_img = i.find('img', src=re.compile(r'link', re.IGNORECASE))
                            if link_img is not None:
                                link_p = link_img.find_parent('p')
                                if link_p is not None:
                                    link_text = link_p.get_text(" ", strip=True)
                                    m = re.search(r'(https?://[^\s]+|(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,})', link_text)
                                    if m:
                                        urlStr = m.group(0)

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,
                            # その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {
                                'updateDate': updateDate,
                                'url': urlStr,
                                'summary': summary,
                                'detectedDate': uf.getDateTime('%Y/%m/%d %H:%M'),
                                'detailUrl': detailUrl
                            }
    except Exception as e:
        Log.LoggingWithFormat(
            groupName,
            logCategory='E',
            logtext=f'args:{str(e.args)},msg:{str(e.msg)}'
        )

    return retDict

def Func_scraping_root(driver, soup, groupName, url, forDetail, value):
    retDict = {}
    try:
        if forDetail:
            pass
        else:
            if soup is not None:
                cards = soup.find_all('a')
                if len(cards) > 0:
                    for i in cards:
                        victimName = ''
                        summary = ''
                        urlStr = ''
                        updateDate = ''
                        detailUrl = ''

                        victimName = i.get_text(strip=True)
                        if victimName:

                            # 被害組織名,掲載時刻、更新時刻取得,被害組織説明,被害組織URL,
                            # その他情報(被害組織概要),詳細ページURL
                            retDict[victimName] = {
                                'updateDate': updateDate,
                                'url': urlStr,
                                'summary': summary,
                                'detectedDate': uf.getDateTime('%Y/%m/%d %H:%M'),
                                'detailUrl': detailUrl
                            }
    except Exception as e:
        Log.LoggingWithFormat(
            groupName,
            logCategory='E',
            logtext=f'args:{str(e.args)},msg:{str(e.msg)}'
        )

    return retDict
