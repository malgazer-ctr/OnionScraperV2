from ast import Or
import os
import sys
import re
import threading
import subprocess
import psutil
import time
import traceback
from datetime import datetime, timedelta
from string import Template
from PIL import Image
from tkinter.tix import COLUMN
from Config import Config as cf
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import GetHTML
from OnionScraperLib import Notification
from OnionScraperLib import Diff as df
from OnionScraperLib import SetupBrowser as sb
from OnionScraperLib import Log
from OnionScraperLib import GenerativeAI as ga
from OnionScraperLib import BoxAPI as ba
from OnionScraperLib import GroupLogger as groupLogger
from tkinter import messagebox,Tk
import cv2
import hashlib
import json

def log_branch(group_name, stage, decision, detail=None):
    groupLogger.log(group_name, stage, f'{decision}', detail)

g_groupName = ''

from collections import deque
# グローバルリスト：ハッシュ値を格納する
g_hash_records = deque(maxlen=200)  # 最大200件を記憶する
# 排他制御用のロック
g_hash_records_lock = threading.Lock()

# 各グループごとにログフォルダ作成するのでフォルダパスを保持
# tl_LogDirPath = threading.local()
# tl_AccessLog = threading.local()
# tl_RunningLog = threading.local()

from seleniumbase import Driver
from seleniumbase import page_actions
def wrap_SettingDriver(groupName, portForGroup, useSeleniumBase_uc, needHeadless, custom_headers):
    ret = None
    chromeService = None
    tempDir = ''

    for retryCnt in range(3):
        try:
            Log.LoggingWithFormat(groupName = groupName, logCategory = 'I', logtext = 'ドライバ取得開始', note = '')

            # debug用。消しちゃだめ
            if sb.headless_options == 2:
                sb.headless_options = 0
            else:
                if "conti" in groupName or\
                    uf.strstr('Babuk', groupName):
                    Log.LoggingWithFormat(groupName = groupName, logCategory = 'I', logtext = 'ヘッドレス無効の対象であるためヘッドレスを無効に設定', note = '')
                    sb.headless_options = 0
                else:
                    Log.LoggingWithFormat(groupName = groupName, logCategory = 'I', logtext = 'ヘッドレス有効に設定', note = '')
                    sb.headless_options = 1

            #Seleniumの設定とドライバーの準備
            if uf.strstr('Black_Shadow', groupName) or \
                uf.strstr('OSINT_corp', groupName) or \
                uf.strstr('MosesStaff', groupName):
                ret, tempDir = sb.Func_SettingDriver_Firefox(portForGroup,groupName,True,False)
                # ret = sb.Func_SettingDriver_Brave(groupName, TorEnable = False)

                cf.g_useFFDriver = True

            elif useSeleniumBase_uc:
                ret = Driver(uc=True)

            elif needHeadless == False or\
                uf.strstr('Black_Basta', groupName) or\
                 uf.strstr('HUNTERS_INTERNATIONAL', groupName) or\
                 uf.strcmp('8BASE_2', groupName) or\
                cf.headless_options == 2:
                ret, chromeService, tempDir = sb.Func_SettingDriver_Chrome(portForGroup,groupName,True,True, headless_options=False, custom_headers = custom_headers) 
                # ret = sb.Func_SettingDriver_Brave(groupName, TorEnable = True, headless = False)
            elif uf.strstr('WEREWOLVES', groupName):
                ret, chromeService, tempDir = sb.Func_SettingDriver_Chrome(portForGroup,groupName,True,False, custom_headers = custom_headers) 
            else:
                ret, chromeService, tempDir = sb.Func_SettingDriver_Chrome(portForGroup,groupName,True,True, custom_headers = custom_headers) 
                # ret = sb.Func_SettingDriver_Brave(groupName, TorEnable = True)

            if ret != None:
                break
        except Exception as e:
            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')
            if ret != None:
                ret.quit()
                ret = None

        if ret != None:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = 'ドライバ取得成功', note = '')
        else:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = 'ドライバ取得失敗', note = '')

    return ret, chromeService, tempDir

def wrap_getHTMLData(groupName, driver, url, excludeIgnoreText = False, groupConfig = {}):
    retOuterHtmlText = ''
    htmlData = ''
    victimsDict = {}
    IsIndivisialScrapingTarget = False
    retCode = cf.SUB_RETURNCODE_ERR
    try:
        htmlDataSize = 0
        threshold = getHtmlSizeThreshold(groupName)

        for i in range(3):
            driver.maximize_window()
            # HTML取得
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLData:{str(i+1)}回目')
            retOuterHtmlText, htmlData, victimsDict, IsIndivisialScrapingTarget, retCode = GetHTML.getHTMLData(driver, url, groupName, excludeIgnoreText, groupConfig)
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLData 終了:{str(i+1)}回目')

            htmlDataSize = len(htmlData)
            if htmlDataSize > threshold:
                break
            # HTML取得できたけど完全無視リストにひっかかった場合も抜ける
            # リトライで正常取得できる可能性もあるけどそれはここでリトライするより次回にかけることにしておく
            elif retCode & cf.SUB_RETURNCODE_GETHTML_IGNORE:
                break

        if htmlDataSize > 0:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'HTMLデータ取得成功')
        else:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'HTMLデータ取得失敗')

    except Exception as e:
        error_text = str(e.args)
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{error_text}')
        groupLogger.log(groupName, 'notify_error', 'exception in getHTMLDiffandNotification', {
            'error': error_text,
            'traceback': traceback.format_exc()
        })
        groupLogger.log(groupName, 'notify_error', 'exception in getHTMLDiffandNotification', {
            'error': error_text,
            'traceback': traceback.format_exc()
        })
    
    return retOuterHtmlText, htmlData, victimsDict, IsIndivisialScrapingTarget, retCode

def isOnlyLocationChanged(diffStr):
    ret = diffStr
    # +と-がついたものが\n区切りにくるはず
    diffStrArray = diffStr.splitlines()

    addStr = ''
    delStr = ''
    for line in diffStrArray:
        if line[0] == '+':
            addStr += line[2:]
        elif line[0] == '-':
            delStr += line[2:]

    if addStr == delStr:
        ret = ''

    return ret

def generateDiffDataHTML(resultFileBefore, resultFileAfter, groupName):
    diffPlane = ''
    difffHTML = ''
    diffFileSize_Before = 0
    diffFileSize_After = 0
    diffHTMLFilePath = ''
    diffPDFFilePath = ''

    try:
        if fo.Func_IsFileExist(resultFileBefore) == True and fo.Func_IsFileExist(resultFileAfter) == True:
            diffFileSize_Before = fo.Func_GetFileSize(resultFileBefore)
            diffFileSize_After = fo.Func_GetFileSize(resultFileAfter)
            
            if diffFileSize_Before > 0 or diffFileSize_After > 0:
                diffPlane = df.diff_Differ(resultFileBefore, resultFileAfter)

                # 差分が出たらHTML差分作成してメール
                if len(diffPlane) > 0:
                    diffPlane = excludeNoise2(diffPlane, groupName)

                    # ゴミをとりのぞいたあとで、+と-が順番変わっただけなえあ差分扱いしない
                    diffPlane = isOnlyLocationChanged(diffPlane)

                    if diffPlane != '':
                        # 差分UIのHTML生成
                        diffHTMLFilePath = os.path.join(cf.PATH_DIFFHTML_DIR, groupName + '_diff.html')
                        diffPDFFilePath = os.path.join(cf.PATH_DIFFPDF_DIR, groupName + '_diff.PDF')
                        difffHTML = df.diff_HTML(resultFileBefore, resultFileAfter)
                        # df.convertHTML2PDF(diffHTMLFilePath, diffPDFFilePath)

                        if len(difffHTML) > 0:
                            # diff_bodyTmp = uf.extractStrging('<body>', '</body>', difffHTML)

                            # 差分UIのテーブルヘッダに差分の取得時刻をセット
                            diffTime_before_ = fo.Func_GetFileUpdateTime(resultFileBefore)
                            diffTime_after_ = fo.Func_GetFileUpdateTime(resultFileAfter)
                            diffTableHeader = Template(cf.DATA_TEMPLATE_DIFFTABLEHEADER).substitute(diffTime_before = diffTime_before_, diffTime_after = diffTime_after_)
                            # を探して直前にヘッダを挿入
                            split_strings = difffHTML.split()
                            split_strings.insert(split_strings.index('<tbody>'), diffTableHeader)
                            difffHTML = ' '.join(split_strings)

                            fo.Func_WiteFile(diffHTMLFilePath, difffHTML)          

                        # # WinmergeでHtmlとか作成
                        # difffHTML = df.createWinmergeReport(resultFileBefore, resultFileAfter, os.path.join(cf.PATH_HTMLDIFF_DATA, groupName), requirePDF = False)
    except Exception as e:
        error_text = str(e.args)
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{error_text}')
        groupLogger.log(groupName, 'notify_error', 'exception in getHTMLDiffandNotification', {
            'error': error_text,
            'traceback': traceback.format_exc()
        })

    return diffPlane, difffHTML, diffFileSize_Before, diffFileSize_After, diffHTMLFilePath, diffPDFFilePath

def find_key_ignore_case(dictionary, key):
    try:
        for k in dictionary:
            # BianLianなどは＊＊＊の組織名があるので危ない
            # if re.match(k, key, re.IGNORECASE):
            if k.lower() == key.lower():
                return True
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')

    return False

def generateDiffDataDict(victimsDict, prevVictims):
    newItems = {}
    deletedItems = {}
    # 検知済みでも特定の条件で再度通知対象にしたい
    detectedItems = {}

    try:
        if len(prevVictims) > 0:
            # 今回取得した情報がすでに登録済みか探査
            for i in victimsDict.keys():
                # if (i in prevVictims) == False:
                if find_key_ignore_case(prevVictims, i) == False:
                    newItems[i] = victimsDict[i]
                # else:
                #     # 中身がかわってたらアップデートしたいかも？？
                #     if victimsDict[i]['summary'] != prevVictims[i].get('summary','')\
                #     or victimsDict[i]['updateDate'] != prevVictims[i].get('updateDate','')\
                #     or victimsDict[i]['detailUrl'] != prevVictims[i].get('detailUrl','')\
                #     or victimsDict[i]['url'] != prevVictims[i].get('url',''):
                #         detectedItems[i] = victimsDict[i]

            # 削除されたものがあるか探査
            for i in prevVictims.keys():
                # if (i in victimsDict) == False:
                if find_key_ignore_case(victimsDict, i) == False:
                    deletedItems[i] = prevVictims[i]
    except Exception as e:
        Log.LoggingWithFormat('groupName', logCategory = 'E', logtext = f'{str(e.args)}')
    
    return newItems, deletedItems,detectedItems

# ------------------------------------------------------------------
# 自分と関連性のあるグループがいたらそいつらのVictimsAll.jsonと比較して、
# 自分が取得した新規あつかいのものが存在しているか確認。
# 存在していたら自分は最新ではないのでファイルを上書きコピーして自分
# ------------------------------------------------------------------
# もし自分より新しい相対関係グループがいたらそいつのJsonをコピー
def mergeRelativeGroupVictimsData(groupName, relativeGroup):
    def parse_datetime(dt_str):
        return datetime.strptime(dt_str, '%Y/%m/%d %H:%M')
    
    try:
        if len(relativeGroup) > 0:
            file_victimsList = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsList.json')
            file_victimsListAll = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsListAll.json')
            victims_Prev = fo.Func_ReadJson2Dict(file_victimsList)
            victimsAll_Prev = fo.Func_ReadJson2Dict(file_victimsListAll)

            beforeCount = len(victims_Prev)
            beforeCountAll = len(victimsAll_Prev)
            for absolute in relativeGroup:
                file_victimsList_absolute = os.path.join(cf.PATH_HTMLDIFF_DATA, absolute + '_VictimsList.json')
                file_victimsListAll_absolute = os.path.join(cf.PATH_HTMLDIFF_DATA, absolute + '_VictimsListAll.json')
                victims_absolute = fo.Func_ReadJson2Dict(file_victimsList_absolute)
                victimsAll_absolute = fo.Func_ReadJson2Dict(file_victimsListAll_absolute)
                
                for key, value in victims_absolute.items():
                    if key in victims_Prev:
                        # 日付を比較し、新しい方を保持する
                        if parse_datetime(victims_Prev[key].get('detectedDate', '')) < parse_datetime(value.get('detectedDate', '')):
                            victims_Prev[key] = value
                    else:
                        victims_Prev[key] = value

                for key, value in victimsAll_absolute.items():
                    if key in victimsAll_Prev:
                        # 日付を比較し、新しい方を保持する
                        if parse_datetime(victimsAll_Prev[key].get('detectedDate', '')) < parse_datetime(value.get('detectedDate', '')):
                            victimsAll_Prev[key] = value
                    else:
                        victimsAll_Prev[key] = value

            if beforeCount < len(victims_Prev):
                fo.Func_WriteDict2Json(file_victimsList, victims_Prev)
            if beforeCountAll < len(victimsAll_Prev):
                fo.Func_WriteDict2Json(file_victimsListAll, victimsAll_Prev)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')


def generateDiffDataIndivisualInfo(groupName, victimsDict, relativeGroup = []):
    try:
        retCode = cf.SUB_RETURNCODE_ERR
        newItems = {}
        deletedItems = {}
        file_victimsListPrev = ''
        file_victimsListPrevTmp = ''
        allVictimsTmp = {}
        updateInfo = {}
        updateInfoDel = {}
        detectedItems = {}

        mergeRelativeGroupVictimsData(groupName, relativeGroup)

        if len(victimsDict) > 0:
            file_victimsListPrev = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsList.json')
            file_victimsListAll = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsListAll.json')
            file_victimsListPrevTmp = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsListTmp.json')
            
            # いったん添付ファイルとして記録しといてメール送り終わったら本物に置き換える
            # じゃないとこの処理～メールまでに何かあったときに、記録したものが通知されずに記録だけ残るため
            fo.Func_DeleteFile(file_victimsListPrevTmp)
            fo.Func_CopyFile(file_victimsListPrev, file_victimsListPrevTmp)
            prevVictims = fo.Func_ReadJson2Dict(file_victimsListPrevTmp)
            allVictims = fo.Func_ReadJson2Dict(file_victimsListAll)
            allVictimsTmp = allVictims.copy()
            prevVictimsTmp = prevVictims.copy()

            if len(prevVictims) > 0:
                newItems, deletedItems, detectedItems = generateDiffDataDict(victimsDict, prevVictims)
            else:
                # 新規取得時
                prevVictims.update(victimsDict)
                # allVictimsTmp.update(victimsDict)
                # 新規取得時も一応証跡残したいのでいったん全通知
                newItems.update(victimsDict)

            # 過去検知済みでもアップデート時に再度通知したい重要な組織は通知対象にし、情報を更新しておく
            searchTarget = fo.Func_CSVReadist(cf.IMPORTANTWORD_UPDATE_LIST_PATH)
            for targetWord in searchTarget:
                for key in detectedItems.keys():
                    if uf.strstr(targetWord[0], key):
                        newItems[key] = detectedItems[key]
                        # 最新の情報を入れたいので一度消しておく
                        del allVictims[key]
                        del allVictimsTmp[key]
                        updateInfo[key] = detectedItems[key]

                # 削除もう更新扱いにする→通常削除情報は重要フラグ立てないけどこのリストが空でなければ重要にする
                for key in deletedItems.keys():
                    if uf.strstr(targetWord[0], key):
                        updateInfoDel[key] = deletedItems[key]

            # 今回追加されたものを前回分Dictに追加
            if len(newItems) > 0:
                prevVictims.update(newItems)
                # allVictimsTmp.update(newItems)

                # 一度削除扱い（本当に削除されたケース、読み込み中断で削除扱いされたケース）されたアイテムにフラグ立てる
                # for key in newItems.keys():
                #     if key in allVictimsTmp.keys():
                #         newItems[key]['isDetected'] = True
                
                # 上はやめる。一度削除扱いされた過去検知済みのアイテムは新規として扱わない 2023/7/26
                newItemsTmp = newItems.copy()
                newItems.clear()

                for key in newItemsTmp.keys():
                    if (key in allVictimsTmp.keys()) == False:
                        newItems[key] = newItemsTmp[key]

                retCode |= cf.SUB_RETURNCODE_DIFF_INDIVISUAL

            # 今回削除されたものを前回分Dictから削除
            if len(deletedItems) > 0:
                for j in deletedItems.keys():
                    del prevVictims[j]
                retCode |= cf.SUB_RETURNCODE_DIFF_INDIVISUAL

            if (retCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL) == False:
                retCode |= cf.SUB_RETURNCODE_NODIFF_INDIVISUAL

            if len(prevVictims) > 0:
                for key in prevVictims.keys():
                    if (key in allVictims) == False:
                        allVictimsTmp[key] = prevVictims[key]

                # メール送信するまでやらないことにする 2023/8/31
                if allVictimsTmp != allVictims:
                    # 過去全ての情報を蓄積するファイルに書き込み
                    # fo.Func_WriteDict2Json(file_victimsListAll, allVictimsTmp)
                    NoCode = 0
                else:
                    allVictimsTmp.clear()

            if prevVictimsTmp != prevVictims:
                # 前回分の情報を保存するファイル
                fo.Func_WriteDict2Json(file_victimsListPrevTmp, prevVictims)

            retCode |= cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_SUCCESS
        else:
            # 個別に被害組織情報リストが取得できてない場合は構造変わってる可能性ある
            retCode |= cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return retCode, newItems, deletedItems, file_victimsListPrev, file_victimsListPrevTmp, allVictimsTmp, updateInfo, updateInfoDel

def generateScreenShotDiff(groupName, resultPNGBefore, resultPNGAfter):
    try:
        resultPNGBeforeTmp = ''
        resultPNGAfterTmp = ''
        resultPNGDiffTmp = ''
        makediff = False

        resultPNGBeforeTmp = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '_beforeTmp.jpeg')
        if fo.Func_IsFileExist(resultPNGBefore):
            makediff = True
            fo.Func_CopyFile(resultPNGBefore, resultPNGBeforeTmp)
        else:
            fo.Func_CopyFile(cf.PATH_ERR_SCREENSHOT, resultPNGBeforeTmp)
            
        uf.Func_Img_encode(resultPNGBeforeTmp)

        resultPNGAfterTmp = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '_afterTmp.jpeg')                    
        if fo.Func_IsFileExist(resultPNGAfter):
            fo.Func_CopyFile(resultPNGAfter, resultPNGAfterTmp)
        else:
            # 今回スクリーンショット取得失敗した場合、エラー画像を次回に回すためにresultPNGAfterとしてコピーしておく
            fo.Func_CopyFile(cf.PATH_ERR_SCREENSHOT, resultPNGAfter)
            fo.Func_CopyFile(cf.PATH_ERR_SCREENSHOT, resultPNGAfterTmp)
            resultPNGDiffTmp = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '_DiffTmp.jpeg')                    
            fo.Func_CopyFile(cf.PATH_ERR_SCREENSHOT, resultPNGDiffTmp)
            makediff = False

        uf.Func_Img_encode(resultPNGAfterTmp)

        if makediff:
            resultPNGDiffTmp = uf.CheckByImageDiff2(groupName, resultPNGBefore, resultPNGAfter)
        uf.Func_Img_encode(resultPNGDiffTmp)        
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return resultPNGBeforeTmp, resultPNGAfterTmp, resultPNGDiffTmp

def saveResultHtmlData(groupName, htmlData):
    try:
        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'Html保存処理開始')

        resultFileBefore = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_before.txt')
        resultFileAfter = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_after.txt')

        if len(htmlData) > 0:
            # Beforeがないときは新規追加したサイトのハズなのでBeforeを空で作成して取得したデータを差分としたい
            if fo.Func_IsFileExist(resultFileBefore) == False:
                fo.Func_WiteFile(resultFileBefore, '')

            resultFile = resultFileAfter

            fo.Func_WiteFile(resultFile, htmlData)

        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'Html保存処理終了')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return resultFileBefore, resultFileAfter

def saveResultOuterHtmltext(groupName, htmlText):
    try:
        retDstFilePath = ''
        if len(htmlText) > 0:
            dstDirPath = os.path.join(cf.PATH_OUTERHTML_TEXT, groupName)
            if not os.path.exists(dstDirPath): 
                fo.Func_CreateDirectry(dstDirPath)
            dateTime = uf.getDateTime('%Y%m%d_%H%M%S')
            retDstFilePath = os.path.join(dstDirPath, groupName + f'_OuterHtml_{dateTime}.txt')
       
            fo.Func_WiteFile(retDstFilePath, htmlText)

        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'Html保存処理終了')
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')
    finally:
        if len(retDstFilePath):
            uf.cleanup_box_files(retDstFilePath)

    return retDstFilePath

def saveScreenShot(groupName, driver):
    resultPNG_now = ''
    resultPNGBefore = ''
    resultPNGAfter = ''
    successScreenShot = False
    
    # スクショ取ってファイルに保存までこの関数でやる
    try:
        for i in range(5):
            resultPNG_now = GetHTML.getScreenShot(groupName, driver)
            if uf.IsWhiteOutImage(resultPNG_now) == False:
                successScreenShot = True
                break
            else:
                time.sleep(10)

        # getScreenShotで取得できてなければ無駄な処理しない
        # スクリーンショットで作成したファイル書き込みの終了が遅いかもなので最大10秒くらい待つ
        for cnt in range(10):
            if fo.Func_IsFileExist(resultPNG_now):
                resultPNGBefore = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '_before.png')
                resultPNGAfter = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '_after.png')
                
                # 初回取得時はBeforeないのでテンプレート使う
                if fo.Func_IsFileExist(resultPNGBefore) == False:
                    fo.Func_CopyFile(cf.PATH_FIRSTTIME_SCREENSHOT, resultPNGBefore)

                resultPNGFile = resultPNGAfter

                fo.Func_CopyFile(resultPNG_now, resultPNGFile)
                # GetHTML.Triming_Screenshotcreenshot(groupName, resultPNGFile)
                
                break
            else:
                time.sleep(1)

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return successScreenShot, resultPNG_now, resultPNGBefore, resultPNGAfter

def IsOnlyDeleted(str):
    ret = True

    lineArray = str.splitlines()

    # 先頭が - 始まりの行しか存在しないなら削除差分しかない
    for line in lineArray:
        if line.startswith('+ '):
            ret = False
            break
    
    return ret

#----------------------------------------------------------------------------------------------------------
# サイトごとのログをファイルに保存する関数
#----------------------------------------------------------------------------------------------------------
def uploadHtmlDataFile2Box(groupName, pathHtmlText, pathJson, savedOuterHtmlFile):
    groupFolderUrl = ''
    fileUrl = ''
    shareFolderLink = ''
    try:
        pathHtmlText_Tmp = ''
        pathJson_Tmp = ''

        dateTime = uf.getDateTime('%Y%m%d_%H%M%S')
        if fo.Func_IsFileExist(pathHtmlText):
            pathHtmlText_Tmp = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + f'_LeakSiteText_{dateTime}.txt')
            fo.Func_CopyFile(pathHtmlText, pathHtmlText_Tmp)
            groupFolderUrl, fileUrl, shareFolderLink = ba.BOX_UploadAccessLog(pathHtmlText_Tmp, groupName)
        
        if fo.Func_IsFileExist(pathJson):
            pathJson_Tmp = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + f'_VictimsData_{dateTime}.json')
            fo.Func_CopyFile(pathJson, pathJson_Tmp)       
            groupFolderUrl, fileUrl, shareFolderLink = ba.BOX_UploadAccessLog(pathJson_Tmp, groupName)

        if fo.Func_IsFileExist(savedOuterHtmlFile):
            groupFolderUrl, fileUrlTmp, shareFolderLink = ba.BOX_UploadAccessLog(savedOuterHtmlFile, groupName)


        # 最大１０秒くらいトライ（スレッドにしてもいいけどいったんさぼる）
        cnt = 0
        while True:
            try:
                fo.Func_DeleteFile(pathHtmlText_Tmp)
                fo.Func_DeleteFile(pathJson_Tmp)
                # savedOuterHtmlFileは作成時に古いのを削除しているのでここでは消さない

                break
            except:
                if cnt > 10:
                    break
                time.sleep(1)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return groupFolderUrl, fileUrl, shareFolderLink

def uploadLogFile2Box(groupName):
    groupFolderUrl = ''
    fileUrl = ''
    shareFolderLink = ''
    try:
        logFilePah = Log.getAccessLogPath(groupName)
            
        dateTime = uf.getDateTime('%Y%m%d_%H%M%S')
        # upLoadLogFilePah = os.path.join(os.path.join(cf.PATH_LOG_DIR, groupName), f'{groupName}_Access_{dateTime}.log')
        upLoadLogFilePah = logFilePah
        with cf.g_dicAccessLogLock[groupName]:
            # fo.Func_CopyFile(logFilePah, upLoadLogFilePah)
            # groupFolderUrl = グループごとのBOX上のフォルダ
            # fileUrl = アップロードしたログファイルのダウンロードリンク
            # shareFolderLink = Logs_HTMLDiffDetectSystem（共有フォルダの最上層）
            # ファイルのアップロード自体はグループ名「フォルダ > 日付フォルダ」にされる
            groupFolderUrl, fileUrl, shareFolderLink = ba.BOX_UploadAccessLog(upLoadLogFilePah, groupName)

        # 最大１０秒くらいトライ（スレッドにしてもいいけどいったんさぼる）
        cnt = 0
        while True:
            try:
                fo.Func_DeleteFile(upLoadLogFilePah)
                break
            except:
                if cnt > 10:
                    break
                time.sleep(1)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return groupFolderUrl, fileUrl, shareFolderLink

def sendAccessLog(targetGroupDic):
    try:
        accessLogStruct = Log.readAccessLogStruct('',cf.FILE_PATH_ACCESSLOG_GENERAL)
        lastSentTimeStr = accessLogStruct.get('sentMailTime', '')
        dateTimeNowStr = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)
        mailTo = cf.SENDTO_REPORT

        debug = False
        if debug == True:
            mailTo = cf.SENDTO_REPORT_YUICHI
            days_passed = 1
        else:
            if lastSentTimeStr != '':
                date_object = datetime.strptime(lastSentTimeStr, cf.ACCESSDATETIME_FORMAT)
                # 現在の日時との差を計算（日数）
                days_passed = (datetime.now() - date_object).days

                # Boxのファイル削除は30分おき
                hours_passed = (datetime.now() - date_object).seconds/60/60

                if hours_passed >= 0.5:
                    ba.deleteFromBOX()
                
                # 送信は1日一回
                if days_passed <= 0:
                    return
        
        dicForHtml = {}
        # メールに掲載するためのデータを読み込み
        # 各スレッドが書き込んでる可能性があるので、なんか読み込みおかしかったら排他処理いれる
        for groupName in targetGroupDic.keys():
            # 検知除外設定のグループはスキップ
            detectDiffSwitch = targetGroupDic[groupName].get('detectDiffSwitch', True)
            if detectDiffSwitch == False:
                continue

            dicForHtml[groupName] = {}

            # 各グループの差分検知スレッドでアップしたものがそのグループの最新のはずなので取得してみる。なければここでアップ
            groupFolderUrl = ''
            fileUrl = ''
            shareFolderLink = ''

            accessLogStruct_Group = Log.readAccessLogStruct(groupName, Log.getAccessLogPath(groupName))
            boxStatus = accessLogStruct_Group.get('boxStatus', {})
            if len(boxStatus) > 0:
                groupFolderUrl = boxStatus.get('box_groupFolderUrl', '')
                fileUrl = boxStatus.get('box_fileUrl', '')
                shareFolderLink = boxStatus.get('box_shareFolderLink', '')
            
            if groupFolderUrl == '' and fileUrl == '' and shareFolderLink == '':
                groupFolderUrl, fileUrl, shareFolderLink = uploadLogFile2Box(groupName)
                accessLogStruct_Group['boxStatus'] = {}
                accessLogStruct_Group['boxStatus']['box_groupFolderUrl'] = groupFolderUrl
                accessLogStruct_Group['boxStatus']['box_fileUrl'] = fileUrl
                accessLogStruct_Group['boxStatus']['box_shareFolderLink'] = shareFolderLink
                # Boxへアップロード終わったらもっかい保存
                Log.saveAccessLog2File(groupName, accessLogStruct, Log.getAccessLogPath(groupName))

            dicForHtml[groupName]['box_groupFolderUrl'] = groupFolderUrl
            dicForHtml[groupName]['box_fileUrl'] = fileUrl
            dicForHtml[groupName]['box_shareFolderLink'] = shareFolderLink

            urlList = targetGroupDic[groupName].get('urlList', [])
            if len(urlList) == 0:
                urlList.append(targetGroupDic[groupName].get('url', ''))

            dicForHtml[groupName]['url'] = '<br>'.join(urlList)
            dicForHtml[groupName]['SiteCategory'] = targetGroupDic[groupName].get('SiteCategory', '')

            accessLogGroup = Log.readAccessLogStruct(groupName, Log.getAccessLogPath(groupName))
            # 最終アクセス成功日時読み取り  
            lastAccessSuccessTime = accessLogGroup.get('lastAccessSuccessTime', '')
            dicForHtml[groupName]['lastAccessSuccessTime'] = lastAccessSuccessTime

            #  最終アクセス成功日時から現在は何日経過しているかを計算する。7日以上経過していたら非アクティブ
            # 日時データをdatetimeオブジェクトに変換
            if lastAccessSuccessTime != '':
                date_object = datetime.strptime(lastAccessSuccessTime, cf.ACCESSDATETIME_FORMAT)
                # 現在の日時との差を計算（日数）
                days_passed = (datetime.now() - date_object).days
            else:
                # 不明扱いしとく
                days_passed = -1

            if days_passed > 6:
                dicForHtml[groupName]['IsActive'] = f'×({str(days_passed)}日)'
            elif days_passed == -1:
                dicForHtml[groupName]['IsActive'] = '△'
            else:
                dicForHtml[groupName]['IsActive'] = '○'

            # レポートメールには３件ずつくらい乗せる
            # accessLogDataArrayの先頭から新しい順
            # リストの長さと3のうち小さい方を取得
            accessLogDataArray = accessLogGroup.get('log', [])
            max_index = min(len(accessLogDataArray), 3)

            # 最初の3つの要素、または利用可能な要素までをループする
            for i in range(max_index):
                keyName = f'lastAccess-{str(i)}'    
                dicForHtml[groupName][keyName] = accessLogDataArray[i].get('accessEndTime', '')

                keyName = f'accessStatus-{str(i)}'    
                status = accessLogDataArray[i].get('getHTMLStatus', '')
                if status == '':
                    dicForHtml[groupName][keyName] = '-'
                elif uf.strstr('成功', status):
                    dicForHtml[groupName][keyName] = '○'
                else:
                    dicForHtml[groupName][keyName] = '×'

        bodyStr = Notification.createNotificationBody_AccessLogReport(dicForHtml)

        sendSuccess = Notification.sendMail_Nofication(bodyStr, f'[V2]【アクセスログ】', mailTo, isUrgent=False)

        if sendSuccess:
            accessLogStruct['sentMailTime'] = dateTimeNowStr
            Log.saveAccessLog2File('', accessLogStruct, cf.FILE_PATH_ACCESSLOG_GENERAL)

    except Exception as e:
        Log.LoggingWithFormat('MainProc', logCategory = 'E', logtext = f'{str(e.args)}')

# stockGen:何世代前まで残すか
def deleteScreenShotFiles(groupName, stockGen, directory = cf.PATH_SCREENSHOT_DIR):
    def enumScreenShotFile(groupName, directory):
        def list_filesAndDate(directory, pattern):
            matched_files = []
            for filename in os.listdir(directory):
                if re.match(pattern, filename):
                    date = os.path.getmtime(os.path.join(directory, filename))
                    matched_files.append([filename, date])
            return matched_files

        # ディレクトリとパターンを指定
        pattern = groupName+r'_\d{12}.(png|jpg|jpeg)'  # YYYYMMDDHHMMの形式

        # ファイルのリストを取得
        files_with_dates = list_filesAndDate(directory, pattern)

        # 若い順に並べる
        sorted_files = sorted(files_with_dates, key=lambda x: x[1], reverse=True)

        sorted_file_paths = [file[0] for file in sorted_files]

        return sorted_file_paths
    
    files = enumScreenShotFile(groupName, directory)

    for file in files[stockGen:]:
        fo.Func_DeleteFile(os.path.join(directory, file))

def investigateVictimsInfoAI(groupName, victimsName, victimsURL):
    retDict = {}
    try:    
        # *や？が複数含まれる組織はChatGptにかけない(3割以上対象の記号が入ってたら)
        kigouCount = 0
        kigouArray = ['*', '?']
        for char in victimsName:
            if char in kigouArray:
                kigouCount += 1

        percentage = kigouCount/len(victimsName)
        if percentage < 0.3:
            retDict = ga.requestVictimsInfo_ChatGPT(victimsName, victimsURL)

    except Exception as e:
        Log.LoggingWithFormat('MainProc', logCategory = 'E', logtext = f'{str(e.args)}')

    return retDict

def wrap_isSentence_ChatGPT(victimsName):
    ret = ''
    try:    
        ret = ga.isExtortioneSentence_ChatGPT(victimsName)
    except Exception as e:
        Log.LoggingWithFormat('MainProc', logCategory = 'E', logtext = f'{str(e.args)}')

    return ret

# HTML情報が取得できないサイトが過去アクセスできていたか確認。
# 直近5回のうち一度でもアクセスできていたならアクセス不可になった可能性。
def isAccessStatusChanged(groupName, isChange2Deny):
    ret = False
    try:
        accessLogArray = Log.readAccessLog(groupName, Log.getAccessLogPath(groupName))

        # アクセスできてた→アクセス不可になったかをチェック
        if isChange2Deny:
            judge = False
            # 接続履歴が件以上あり、直近20件は取得サイズが0の場合、接続不可になった可能性。
            if len(accessLogArray) >= 30:
                judge = True
                for i in range(20):
                    if accessLogArray[i]['htmlSize'] > 0:
                        judge = False
                        break

                if judge:
                    # 21件目から30件目に接続成功してたら接続不可になった判定
                    for i in range(21, 30):
                        if accessLogArray[i]['htmlSize'] > 0:
                            ret = True

    except Exception as e:
        Log.LoggingWithFormat('MainProc', logCategory = 'E', logtext = f'{str(e.args)}')

    return ret


# excludeNoiseでは+-のセットで見るようにしてたけど
# +-にかかわらず一行ずつチェックしていらなそうなものあったら差分からはじく
def excludeNoise2(diffStr, groupName = ''):
    try:
        ret = diffStr

        excludeWordJson = fo.Func_ReadJson2Dict(cf.PATH_EXCLUDEDIFF_LIST)

        #　改行コードを空にして正規表現チェッカーにかける
        lineArray = diffStr.splitlines()

        retTmp = []

        # patternキーに配列として除外ワードの一覧が入っている
        excludeWordList = excludeWordJson['pattern']

        # + と - をセットの配列にする
        for line in lineArray:
            # 頭についてる+-とスペース外す
            lineTmp = line[2:]
            chkRet = False

            i = 0
            for i in range(len(excludeWordList)):
                isUseRegExp = excludeWordList[i]['regExp']
                pattern = excludeWordList[i]['word']
                isTargetGroup = True

                if groupName != '':
                    if 'groupNames' in excludeWordList[i]:
                        groupNameArray = excludeWordList[i]['groupNames']
                        if (groupName in groupNameArray) == False:
                            isTargetGroup = False

                if isTargetGroup:
                    if isUseRegExp:
                        if re.match(pattern, lineTmp) != None:
                            chkRet = True
                            break
                    else:
                        if pattern.lower() == lineTmp.lower():
                            chkRet = True
                            break

            # 該当するものがあったら無視。なければ返す
            if chkRet == False:
                retTmp.append(line)

        if len(retTmp) > 0:
            ret = '\n'.join(retTmp)
        else:
            ret = ''

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return ret

def getHtmlSizeThreshold(groupName):
    threshold = 0
    try:
        
        # 読み込みが不安定なサイトがあるので、過去のアクセスログからHTMLサイズを取得し、過去５回のなかでサイズが一番大きいものを取得
        # （過去三回のデータがなければそのまま通知）
        # 今回の取得サイズがそのサイズの半分以下なら明らかに読み込めてない可能性があるのでリトライ（3回まで）。
        # それでもだめなら通常通り通知
        accessLogArray = Log.readAccessLog(groupName, Log.getAccessLogPath(groupName))

        if len(accessLogArray) >= 5:
            for i in range(5):
                threshold_Tmp = accessLogArray[i].get('htmlSize', 0)

                if threshold < threshold_Tmp:
                    threshold = threshold_Tmp
        threshold = threshold * 0.5
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return threshold

def isKnownHtml(groupName, htmlData):
    knownHtml = False

    try:
        if len(htmlData) > 0:
            hashListPath = os.path.join(cf.PATH_HTMLDIFF_DATA, f'{groupName}_HashList.csv')
            hashStr = uf.string_to_sha256(htmlData)

            existHashList = fo.Func_CSVReadist(hashListPath)

            for sublist in existHashList:
                if hashStr in sublist:
                    knownHtml = True
                    break

            if knownHtml == False:
                existHashList.insert(0, [hashStr])

                if len(existHashList) > 100:
                    existHashList.pop()

                fo.Func_CSVWriteList(hashListPath, existHashList)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

    return knownHtml

def generate_and_check_dict_hash_thread_safe(data: dict, extra_list: list) -> bool:
    """
    マルチスレッド環境で辞書とリストを元にハッシュ値を生成し、重複をチェックする関数。
    200件を超えた場合は古いものを自動的に削除。
    
    Parameters:
        data (dict): ハッシュ化したい辞書
        extra_list (list): ハッシュ化したいリスト
    
    Returns:
        bool: Trueなら新しいハッシュでリストに追加。Falseなら既存のハッシュが発見された。
    """
    global g_hash_records
    global g_hash_records_lock

    # 辞書とリストを結合し、JSON文字列に変換
    combined_data = json.dumps({"dict": data, "list": extra_list}, sort_keys=True)
    
    # ハッシュ値を生成（SHA256を使用）
    hash_object = hashlib.sha256(combined_data.encode())
    hash_value = hash_object.hexdigest()

    # 排他制御でリストを操作
    with g_hash_records_lock:
        # 重複チェック
        if hash_value in g_hash_records:
            return False  # 重複あり
        
        # ハッシュをリストに追加（dequeにより自動的に古いものが削除される）
        g_hash_records.append(hash_value)
        return True

from threading import Lock
g_lock = Lock()
g_sentMailCount_DriverErr = 0
#----------------------------------------------------------------------------------------------------------
# Html情報取得、差分作成、通知送信のメイン関数
#----------------------------------------------------------------------------------------------------------
def getHTMLDiffandNotification(url, groupName, targetGroupDic, portForGroup):
    global g_sentMailCount_DriverErr
    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLDiffandNotification Start')
    groupLogger.log(groupName, 'notify_start', 'getHTMLDiffandNotification start', {'url': url})

    retCode = cf.SUB_RETURNCODE_ERR

    # ------------------------------------------------------------------
    # グループごとのログ格納用フォルダ作成
    # ------------------------------------------------------------------
    fo.Func_CreateDirectry(os.path.join(cf.PATH_LOG_DIR, groupName))

    try:
        driver = None
        webDriverTempDir = ''
        retOuterHtmlText = ''
        htmlData = ''
        htmlDataSize = 0
        victimsDict = {}
        file_victimsListPrev = ''
        file_victimsListPrevTmp = ''
        resultPNG_now  = ''
        resultPNGBefore = ''
        resultPNGAfter = ''
        resultPNGBeforeTmp = ''
        resultPNGAfterTmp = ''
        resultPNGDiffTmp = ''
        diffHTMLFilePath2Box = ''
        resultFileAfter = ''
        savedOuterHtmlFile = ''

        # 差分比較関数の戻り
        diffPlane = ''
        difffHTML = ''
        diffFileSize_Before = 0
        diffFileSize_After = 0
        diffHTMLFilePath = ''

        # 個別対応で取得した被害者
        # 今回追加されたものを格納するDic
        newItems = {}
        # 今回削除されたものを格納するDic
        deletedItems = {} 
        #スクリーンショットが正常に取得できたかどうか
        successScreenShot = False
        # 本来再検知は通知しないが、非常に重要な組織は再通知するのでそれ用
        updateInfo = {}
        updateInfoDel = {}
        allVictimsTmp = {}

        # AIによる被害組織情報取得において、文書っぽいものなら重要情報としてみる
        setUrgentFlgByAI = False
        setUrgentFlgByAI_VicList = []
        # inevstigateVictimsInfoAIArray = []
        investigateVictimsInfoAIDic = {}

        # 生成AIによって日本に関係のある組織と判断された被害組織
        japanRelatedOrganizations_VicList = []

        accessLogStruct = Log.readAccessLogStruct(groupName, Log.getAccessLogPath(groupName))

        isFinishSaveAccessLog = False

        # HTML情報が取得できないサイトが過去アクセスできていたか
        # 直近は接続できていたのに接続できなくなった場合はTrueになる
        isSiteChange2Unavailable = False
        isSiteChange2Available = False

        # サイトごとのログ
        accessLogData = cf.accessLog.copy()
        accessLogData = {}
        accessLogData['groupName'] = groupName
        accessLogData['getHTMLStatus'] = '初期化中'

        IsIndivisialScrapingTarget = False

        accessLogData['mainStartTime'] = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)

        # 個別ページの差分特別対応
        # 個別ページで差分をとる場合、メールの宛先、重要フラグ、差分取得するかのオンオフをここで取得しておく
        # debug_URL_Dic = cf.getTargetLeakSite(cf.TARGET_URL_JSON_PATH)

        detectDiffSwitch = targetGroupDic[groupName].get('detectDiffSwitch', True)
        forceNotification = targetGroupDic[groupName].get('forceNotification', False)
        forceUrgentMail = targetGroupDic[groupName].get('forceUrgentMail', False)
        notificateOnlyDeleteInfo = targetGroupDic[groupName].get('notificateOnlyDeleteInfo', True)
        excludeIgnoreText = targetGroupDic[groupName].get('excludeIgnoreText', False)
        useSeleniumBase_uc = targetGroupDic[groupName].get('useSeleniumBase_uc', False)
        # specialSurveillance = targetGroupDic[groupName].get('specialSurveillance', False)
        groupConfig = targetGroupDic[groupName]
        
        mailTo = targetGroupDic[groupName].get('mailTo', [])
        # これが指定されてたら強制的に宛先はこいつ
        # LockBitが2024/4/23接続不可になったときにYuichiにしか送りたくなくて追加
        mailToForce = targetGroupDic[groupName].get('mailToForce', [])
        headless = targetGroupDic[groupName].get('headless', True)

        if detectDiffSwitch == False:
            log_branch(groupName, 'diff_switch', 'disabled', {'forceNotification': forceNotification})
            return 0
        else:
            log_branch(groupName, 'diff_switch', 'enabled')

        # ------------------------------------------------------------------
        # ドライバ取得
        # ------------------------------------------------------------------
        # V2はBrave使いたいけどHeadlessで実行できなくてメモリやたら食うのでいったん保留
        # driver = sb.Func_SettingDriver_Brave(groupName)
        # headers = {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        #     'Accept-Enc        headers = {
        #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        #     'Accept-Encoding': 'gzip, deflate, br, zstd',
        #     'Accept-Language': 'en-US,en;q=0.5',
        #     'Connection': 'keep-alive',
        #     'Priority': 'u=0, i',
        #     'Sec-Fetch-Dest': 'document',
        #     'Sec-Fetch-Mode': 'navigate',
        #     'Sec-Fetch-Site': 'none',
        #     'Sec-Fetch-User': '?1',
        #     'Sec-GPC': '1',
        #     'Upgrade-Insecure-Requests': '1'
        # }
        headers = None
        driver, chromeService, webDriverTempDir = wrap_SettingDriver(groupName, portForGroup, useSeleniumBase_uc, headless, headers)

        if driver == None:
            with g_lock:
                # 必要以上に送るとGmailの送信制限に引っかかるので回数制限
                if g_sentMailCount_DriverErr < 20:
                    accessLogData['errText'] = 'ドライバの取得に失敗しました。'
                    Notification.sendMail_Nofication(f'スクレイピング対象：【{groupName}】<br>ドライバの取得に失敗しました。', '【重要】システムエラー', cf.SENDTO_REPORT_YUICHI)
                    g_sentMailCount_DriverErr += 1
                    raise Exception('ドライバの取得に失敗しました。')

        # ------------------------------------------------------------------
        # HTML取得
        # ------------------------------------------------------------------
        accessLogData['accessStartTime'] = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)
        retOuterHtmlText, htmlData, victimsDict, IsIndivisialScrapingTarget, retCode = wrap_getHTMLData(groupName, driver, url, excludeIgnoreText, groupConfig)
        accessLogData['accessEndTime'] = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)
        htmlDataSize = len(htmlData)
        accessLogData['htmlSize'] = len(htmlData)

        if htmlDataSize > 0:
            # 最終アクセス成功日時を記述しておく。ここに来るたびに更新していい
            # TODO:時々サーバーエラーとかの文字列がとれても成功になっちゃうのは要対応。現状はいちいちIgnoreに入れてる
            accessLogStruct['lastAccessSuccessTime'] = accessLogData['accessEndTime']

            # 何にせよアクセスできたとして次回アクセス不可時に通知するためにFalseにしておく
            # if isAccessStatusChanged(groupName, isChange2Deny = False):
            # ログのために変更前の状態取得
            prevStatus = accessLogStruct.get('SiteUnavailableNotification', False)
            if prevStatus:
                # アクセス不可から可になったら重要情報
                isSiteChange2Available = True
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'HTML取得成功扱い。アクセス不可→アクセス可', note=f'htmlDataSize:{str(htmlDataSize)},htmlData:{htmlData}')

            accessLogStruct['SiteUnavailableNotification'] = False
        else:
            isSiteChange2Unavailable = isAccessStatusChanged(groupName, isChange2Deny = True)
            
            # アクセス不可になったと判定された場合に通知を送信済みか
            sentNotification = accessLogStruct.get('SiteUnavailableNotification', False)
            # 通知済みなら送らない
            if sentNotification:
                isSiteChange2Unavailable = False
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'アクセス不可通知しない判定', note=f'htmlDataSize:{str(htmlDataSize)},htmlData:{htmlData}')
            else:
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'アクセス不可通知する判定', note=f'htmlDataSize:{str(htmlDataSize)},htmlData:{htmlData}')

            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'HTMLデータ取得(0KB)')

        # forceNotification CIG指定監視ページは読み取れなくてもメール飛ばしたい。削除の可能性
        if retCode & cf.SUB_RETURNCODE_GETHTML or forceNotification or isSiteChange2Unavailable:
            IsNeedToNotification = False
            onlyDeletedDiff = False

            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'差分検知処理開始')

            # Htmlデータをファイルに保存
            # htmlDataが0KBの場合は関数内で保存しないようにガードしている
            resultFileBefore, resultFileAfter = saveResultHtmlData(groupName, htmlData)
            resultFileBefore, resultFileAfter = saveResultHtmlData(groupName, htmlData)
            savedOuterHtmlFile = saveResultOuterHtmltext(groupName, retOuterHtmlText)

            # 過去に検知したことのあるHTMLテキスト。記憶しているハッシュから
            knownHtml = False
            # なんのための過検知防止か忘れたので一回コメント。
            # この機能のせいでスルーされてしまう差分がある。(KADOKAWA固有ページなど)_2024/7/5
            # if specialSurveillance == False:
            #     knownHtml = isKnownHtml(groupName, htmlData)

            # ------------------------------------------------------------------
            # HTML差分取得処理
            # ------------------------------------------------------------------
            if knownHtml == False:
                # アクセス不可の時は差分などいらない
                if isSiteChange2Unavailable == False or forceNotification:
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'generateDiffDataHTML:{resultFileBefore}:{resultFileAfter}', note = '')
                    diffPlane, difffHTML, diffFileSize_Before, diffFileSize_After, diffHTMLFilePath, diffPDFFilePathX = generateDiffDataHTML(resultFileBefore, resultFileAfter, groupName)
                
                if (diffPlane != '' and difffHTML != '') or isSiteChange2Unavailable:
                    IsNeedToNotification = True
                else:
                    IsNeedToNotification = False
                    forceNotification = False

                if IsNeedToNotification:
                    # ------------------------------------------------------------------
                    # スクリーンショット取得処理
                    # ------------------------------------------------------------------
                    successScreenShot, resultPNG_now, resultPNGBefore, resultPNGAfter = saveScreenShot(groupName, driver)
                 
            # 個別対応しててもHTMLに差分がなければやらない
            # → Medusaなど読み込みが中途半端で削除扱いされてしまうケースがあったため
            if IsIndivisialScrapingTarget == True and IsNeedToNotification == True:
                # ------------------------------------------------------------------
                # 個別対応で取得したデータ(Dictionary)の差分取得処理
                # ------------------------------------------------------------------
                # 差分は取れているので通知メールは送りたい。ただし処理がおかしかったら別途エラーメールおくる
                try:
                    retCode, newItems,deletedItems,file_victimsListPrev,file_victimsListPrevTmp,allVictimsTmp,updateInfo,updateInfoDel\
                    = generateDiffDataIndivisualInfo(groupName, victimsDict, targetGroupDic[groupName].get('relativeGroup',[]))

                    # ------------------------------------------------------------------
                    # 個別対応で取得した被害組織の詳細ページ情報の取得
                    # ------------------------------------------------------------------
                    # 個別対応していてvictimsDictも取得できているのにnewItems、deletedItemsがない場合は通知しない
                    # → 読み込みが中途半端で取得が中途半端な場合deletedItems扱いされそう
                    # メール送信後に取得したHtmlのAfterとかの置き換えするけど通知しないならそれらもやらないでよし
                    if len(victimsDict) > 0:
                        if len(newItems) == 0:
                            if len(deletedItems) == 0:
                                if forceNotification == False:
                                    IsNeedToNotification = False
                            else:
                                # Dark_Leak_Market_Newにように削除差分が非常に多いサイト対策
                                # このフラグがFalseの時は削除のみは通知しない
                                if notificateOnlyDeleteInfo:
                                    # 削除差分のみ
                                    onlyDeletedDiff = True

                                    for key in deletedItems:
                                        # 重要情報検索を翻訳からも検索したいのでここで翻訳入れておく
                                        deletedItems[key]['summary_JP'] = uf.Google_Translate(deletedItems[key]['summary'])
                                else:
                                    if forceNotification == False:
                                        IsNeedToNotification = False
                        else:
                            # 差分画像でcid:image3まで確定なので4から
                            detailScreenShotCnt = 4
                            for key in newItems.keys():
                                detailUrl = newItems[key].get('detailUrl', '')

                                if detailUrl != '':
                                    GetHTML.goTargetUrl(driver=driver, url=detailUrl, groupName=groupName)
                                    # screenShotTmpPath = GetHTML.getScreenShot(groupName+'_'+key, driver)
                                    # 新機構のページ内フルスクリーンショット取得関数
                                    keyTmp = re.sub(r'[\\|/|:|?|.|"|<|>|\|\t|\s|\*]', '_', key)

                                    try:
                                        screenShotTmpPath = GetHTML.save_fullscreenshot(groupName+'_'+keyTmp, driver)
                                        # screenShotTmpPath = ''
                                        if screenShotTmpPath !='':
                                            try:
                                                isSuccess, uploadUrl = ba.upload2BOX(groupName, screenShotTmpPath)
                                            except:
                                                uploadUrl = ''
                                            #詳細ページのスクリーンショットを挿入するタグを用意しておく。実際に挿入するのはメール送信時
                                            GetHTML.TrimImage_takasa_DetailPage(groupName,screenShotTmpPath)
                                            newItems[key]['detailScreenshot'] = screenShotTmpPath
                                            newItems[key]['detailScreenshotTag'] = '<img width="100%" src="cid:image{}" alt="Logo">'.format(str(detailScreenShotCnt))
                                            newItems[key]['detailScreenshotImgNo'] = detailScreenShotCnt
                                            newItems[key]['screenShotUrl'] = uploadUrl
                                            detailScreenShotCnt += 1
                                    except:
                                        Notification.sendMail_Nofication(f'スクレイピング対象：【{groupName}】<br>詳細ページのスクショ失敗', '【重要】システムエラー', cf.SENDTO_REPORT_YUICHI)

                                    # 詳細ページでより多く情報取れるグループは詳細ページの情報に更新する
                                    GetHTML.wrap_Func_scraping(driver, None, groupName, url, forDetail = True, value = newItems[key])
                                
                                # 重要情報検索を翻訳からも検索したいのでここで翻訳入れておく
                                newItems[key]['summary_JP'] = uf.Google_Translate(newItems[key]['summary'])

                            for key in deletedItems:
                                # 重要情報検索を翻訳からも検索したいのでここで翻訳入れておく
                                deletedItems[key]['summary_JP'] = uf.Google_Translate(deletedItems[key]['summary'])

                            # ------------------------------------------------------------------
                            # 被害組織の情報を生成AIに問い合わせ
                            # ------------------------------------------------------------------
                            for key in newItems.keys():
                                url = newItems[key].get('url', '')
                                start = time.time()
                                investigateVictimsInfoAIDict = investigateVictimsInfoAI(groupName, key, url)
                                end = time.time()
                                elapsed = end - start
                                print(f"[END] investigateVictimsInfoAI groupName={groupName}, key={key}, url={url}, elapsed={elapsed:.3f} sec")
                                
                                if len(investigateVictimsInfoAIDict) > 0:
                                    # inevstigateVictimsInfoAIArray.append({key:inevstigateVictimsInfoAIDict})
                                    investigateVictimsInfoAIDic[key] = {}
                                    newItems[key]['aiInvestigatement'] = {}
                                    newItems[key]['aiInvestigatement'] = investigateVictimsInfoAIDic[key] = investigateVictimsInfoAIDict

                except Exception as e:
                    Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')
                    body = '【Location】:{}<br>【Exception】:{}'.format(Log.Trace.execution_location(), str(e))
                    Notification.sendMail_Nofication(f'スクレイピング対象：【{groupName}】<br>{body}', '【重要】システムエラー', cf.SENDTO_REPORT_YUICHI)

            if IsNeedToNotification == True:
                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'差分検知処理開始 diffDataあり')

                if isSiteChange2Unavailable == False:
                    retCode |= cf.SUB_RETURNCODE_DIFF
    
                diffUIFile = diffHTMLFilePath

                # ------------------------------------------------------------------
                # 添付用差分画像の準備
                # ------------------------------------------------------------------
                tmpRet = generateScreenShotDiff(groupName, resultPNGBefore, resultPNGAfter)
                resultPNGBeforeTmp = tmpRet[0]
                resultPNGAfterTmp = tmpRet[1]
                resultPNGDiffTmp = tmpRet[2]
                if fo.Func_IsFileExist(resultPNGBeforeTmp):
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'resultPNGBeforeTmp Exists')
                else:
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'resultPNGBeforeTmp Not Exists')

                if fo.Func_IsFileExist(resultPNGAfterTmp):
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'resulresultPNGAfterTmp Existsts')
                else:
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'resultPNGAfterTmp Not Exists')

                if fo.Func_IsFileExist(resultPNGDiffTmp):
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'resultPNGDiffTmp Exists')
                else:
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'resultPNGDiffTmp Not Exists')
                
                # ------------------------------------------------------------------
                # 作成したHTMLファイルをBOXへのアップ用にユニークなファイル名にしてコピー
                # アップしたら消す
                # ------------------------------------------------------------------
                diffHTMLFilePath2Box = os.path.join(cf.PATH_DIFFHTML_DIR, groupName + '{}_diff.html'.format(uf.getDateTime('%Y%m%d%H%M')))
                fo.Func_CopyFile(diffUIFile, diffHTMLFilePath2Box)

                # ------------------------------------------------------------------
                # 差分から重要単語を検索
                # 個別対応で取得した情報がある時は個別対応側で重要情報を探す。
                # ------------------------------------------------------------------
                mailCfgTmp = cf.cfgDic['mailConfig'].copy()
                time_before = fo.Func_GetFileUpdateTime(resultFileBefore)
                time_after = fo.Func_GetFileUpdateTime(resultFileAfter)
                if time_before == '' or time_after == '':
                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'generateDiffDataHTML:{resultFileBefore}:{resultFileAfter}', note = '')
                    
                # ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                if retCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL:
                    # アイテム数が多いとGmailの一回のメール送信キャパ超えてエラーになるので分割
                    splitNewItemArray = uf.split_dict_fixed_size(newItems, 10)
                else:
                    # 個別対応してないときは空を一つだけ入れてダミーフラグ扱いする
                    splitNewItemArray = [None]

                # 個別対応はメールに総件数とメール記載件数をだすのでカウントする
                newItemsTotalCount = len(newItems)
                totalMailCount = len(splitNewItemArray)

                for currentMailCount, sNewItems in enumerate(splitNewItemArray, 1):
                    for key in mailCfgTmp.keys():
                        setImportantFlagForce = mailCfgTmp[key]['setImportantFlagForce']
                        # CIGの特別監視対象個別ページの場合は強制重要扱い（forceUrgentMailはTargetURLに記述）
                        if setImportantFlagForce == False:
                            setImportantFlagForce = forceUrgentMail

                        mailCfgTmp[key]['hasImportantInfo'] = False
                        mailCfgTmp[key]['importantWordsInfo'] = []
                        mailCfgTmp[key]['importantWordsList'] = []
                        if retCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL:
                            # isImportant = Notification.IsImportantInfo(groupName, importantWordListPath, newItemDict = newItems, delItemDict = deletedItems, force = setImportantFlagForce, autoCheckJapanese = autoCheckJapanese)
                            
                            # 2024/11の新バージョン向け。戻すときはElse側で入れてるmailCfgTmpもElseから出してこの下をコメント
                            retHasImportantInfo, importantWords = Notification.IsImportantInfo2(groupName,
                                                                                                mailCfgTmp[key]['importantWordList'],
                                                                                                targetDictArray = sNewItems,
                                                                                                extraImportantInfo = '',
                                                                                                force = setImportantFlagForce,
                                                                                                autoCheckJapanese = mailCfgTmp[key]['autoCheckJapanese'])
                            mailCfgTmp[key]['hasImportantInfo'] = retHasImportantInfo
                            mailCfgTmp[key]['importantWordsInfo'] = importantWords

                            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード[{key}]-retHasImportantInfo:{retHasImportantInfo}')
                            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード[{key}]-importantWords:{importantWords}')
                        else:
                            isImportant = Notification.IsImportantInfo(groupName,
                                                                       mailCfgTmp[key]['importantWordList'],
                                                                       str = diffPlane,
                                                                       force = setImportantFlagForce)

                            mailCfgTmp[key]['hasImportantInfo'] = isImportant[0]
                            mailCfgTmp[key]['importantWords'] = isImportant[1]
                            mailCfgTmp[key]['importantWordsList'] = isImportant[2]
                            mailCfgTmp[key]['importantWord_OnlyDeleted'] = isImportant[3]
                            mailCfgTmp[key]['importantWordsReplaceList'] = isImportant[4]
                            mailCfgTmp[key]['importantWords_jp'] = isImportant[5]
                            mailCfgTmp[key]['importantWordsList_jp'] = isImportant[6]
                            mailCfgTmp[key]['importantWordsReplaceList_jp'] = isImportant[7]

                    # 既存ではmailCfgTmp分、IsImportantInfo関数の中で日本語検知のChatGPTに問い合わせロジックが走ってたけど無駄なので分けて外だし
                    if sNewItems and len(sNewItems) > 0:
                        importantWordsList_jp = Notification.hasJapaneseWord(groupName, targetDictArray = sNewItems)
                        mailCfgTmp[key]['importantWordsList_jp'] = importantWordsList_jp

                    # ------------------------------------------------------------------
                    # メールに掲載するアクセス履歴のステータス更新しておく
                    # メール作成時このアクセスログファイルを参照するため一度書き込んでおかなければならない・・・
                    # ------------------------------------------------------------------
                    accessLogData['getHTMLStatus'] = Log.getHtmlStatus(retCode)
                    accessLogStruct['log'] = Log.mergeAccessLogDataList(accessLogData, Log.getAccessLogPath(groupName))
                    Log.saveAccessLog2File(groupName, accessLogStruct, Log.getAccessLogPath(groupName))
                    isFinishSaveAccessLog = True
                
                    # ------------------------------------------------------------------
                    # メール作成、送信
                    # ------------------------------------------------------------------
                    uploadUrl = ''
                    diffHTMLFilePath2BoxUrl = ''

                    # 概要を分析した結果を格納しておく、生成AIにやらせるから一回しかやりたくない
                    analyzesummary = ''
                    for key in mailCfgTmp.keys():
                        # 新型もってたらこちら優先
                        importantWordsList = mailCfgTmp[key].get('importantWordsInfo',[])
                        # if len(importantWordsList) <= 0:
                        #     importantWordsList = mailCfgTmp[key].get('importantWordsList', [])

                        # 通知を送るかどうか。'regular'以外はhasImportantInfoがないと送らない
                        # 重要単語以外でも重要フラグを立てる条件はあるけど、それらはCIG用なのでスキップしてOK
                        # if key != 'cig' and key != 'regular' and mailCfgTmp[key]['hasImportantInfo'] == False:
                        if key != 'cig' and key != 'regular' and len(importantWordsList) <= 0:
                            continue
                        else:
                            try:
                                if key != 'cig' and key != 'regular':
                                    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード({key}):{importantWordsList}')
                            except Exception as e:
                                Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'重要ワードログException:{str(e.args)}')

                        try:
                            if importantWordsList:
                                debugJsonTmp = []
                                debugJsonLogPath = os.path.join(cf.PATH_LOG_DIR, groupName + '_VictimsListAll.json')
                                debugJsonTmp = fo.Func_ReadJson2Dict(debugJsonLogPath)
                                if not debugJsonTmp:
                                    debugJsonTmp = []

                                debugJsonTmp.append(mailCfgTmp)
                                fo.Func_WriteDict2Json(debugJsonLogPath, debugJsonTmp)
                        except Exception as e:
                            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'DebugLogError:{str(e.args)}')

                        importantWordsReplaceList = mailCfgTmp[key].get('importantWordsReplaceList', [])
                        importantWordsList_jp = mailCfgTmp[key].get('importantWordsList_jp', [])
                        importantWordsReplaceList_jp = mailCfgTmp[key].get('importantWordsReplaceList_jp', [])
                        sendTo = mailCfgTmp[key]['sendTo']
                        importantWord_OnlyDeleted = mailCfgTmp[key].get('importantWord_OnlyDeleted', False) # 重要ワードが削除差分のみの場合立ってくる
                        setMailUrgentFlg = False
                        urgentMailInfo =\
                        {
                            # 重要ワードあり→いったんそのままにするけど新しいimportantWordsInfoとか旧importantWordsListで判断できるから無駄
                            'urgent_hasImportantWords':mailCfgTmp[key]['hasImportantInfo'],
                            # 重要フラグは立てないけど、削除のみであることを記載したい
                            'notUrgent_OnlyDeleted':importantWord_OnlyDeleted,
                            'hasJapanRelatedOrganizations':bool(japanRelatedOrganizations_VicList),
                            # "ExtraInfo:AI"始まりのAIによる概要の場合はただの企業名ではない可能性（グループによるなんらかのアナウンスなど）があるので重要
                            'urgent_ByAI':setUrgentFlgByAI,
                            # 個別ページ対応。このフラグがTargetURL.jsonでセットされてたら強制重要メール
                            'urgent_UserSpecified':forceUrgentMail,
                            'urgent_infoUpdate':len(updateInfo) > 0 or len(updateInfoDel) > 0,
                            'changedHTMLStructure': True if retCode & cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED else False,
                            'isSiteChange2Unavailable':isSiteChange2Unavailable,
                            'isSiteChange2Available':isSiteChange2Available
                        }

                        try:
                            if len(sendTo) <= 0:
                                continue
                            elif all(item == '' for item in sendTo):
                                continue
                        except Exception as e:
                            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')
                            continue

                        # 【サイト構成変更の可能性】は重要扱いにする 2023/12/4
                        if retCode & cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED:
                            # これはCIG以外送らなくてよし
                            if key != 'cig':
                                continue
                            setMailUrgentFlg = True
                            
                        # 更新時の情報は現状CIGにしか通知しないので強制False
                        # 送るとMBSDが特別に更新を監視していることがばれてしまう
                        if key != 'cig':
                            urgentMailInfo['urgent_infoUpdate'] = False
                            # CIG以外は個別の強制重要メール指定フラグは無視する
                            urgentMailInfo['urgent_UserSpecified'] = False
                        else:
                            if diffFileSize_After == 0:
                                # 取得したのが0KBなら個別の強制重要メール指定フラグは無視する
                                urgentMailInfo['urgent_UserSpecified'] = False
                            
                        if urgentMailInfo['urgent_hasImportantWords'] and urgentMailInfo['notUrgent_OnlyDeleted'] == False\
                            or urgentMailInfo['urgent_UserSpecified']\
                            or urgentMailInfo['hasJapanRelatedOrganizations']\
                            or urgentMailInfo['urgent_ByAI']\
                            or urgentMailInfo['isSiteChange2Unavailable']\
                            or urgentMailInfo['isSiteChange2Available']\
                            or urgentMailInfo['changedHTMLStructure']\
                            or urgentMailInfo['urgent_infoUpdate']:
                            setMailUrgentFlg = True

                        if len(mailToForce):
                            # 強制的に宛先が指定されている場合は一回しか送りたくないのでcig以外はスキップする
                            if key != 'cig':
                                break
                            # この宛先指定が最強
                            sendTo = mailToForce
                        else:
                            if urgentMailInfo['urgent_infoUpdate']:
                                # メールの宛先が指定されてたら変更。万が一メールがセットされてなかったら嫌なのでCIGには強制的に飛ぶようにしておく
                                if len(mailTo) > 0:
                                    sendTo = mailTo
                                else:
                                    sendTo = ["y.yasuda@mbsd.jp","takashi.yoshikawa.el@d.mbsd.jp", "m.fukuda@mbsd.jp"]


                        # はっしゅで重複チェック入れる。宛先と本文用データでハッシュ
                        if sNewItems or deletedItems:
                            merged_dict = {**sNewItems, **deletedItems}
                            if not generate_and_check_dict_hash_thread_safe(merged_dict, sendTo):
                                continue

                        # 削除差分しかないかを確認
                        if IsIndivisialScrapingTarget == False:
                            onlyDeletedDiff = IsOnlyDeleted(diffPlane)

                        extraSubjectStr = ''
                        if 'extraSubjectStr' in mailCfgTmp[key]:
                            extraSubjectStr = mailCfgTmp[key]['extraSubjectStr']

                        # ------------------------------------------------------------------
                        # 通知メールの本文作成
                        # ------------------------------------------------------------------
                        # アップ自体は一回だけでよい
                        if key == 'cig' or uploadUrl == 'アップロード失敗':
                            if fo.Func_IsFileExist(resultPNG_now):
                                isSuccess, uploadUrl = ba.upload2BOX(groupName,resultPNG_now)

                                # もし失敗したら消されたくないのでコピーしとく
                                # めったにないと信じてコピーの削除は手動
                                if isSuccess == False:
                                    tmp = resultPNG_now[:-len('.png')]
                                    resultPNG_now_Backup = tmp + f'_BoxUploadFailed.png'
                                    fo.Func_CopyFile(resultPNG_now, resultPNG_now_Backup)
                            else:
                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'[{resultPNG_now}]が存在しません')
                        if key == 'cig' or diffHTMLFilePath2BoxUrl == 'アップロード失敗':
                            # diffHTML, 軽量化のためにBoxにあっぷ
                            isSuccess, diffHTMLFilePath2BoxUrl = ba.upload2BOX(groupName, diffHTMLFilePath2Box)

                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'mailBody作成直前')

                        # isSiteChange2Unavailable がTrueの時はDiffとらずにくるはず。一応ガードいれるけど
                        # diffFileSize_Beforeは０KBで来るはずなのでここでBeforeのファイル取得しておく
                        # diffFileSize_BeforeはHTML取得成功時にしか上書きされないはずなので０KBはありえない
                        if diffFileSize_Before == 0 and isSiteChange2Unavailable:
                            diffFileSize_Before = fo.Func_GetFileSize(resultFileBefore)

                        mailBody = ''
                        dicForMailBody = {}
                        retUrgentFlg = False
                        if (sNewItems or deletedItems) and len(sNewItems) > 0 or len(deletedItems) > 0:
                            try:
                                dicForMailBody, retUrgentFlg = Notification.ConvertVictimsData2MailBodyData(
                                    groupName,
                                    sNewItems,
                                    deletedItems,
                                    importantWordsList,
                                    urgentMailInfo,
                                    importantWordsList_jp,
                                    uploadUrl
                                    )
                                
                                if not setMailUrgentFlg:
                                    setMailUrgentFlg = retUrgentFlg
                                if analyzesummary == '':
                                    analyzesummary = ga.analyzesummaryByAI_ChatGPT(dicForMailBody)
                                    
                                dicForMailBody['analyzeSummaryByAI'] = analyzesummary
                                dicForMailBody['added_orgs_TotalCount'] = newItemsTotalCount
                                dicForMailBody['totalMailCount'] = totalMailCount
                                dicForMailBody['currentMailCount'] = currentMailCount

                                days, hours, minutes =  uf.diffDetectedTime(time_before, time_after)
                                dicForMailBody['detectedTimePrev'] = time_before
                                dicForMailBody['detectedTimeNow'] = time_after
                                dicForMailBody['diffDetectedTime'] = f"{days}日 {hours:02d}時間 {minutes:02d}分"

                                mailBody = Notification.CreateNotificationMailBody(dicForMailBody)
                                log_branch(groupName, 'mail_body_path', 'AI_generated', {'newItems': len(sNewItems), 'deleted': len(deletedItems)})
                            except Exception as e:
                                Notification.sendMail(f'{groupName}:ConvertVictimsData2MailBodyData', "V2差分検知：[監視システムエラー]", cf.SENDTO_REPORT_YUICHI)
                        else:
                            sNewItems = {}
                            # deletedItems = {}
                            mailBody = Notification.createNotificationBody_HTMLVer(
                                    groupName,
                                    sNewItems,
                                    deletedItems,
                                    updateInfo,
                                    updateInfoDel,
                                    importantWordsList,
                                    importantWordsReplaceList,
                                    diffPlane,
                                    diffHTMLFilePath2BoxUrl,
                                    time_before,
                                    time_after,
                                    str(diffFileSize_Before),
                                    str(diffFileSize_After),
                                    uploadUrl,
                                    successScreenShot,
                                    urgentMailInfo,
                                    japanRelatedOrganizations_VicList,
                                    setUrgentFlgByAI_VicList,
                                    importantWordsList_jp,
                                    importantWordsReplaceList_jp,
                                     )
                            log_branch(groupName, 'mail_body_path', 'fallback_template', {'newItems': len(sNewItems), 'deleted': len(deletedItems)})

                        if uf.strstr('【ERROR】', mailBody):
                            groupLogger.log(groupName, 'email_error_body', 'mailBody contains ERROR marker, sending error report', {'subject': "V2差分検知：[監視システムエラー]", 'recipients': cf.SENDTO_REPORT_YUICHI})
                            Notification.sendMail(mailBody, "V2差分検知：[監視システムエラー]", cf.SENDTO_REPORT_YUICHI)
                        else:
                            if mailBody:
                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'メール送信直前')
                                groupLogger.log(groupName, 'mail_body_ready', '通知メール本文が成立した', {
                                    'newItems': len(sNewItems),
                                    'deletedItems': len(deletedItems),
                                    'urgent': setMailUrgentFlg,
                                    'retCode': retCode
                                })

                                subject = Notification.createSubject_HTMLVer(
                                    groupName,
                                    urgentMailInfo['urgent_hasImportantWords'],
                                    retCode,
                                    importantWord_OnlyDeleted,
                                    onlyDeletedDiff,
                                    extraSubjectStr,
                                    htmlDataSize)
                                
                                def isRegistImportantInfo(data):
                                    if isinstance(data, dict):
                                        return any(isRegistImportantInfo(v) for v in data.values())  # all → any
                                    elif isinstance(data, list):
                                        return len(data) > 0 and any(isRegistImportantInfo(item) for item in data)  # 条件を反転
                                    elif isinstance(data, str):
                                        return len(data.strip()) > 0  # 条件を反転
                                    elif isinstance(data, (int, float)):
                                        return data != 0  # 条件を反転
                                    return False  # デフォルト値をFalseに変更
                                
                                if dicForMailBody:
                                    setMailUrgentFlg = isRegistImportantInfo(dicForMailBody.get('important_info',{}))

                                # 個別ページが取得できないケースは、テキストや画像を載せるとGmailがスパム扱いされる件を避けるために検知メール送信しない
                                # ただし、特別監視（被害組織ごとのリークページ監視）は、Html差分でしか検知できないのでメール送信してあげる
                                sendNotificationMail = True
                                SiteCategory = targetGroupDic[groupName].get('SiteCategory', '')
                                if not (retCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL):
                                    sendNotificationMail = '特別監視' in SiteCategory

                                if sendNotificationMail:
                                    attatchImage = targetGroupDic[groupName].get('attatchImage', False)

                                    # DEBUG = True
                                    # if DEBUG:
                                    #     isSendSuccess = Notification.sendMail(mailBody, subject, cf.SENDTO_REPORT_YUICHI, resultPNGBeforeTmp, resultPNGAfterTmp, resultPNGDiffTmp, setMailUrgentFlg, newItems, attatchImage = attatchImage)
                                    # else:
                                    groupLogger.log(groupName, 'email_send_attempt', 'about to call Notification.sendMail', {
                                        'subject': subject,
                                        'recipients': sendTo,
                                        'attachImage': attatchImage,
                                        'newItems': len(newItems),
                                        'retCode': retCode
                                    })
                                    isSendSuccess = Notification.sendMail(mailBody, subject, sendTo, resultPNGBeforeTmp, resultPNGAfterTmp, resultPNGDiffTmp, setMailUrgentFlg, newItems, attatchImage = attatchImage)

                                    if isSendSuccess:
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'メール送信完了')
                                        groupLogger.log(groupName, 'email_send_success', 'Notification.sendMail succeeded', {'recipients': sendTo, 'retCode': retCode})
                                    else:
                                        detectedCompany = ''
                                        if len(sNewItems):
                                            detectedCompany = '<br><br>■被害組織<br>' + '<br><br>'.join(sNewItems.keys())

                                        Notification.sendMail_Nofication(f'メール送信失敗の可能性<br>■グループ名<br>{groupName}{detectedCompany}', '【重要】システムエラー', cf.SENDTO_REPORT_YUICHI)
                                        groupLogger.log(groupName, 'email_send_failed', 'Notification.sendMail reported failure', {
                                            'retCode': retCode,
                                            'recipients': sendTo,
                                            'detectedItems': detectedCompany
                                        })
                                else:
                                    groupLogger.log(groupName, 'email_skipped', 'sendNotificationMail flag false', {
                                        'sendNotificationMail': sendNotificationMail,
                                        'SiteCategory': targetGroupDic[groupName].get('SiteCategory', ''),
                                        'retCode': retCode
                                    })
                            else:
                                groupLogger.log(groupName, 'mail_body_empty', 'mailBody is empty, skipping Notification.sendMail', {
                                    'retCode': retCode,
                                    'sendNotificationMail': sendNotificationMail
                                })
                try:
                    # 0KBならBeforeに上書きはしない
                    # TODO:コード整理するとき以下の条件は見直せるかも。というか必要ないかも？
                    # とりあえずforceUrgentMailの時は情報削除されて読み込み不可がありうるため、0KBでも保存しておく
                    if fo.Func_GetFileSize(resultFileAfter) > 0 or forceUrgentMail:
                        fo.Func_RenameFileEx(resultFileAfter, resultFileBefore)

                    if fo.Func_GetFileSize(file_victimsListPrevTmp) > 0:
                        fo.Func_RenameFileEx(file_victimsListPrevTmp, file_victimsListPrev)

                    # もともとgenerateDiffDataIndivisualInfoのなかでやってたけど、ほかのファイルは処理終了時に書き込んでるのにこいつは処理終了前に書き込むから不整合おきる
                    # そのため同じように処理終了時に更新するように変更
                    if len(allVictimsTmp) > 0:
                        file_victimsListAll = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsListAll.json')
                        fo.Func_WriteDict2Json(file_victimsListAll, allVictimsTmp)
                    
                    # BOXにユニークな名前でアップしたいので日付つきのファイル名にしていたPNGをリネーム
                    # ローカルには直近のものしか残さないので日付けけす
                    # →何世代か残すことにしたので何もしない
                    # 削除はdeleteScreenShotFilesで指定された世代以前をまとめて削除
                    # currentPng = os.path.join(cf.PATH_SCREENSHOT_DIR, groupName + '.png')
                    # fo.Func_RenameFileEx(resultPNG_now, currentPng)

                    # リサイズ済のPNGを次回のためにBeforeにリネーム
                    # HTMLDataと同じく、今回取得サイズが0なら上書きせずに成功時のを残しておきたい
                    if htmlDataSize > 0:
                        fo.Func_RenameFileEx(resultPNGAfter, resultPNGBefore)
                except:
                    Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e.args)}')

            else:
                if retCode != cf.SUB_RETURNCODE_ERR:
                    retCode |= cf.SUB_RETURNCODE_NODIFF

            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'差分検知処理終了')
        else:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'差分検知処理スキップ(Html取得失敗)')

    except Exception as e:
        error_text = str(e.args)
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{error_text}')
        groupLogger.log(groupName, 'notify_error', 'exception in getHTMLDiffandNotification', {
            'error': error_text,
            'traceback': traceback.format_exc()
        })

    finally:
        if driver != None:
            driver.quit()
            driver = None

        if chromeService:
            # ChromeDriverプロセスが終了したか確認する
                def is_process_running(pid):
                    try:
                        process = psutil.Process(pid)
                        return process.is_running()
                    except psutil.NoSuchProcess:
                        return False

                # Service オブジェクトからプロセスIDを取得
                from selenium.webdriver.chrome.service import Service
                chrome_pid = chromeService.process.pid
                cnt_parent = 1
                while is_process_running(chrome_pid):
                    print(f'メインプロセス：[{str(chrome_pid)}]が終了していない。リトライ回数：{str(cnt_parent)}回')
                    cnt_parent += 1
                    # プロセスが終了するまで待つ
                    time.sleep(1)


                # 子プロセスも含めて全て終了したことを確認
                try:
                    parent = psutil.Process(chrome_pid)
                    children = parent.children(recursive=True)
                    cnt_child = 1
                    for child in children:
                        while child.is_running():
                            print(f'メインプロセス：[{str(chrome_pid)}]の子プロセスが終了していない。リトライ回数：{str(cnt_child)}回')
                            cnt_child += 1
                            time.sleep(1)
                except psutil.NoSuchProcess:
                    # 親プロセスが終了していればOK
                    pass

        #-----------------------------------------------------
        # ここに来るまでにリネーム処理などは済んでいるはず。
        # エラーなどで余計なファイルが残らないように念のため削除処理
        #-----------------------------------------------------
        fo.Func_DeleteFile(resultFileAfter)
        # fo.Func_DeleteFile(resultPNG_now)
        # 指定された世代より前のスクショは削除しておく
        deleteScreenShotFiles(groupName, cf.GEN_STOCKSCREENSHOT)
        fo.Func_DeleteFile(resultPNGAfter)
        fo.Func_DeleteFile(diffHTMLFilePath2Box)
        fo.Func_DeleteFile(resultPNGBeforeTmp)
        fo.Func_DeleteFile(resultPNGAfterTmp)
        fo.Func_DeleteFile(resultPNGDiffTmp)
        fo.Func_DeleteFile(file_victimsListPrevTmp)

        if len(newItems) > 0:
            for key in newItems.keys():
                tmp = newItems[key].get('detailScreenshot','')
                if tmp != '':
                    fo.Func_DeleteFile(tmp)
                            
        # HTMLから取得したデータもBOXへアップロードする。
        # Jsonファイルは差分が或る時だけ
        file_victimsListPrev = ''
        resultFileBefore = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_before.txt')
        if retCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL:
            file_victimsListPrev = os.path.join(cf.PATH_HTMLDIFF_DATA, groupName + '_VictimsList.json')
        uploadHtmlDataFile2Box(groupName, resultFileBefore, file_victimsListPrev, savedOuterHtmlFile)

        if isFinishSaveAccessLog == False:
            accessLogData['getHTMLStatus'] = Log.getHtmlStatus(retCode)
            accessLogStruct['log'] = Log.mergeAccessLogDataList(accessLogData, Log.getAccessLogPath(groupName))
        
        accessLogData['mainEndTime'] = uf.getDateTime(cf.ACCESSDATETIME_FORMAT)

        # アクセス不可になった旨を通知したら記録しておく
        if isSiteChange2Unavailable:
            accessLogStruct['SiteUnavailableNotification'] = True
            accessLogStruct['SiteUnavailableNotificationDate'] = accessLogData['mainEndTime']

        Log.saveAccessLog2File(groupName, accessLogStruct, Log.getAccessLogPath(groupName))

        groupFolderUrl, fileUrl, shareFolderLink = uploadLogFile2Box(groupName)
        accessLogStruct['boxStatus'] = {}
        accessLogStruct['boxStatus']['box_groupFolderUrl'] = groupFolderUrl
        accessLogStruct['boxStatus']['box_fileUrl'] = fileUrl
        accessLogStruct['boxStatus']['box_shareFolderLink'] = shareFolderLink

        # Boxへアップロード終わったらboxStatusを書き込んでもっかい保存
        Log.saveAccessLog2File(groupName, accessLogStruct, Log.getAccessLogPath(groupName))

        # いつかのために
        # 'log'を日付ごとのファイルに保存と、'log'キー以外を分けて保存しておく
        tmpStruct = uf.create_dict_with_selected_elements(accessLogStruct, ['log'])
        Log.saveAccessLog2File(groupName, tmpStruct, Log.getAccessLogPath(groupName, uf.getDateTime('%Y%m%d')))
        tmpStruct = uf.create_dict_with_removed_elements(accessLogStruct, ['log'])
        Log.saveAccessLog2File(groupName, tmpStruct, Log.getAccessLogConfigPath(groupName))

        # WebDriverに設定した一時フォルダ削除
        # import shutil
        # shutil.rmtree(webDriverTempDir)

        # fo.clean_temp_folder(webDriverTempDir)

    groupLogger.log(groupName, 'notify_end', 'getHTMLDiffandNotification finished', {'retCode': retCode})
    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'getHTMLDiffandNotification End')

    return retCode, webDriverTempDir
