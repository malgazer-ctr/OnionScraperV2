# from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError
import threading
import time
import shutil
import os
import subprocess
import sys
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import traceback

from Config import Config as cf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import BoxAPI as ba
from OnionScraperLib import GetHTML as gh
from OnionScraperLib import SetupBrowser as sb
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import Log
from OnionScraperLib import GroupLogger as groupLogger
import MonitorSub as ms

g_TargetGroupDic = {}

# --------------------------------------------------------------------------------------------------
# 初期化関数
# --------------------------------------------------------------------------------------------------
def init():
    # fo.Func_removeAllFiles(cf.PATH_HTMLDIFF_DATA)
    # fo.Func_removeAllFiles(cf.PATH_HTMLDIFF_RESULTS)
    fo.Func_removeAllFiles(cf.TARGET_URL_LISTSUB_DIR)

    uf.killProccess('tor.exe', True)

    ClearSettingDirectory()

    fo.Func_CreateDirectry(cf.PATH_LOG_DIR)
    # uf.startProcess(cf.PATH_TOREXE)
    dateTime = uf.getDateTime('%Y%m%d_%H%M%S')
    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'Crawl_All_{}.log'.format(dateTime))
    fo.Func_RenameFileEx(cf.PATH_ALLLOG_FILE, tmpPath)

    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'Benchmark_{}.log'.format(dateTime))
    fo.Func_RenameFileEx(cf.PATH_BENCHMARK_FILE, tmpPath)
    
    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'AccessLogLock')
    fo.Func_DeleteFile(tmpPath)
    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'AccessLog_{}.log'.format(dateTime))
    fo.Func_RenameFileEx(cf.PATH_ACCESSLOG_FILE, tmpPath)

    fo.Func_CreateDirectry(cf.PATH_HTMLDIFF_DATA)
    fo.Func_CreateDirectry(cf.PATH_DIFFHTML_DIR)
    fo.Func_CreateDirectry(cf.PATH_DIFFPDF_DIR)
    fo.Func_CreateDirectry(cf.PATH_SCREENSHOT_DIR)
    fo.Func_CreateDirectry(cf.PATH_NOTIFIED_IMPORANT_INFO)
    fo.Func_CreateDirectry(cf.PATH_SCREENSHOT_DIFF_DIR)
    fo.Func_CreateDirectry(cf.PATH_OUTERHTML_TEXT)
    fo.Func_CreateDirectry(cf.PATH_LOG2_ROOT)

    cf.g_logMainFolderId, cf.g_shareFolderLink = ba.BOX_SetAccessLogStockFolder('MainProc')

    cf.g_BoxFolderIds['SharedParent'] = cf.g_logMainFolderId
    
# --------------------------------------------------------------------------------------------------
# Chrome,FireFox使用時のTOR設定ファイル関連
# --------------------------------------------------------------------------------------------------
def ClearTorDataDirectory():
    dir_path = cf.PATH_TOR_DATA

    if os.path.exists(dir_path) == True:
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)

def ClearSettingDirectory():
    dir_path = cf.PATH_TORRC_DIR
    if os.path.exists(dir_path) == True:
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)

def CreateTorDataDirectory(num):
    new_path = os.path.join(cf.PATH_TORRC_DIR, 'tor'+str(num))
    
    if not os.path.exists(new_path):#ディレクトリがなかったら
        os.makedirs(new_path)
    else:
        shutil.rmtree(new_path)
    
    return new_path

def CreateTorrc(num,sockport,DataDirectoryPath):

    torrc_file = os.path.join(cf.PATH_TORRC_DIR, 'torrc' + str(num))
    controlport = sockport + 1
    text_file = open(torrc_file, "wt")

    text_file.write("SocksPort localhost:" + str(sockport) + "\n")
    #text_file.write("ControlPort localhost:" + str(controlport) + "\n")
    text_file.write("StrictNodes 1\n")
    text_file.write("ExcludeNodes SlowServer\n")
    text_file.write("DataDirectory " + str(DataDirectoryPath) + "\n")

    text_file.close()

    return torrc_file

def ExecuteTorProcess(groupName, torConfigfile):

    return execute_tor_process(groupName, torConfigfile)
    try:
        commandline = "\"{}\" -f ".format(cf.PATH_TOREXE) + str(torConfigfile)
        proc = subprocess.Popen(commandline, shell=True)
        time.sleep(15)
        return proc.pid
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e)}', note = '')

def execute_tor_process(groupName, torConfigfile):
    try:
        commandline = [cf.PATH_TOREXE, '-f', str(torConfigfile)]
        proc = subprocess.Popen(commandline)
        time.sleep(15)
        return proc.pid
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory='E', logtext=f'{str(e)}', note='')


def ProcessTerminateTree(groupName, pid):
    try:
        parent_pid = pid
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True): 
            child.kill()
        parent.kill()
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'{str(e)}', note = '')

# --------------------------------------------------------------------------------------------------
# 初期設定関連
# --------------------------------------------------------------------------------------------------
def getTargetList_Dict(path = ''):
    try:
        ret = {}
        targetPath = path
        if targetPath == '':
            targetPath = cf.TARGET_URL_JSON_PATH

        ret = fo.Func_ReadJson2Dict(targetPath)

    except Exception as e:
        Log.LoggingWithFormat('MainProc', logCategory = 'E', logtext = f'{str(e)}', note = '')

    return ret

# --------------------------------------------------------------------------------------------------
# アクセスログ送信用スレッド関数
# --------------------------------------------------------------------------------------------------
g_Thread_SendAccessLog = None
from datetime import datetime
def thread_SendAccessLog():
    try:
        while True:
            ms.sendAccessLog(g_TargetGroupDic)
            time.sleep(10)

    except Exception as e:
        print(f"スレッドで例外が発生しました: {e}")

def threadWait_SendAccessLog():
    while g_Thread_SendAccessLog == None:
        if g_Thread_SendAccessLog != None:
            break
    while g_Thread_SendAccessLog.is_alive():
        time.sleep(0.1)
# --------------------------------------------------------------------------------------------------
# 自身の終了ハンドリング用
# --------------------------------------------------------------------------------------------------
import signal
import sys
import atexit

def messageBox(title, text_):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    root.lift()
    messagebox.showwarning(title, text_)
    root.destroy()


def handle_exit():
    threadWait_SendAccessLog()

    messageBox('main_threadVer', 'handle_exit')

def handle_sigterm(signum, frame):
    threadWait_SendAccessLog()

    messageBox('main_threadVer', 'handle_sigterm')

    sys.exit(0)

    # def handle_keyboard_interrupt():
    #     threadWait_SendAccessLog()

    sys.exit(0)

# 子プロセスのタイムアウトは共通で10分にしておく
CHILDPROC_TIMEOUT = 3600
# 子プロセスのタイムアウトは共通で5分にしておく
CHILDPROC_INTERVAL = 10 #Debug

g_benchmarklogLock = threading.Lock()
# --------------------------------------------------------------------------------------------------
# スクレイピング本体
# --------------------------------------------------------------------------------------------------
import time
from datetime import datetime
def scrape_url(groupName, targetGroupDic, isActive = 'Active', threadGroupName = ''):
    retCode = 0

    # while True:  # 無限に繰り返し
    try:
        groupLogger.log(groupName, 'scrape_sched', 'scrape_url invoked', {'isActive': isActive, 'thread': threadGroupName})
        benchmarkStruct = {}
        benchmarkStruct['groupName'] = groupName
        benchmarkStruct['start'] = time_str1 = uf.getDateTime('%Y年%m月%d日 %H時%M分%S秒')

        # 前回アクセスから3分以上経過してなかったらスキップ
        isSkip = False
        interval = 60*3
        accessLog = Log.getAccessLogPath(groupName)
        if getattr(Log, 'g_Lock', None) is not None:
            with Log.g_Lock:
                logArray = Log.readAccessLog(groupName, accessLog)
        else:
            logArray = Log.readAccessLog(groupName, accessLog)

        if len(logArray) > 0:
            lastAccess = logArray[0].get('accessEndTime', '')
            if lastAccess != '':
                # 文字列を datetime オブジェクトに変換
                datetime_obj = datetime.strptime(lastAccess, cf.ACCESSDATETIME_FORMAT)
                # datetime オブジェクトをエポック秒に変換
                epoch_seconds = datetime_obj.timestamp()

                while True:
                    dateTimeNow = uf.getDateTime(useTimeData=True)
                    if  ( dateTimeNow.timestamp() - epoch_seconds) >= interval:
                        break
                    time.sleep(1)
                # dateTimeNow = uf.getDateTime(useTimeData=True)
                # if  ( dateTimeNow.timestamp() - epoch_seconds) < interval:
                #     isSkip = True

        if isSkip == False:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scrape_url: Start', note = threadGroupName)
            useBrave = False
            pid = -1

            # スクレイピング対象URL取得
            urlList = targetGroupDic[groupName].get('urlList', [])
            if len(urlList) == 0:
                urlList.append(targetGroupDic[groupName].get('url', ''))
            groupLogger.log(groupName, 'scrape_start', 'begin scraping loop', {'urlCount': len(urlList)})

            if len(urlList) > 0:
                portForGroup = 9070
                if useBrave == False:
                    DataDirectoryPath = ''
                    torConfigfile = ''
                    webDriverTempDir = ''
                    try:
                        portForGroup = targetGroupDic[groupName]['sockPort']
                        groupLogger.log(groupName, 'tor_setup', 'starting tor process', {'port': portForGroup})
                
                        # TODO:TORの設定と起動処理ってサブ側でやったほうがいいかも。。。困ってないからいったん保留
                        # Torの設定ファイルとデータフォルダを生成
                        num = portForGroup
                        DataDirectoryPath = CreateTorDataDirectory(num)
                        torConfigfile = CreateTorrc(num, portForGroup, DataDirectoryPath)
                        pid = ExecuteTorProcess(groupName, torConfigfile)
                    except Exception as e:
                        Log.LoggingWithFormat(groupName = groupName, logCategory = 'E', logtext = f'{str(e)}', note = threadGroupName)

                    try:
                        for url in urlList:
                            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scrape_url:getHTMLDiffandNotification Start', note = threadGroupName)
                            groupLogger.log(groupName, 'scrape_gethtml_start', 'calling getHTMLDiffandNotification', {'url': url})

                            retCode, webDriverTempDir = ms.getHTMLDiffandNotification(url, groupName, targetGroupDic, portForGroup)

                            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scrape_url:getHTMLDiffandNotification End', note = threadGroupName)
                            groupLogger.log(groupName, 'scrape_gethtml_end', 'getHTMLDiffandNotification returned', {'retCode': retCode})

                            # break
                            if retCode & cf.SUB_RETURNCODE_GETHTML:
                                break
                    finally:
                        # この時点でwebDriverTempDirが存在しないとExceptionになる
                        ProcessTerminateTree(groupName, pid)
                        groupLogger.log(groupName, 'cleanup', 'ProcessTerminateTree completed')

                        cleanup_paths = [
                            ('webdriver temp dir', webDriverTempDir),
                            ('tor data dir', DataDirectoryPath),
                        ]
                        for label, target_path in cleanup_paths:
                            if target_path:
                                for attempt in range(3):
                                    try:
                                        if os.path.isdir(target_path):
                                            shutil.rmtree(target_path)
                                        elif os.path.exists(target_path):
                                            os.remove(target_path)
                                        break
                                    except Exception as cleanup_err:
                                        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'cleanup({label}) failed on attempt {attempt+1}: {cleanup_err}', note = '')
                                        time.sleep(1)

                        if torConfigfile:
                            fo.Func_DeleteFile(torConfigfile)

            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scrape_url:ProcessTerminateTree End', note = threadGroupName)
        else:
            Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'isSkip==True', note = threadGroupName)
            groupLogger.log(groupName, 'scrape_skip', 'skipped because interval threshold not met')

        benchmarkStruct['end'] = time_str2 = uf.getDateTime('%Y年%m月%d日 %H時%M分%S秒')
        # 文字列を datetime オブジェクトに変換
        time_obj1 = datetime.strptime(time_str1, '%Y年%m月%d日 %H時%M分%S秒')
        time_obj2 = datetime.strptime(time_str2, '%Y年%m月%d日 %H時%M分%S秒')
        # 時間差を計算
        time_diff = time_obj2 - time_obj1
        # 分と秒に変換
        minutes = time_diff.seconds // 60
        seconds = time_diff.seconds % 60

        # 結果をフォーマット
        benchmarkStruct['diffTIme'] = f"{minutes}分{seconds}秒"
        if isSkip:
            benchmarkStruct['getHtmlResult'] = '前回から3分経過していないのでスキップ'
        else:
            benchmarkStruct['getHtmlResult'] = Log.getHtmlStatus(retCode)

        benchmarkStruct['isActive'] = isActive
        with g_benchmarklogLock:
                accessLogStruct = {}

                # まずは既存のログを読み込み
                existDataStruct = fo.Func_ReadJson2Dict(cf.PATH_BENCHMARK_FILE)
                newDataArray = existDataStruct.get('log',[])

                # 既存データに今回データを追加
                newDataArray.append(benchmarkStruct)
                accessLogStruct['log'] = newDataArray
                if getattr(Log, 'g_Lock', None) is not None:
                    with Log.g_Lock:
                        Log.saveAccessLog2File(groupName, accessLogStruct, cf.PATH_BENCHMARK_FILE)
                else:
                    Log.saveAccessLog2File(groupName, accessLogStruct, cf.PATH_BENCHMARK_FILE)
        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scrape_url: Write PATH_BENCHMARK_FILE End', note = threadGroupName)

    except Exception as e:
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        Log.LoggingWithFormat(groupName = groupName, logCategory='E', logtext=error_message, note = threadGroupName)
        groupLogger.log(groupName, 'scrape_error', 'exception occurred', {'error': str(e), 'traceback': traceback.format_exc()})

    Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'scrape_url: End', note = threadGroupName)
    return retCode


def isActiveGroup(groupName):
    ret = False

    try:
        accessLogGroup = Log.readAccessLogStruct(groupName, Log.getAccessLogPath(groupName))

        # アクセスした回数が少ない場合はまだ新しい
        if len(accessLogGroup) <= 30:
            return True
        
        logArray = accessLogGroup.get('log', [])

        now = datetime.now()
        for logData in logArray:
            accessEndTime = logData.get('mainStartTime', '')

            if accessEndTime != '':
                date_object = datetime.strptime(accessEndTime, cf.ACCESSDATETIME_FORMAT)

                # 現在の日時との差を計算（日数）
                days_passed = (now - date_object).days
            else:
                days_passed = 0

            # まず7日以内に更新があったか見る
            if days_passed <= 7:
                getHTMLStatus = logData.get('getHTMLStatus', '')

                if uf.strstr('成功', getHTMLStatus):
                    ret = True
                    break
            else:
                if days_passed > 7:
                    ret = False
                else:
                    # 指定期間以前のログがないってことは最近追加したかなんかの手違いでログが吹き飛んだのでアクティブ扱い
                    ret = True

    except Exception as e:
        Log.LoggingWithFormat(groupName = groupName, logCategory = 'E', logtext = f'{str(e)}', note = '')

    return ret

# 接続はできるけどシステム開始時前7日以内に更新がなかったやつらは準アクティブ（システム上優先度下げるだけでアクティブ扱い）
# 完全にはフィルタできないけど接続できるのに更新全くない奴は間引けるはず
def isPreActiveGroup(groupName):
    retIsPreActive = True
    
    try:
        accessLogGroup = Log.readAccessLogStruct(groupName, Log.getAccessLogPath(groupName))
        logArray = accessLogGroup.get('log', [])

        now = datetime.now()
        outOfTerm = False
        for logData in logArray:
            accessEndTime = logData.get('mainStartTime', '')

            if accessEndTime != '':
                date_object = datetime.strptime(accessEndTime, cf.ACCESSDATETIME_FORMAT)

                # 現在の日時との差を計算（日数）
                days_passed = (now - date_object).days
            else:
                days_passed = 0

            # 60日以内に更新があったか見る
            if days_passed <= 60:
                getHTMLStatus = logData.get('getHTMLStatus', '')

                if uf.strstr('差分あり', getHTMLStatus):
                    retIsPreActive = False
                    break
            else:
                # 指定期間以前のログがないってことは最近追加したかなんかの手違いでログが吹き飛んだのでアクティブ扱い
                outOfTerm = True

        if outOfTerm == False:
            retIsPreActive = False

    except Exception as e:
        Log.LoggingWithFormat(groupName = groupName, logCategory = 'E', logtext = f'{str(e)}', note = '')

    return retIsPreActive


def thread_scrape_url_SingleThread(groupList, targetGroupDic, isActive = '', threadGroupName = ''):
    try:
        while True:
            for groupName in groupList:
                scrape_url(groupName, targetGroupDic, isActive = isActive, threadGroupName = threadGroupName)

    except Exception as e:
        Log.LoggingWithFormat(groupName = groupName, logCategory = 'E', logtext = f'{str(e)}', note = '')
# --------------------------------------------------------------------------------------------------
# メイン
# --------------------------------------------------------------------------------------------------
def main_threadVer():
    try:
        global g_TargetGroupDic    #もはやグローバルの必要なし
        global g_Thread_SendAccessLog
        dicAccessLogLock = {}
        targetGroupDic_Active = {}
        targetGroupDic_UseSeleniumBase = {}
        targetGroupDic_PreActive = {}
        targetGroupDic_NonActive = {}

        init()
        g_TargetGroupDic = getTargetList_Dict()

        # 各スレッドで書き込み、メインプロセスで読み込むので排他用
        Log.g_Lock = threading.Lock()

        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # Debug バージョン１からのログデータ転記ロジック
        # v1ReportPath = getTargetList_Dict(r'E:\MonitorSystem\Source\OnionScraper\Config\TargetURLReport.json')

        # for item in g_TargetGroupDic.keys():
        #     newLogPah = os.path.join(r'E:\MonitorSystem\Source\OnionScraperV2\Data\Log', item)
        #     newLogName = f'{item}_Access.log'
        #     logName = f'{item}.log'
        #     oldLogFilePah = os.path.join(r'E:\MonitorSystem\Source\OnionScraper\Data\Log\EachGroup', logName)
        #     newLogFilePah = os.path.join(newLogPah, newLogName)
        # # #     fo.Func_CreateDirectry(newLogPah)
        # # #     fo.Func_CopyFile(oldLogFilePah, newLogFilePah)

        #     accessLogStruct = Log.readAccessLogStruct(item, newLogFilePah)
        #     if item in v1ReportPath:
        #         accessLogStruct['lastAccessSuccessTime'] = v1ReportPath[item].get('lastAccessSuccessTime', v1ReportPath[item].get('lastAccessErrorTime', ''))
        #         Log.saveAccessLog2File(item, accessLogStruct, newLogFilePah)

        # ms.sendAccessLog(g_TargetGroupDic)
        # groupNameList = ['BianLian']
        # Log.LoggingWithFormat(groupName = 'LogTestGroup', logCategory = 'I', logtext = 'Test', note = '')
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------

        # 使用するポート番号はあらかじめ決めておく→できたらランダムがいいけど非同期にしてるのでポートの仕様状態が管理しきれない
        portNum = 9070
        i = 0
        for groupName in g_TargetGroupDic.keys():
            g_TargetGroupDic[groupName]['sockPort'] = portNum + i
            i += 1

            dicAccessLogLock[groupName] = threading.Lock()

            useSeleniumBase_uc = g_TargetGroupDic[groupName].get('useSeleniumBase_uc', False)

            # SeleniumBaseを使用するサイトは一つにまとめてシングルスレッドで処理したい。
            # ライブラリ自体が並列処理に対応しておらず、pytestとかを使用して並列にする方法はあるらしいが現状の作りでは複雑になりそうなので
            if useSeleniumBase_uc:
                targetGroupDic_UseSeleniumBase[groupName] = g_TargetGroupDic[groupName].copy()
            else:
                # アクティブグループと非アクティブグループのリストを分ける
                if isActiveGroup(groupName):
                    if isPreActiveGroup(groupName):
                        targetGroupDic_PreActive[groupName] = g_TargetGroupDic[groupName].copy()
                    else:
                        targetGroupDic_Active[groupName] = g_TargetGroupDic[groupName].copy()
                else:
                    targetGroupDic_NonActive[groupName] = g_TargetGroupDic[groupName].copy()

        # Wather用にどれがアクティブでどれが非アクティブのグループかファイルに保存
        watcherDict = {}
        for key in targetGroupDic_Active:
            watcherDict[key] = 'Active'
        for key in targetGroupDic_PreActive:
            watcherDict[key] = 'PreActive'
        for key in targetGroupDic_NonActive:
            watcherDict[key] = 'NonActive'

        fo.Func_WriteDict2Json(cf.WATCHER_JSON_PATH, watcherDict)

        groupNameList = list(targetGroupDic_Active.keys())

        # 渡しておくとかできんのかな 
        cf.g_dicAccessLogLock = dicAccessLogLock.copy()

        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        isDebug = False

        # ---------------------------------------------------------------------------------------------------------------
        # ---------------------------------------------------------------------------------------------------------------
        # ba.deleteFromBOX()
        
        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        # 以下if/elseをコメントした状態でデバッグモードでは一応動作してた。(2023/12/11)
        # コメント戻してデバッグモードで動作させてみる
        # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
        if isDebug == False:
            # # アクセスログ送信用スレッドの作成
            g_Thread_SendAccessLog = threading.Thread(target=thread_SendAccessLog)
            # スレッドの開始True
            g_Thread_SendAccessLog.start()

            # 非アクティブグループ/準アクティブグループのシングルスレッド実行
            if len(targetGroupDic_PreActive) > 0:
                thread_scrape_url_ForPreActive_ = threading.Thread(target = thread_scrape_url_SingleThread,args=(list(targetGroupDic_PreActive.keys())+list(targetGroupDic_NonActive.keys()), {**targetGroupDic_PreActive,**targetGroupDic_NonActive}, 'NonActive-PreActive', 'OtherGroups', ))
                thread_scrape_url_ForPreActive_.start()

            if len(targetGroupDic_UseSeleniumBase) > 0:
                thread_scrape_url_ForSeleniumBase_ = threading.Thread(target = thread_scrape_url_SingleThread,args=(list(targetGroupDic_UseSeleniumBase.keys()), {**targetGroupDic_UseSeleniumBase}, 'UseSeleniumBase', 'SurfaceWebGroups', ))
                thread_scrape_url_ForSeleniumBase_.start()
        else:
            # if len(targetGroupDic_UseSeleniumBase) > 0:
            #     thread_scrape_url_ForSeleniumBase_ = threading.Thread(target = thread_scrape_url_SingleThread,args=(list(targetGroupDic_UseSeleniumBase.keys()), {**targetGroupDic_UseSeleniumBase}, 'UseSeleniumBase', 'SurfaceWebGroups', ))
            #     thread_scrape_url_ForSeleniumBase_.start()
            # targetGroupDic_Active.update(targetGroupDic_UseSeleniumBase)

            cf.headless_options = 2
            groupNameList = ['RustyLocker']
            # groupNameList = ['Lockbit5.0']

        # 同時に実行するスレッド数の上限
        MAX_THREADS = 5

        if len(groupNameList) > MAX_THREADS:
            max_Threads = MAX_THREADS
        else:
            max_Threads = len(groupNameList)

        def split_list(lst, size):
            # sizeが0以下の場合、空のリストを返す
            if size <= 0:
                return []

            # lstをできるだけ均等に`size`個のサブリストに分割する
            n = len(lst)
            avg = n // size
            remainder = n % size

            result = []
            start = 0

            for i in range(size):
                end = start + avg + (1 if i < remainder else 0)
                result.append(lst[start:end])
                start = end

            return result
        
        if True:
            activeThreadList = []
            # 指定したスレッド数に分割したリストをもらう
            activeGroupListArray = split_list(groupNameList, max_Threads)

            groupCount = 1
            for groupList in activeGroupListArray:
                threadGroupName = f'Group{groupCount}'
                thread_ = threading.Thread(target = thread_scrape_url_SingleThread,args=(groupList, targetGroupDic_Active, 'Active', threadGroupName, ))
                groupCount += 1
                thread_.start()
                activeThreadList.append(thread_)
                
            for thread_ in activeThreadList:
                thread_.join()
        else:
            horyu = 1
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # popできなくて固まることおおいから保留
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # with ThreadPoolExecutor(max_workers=max_Threads) as executor:
            #     # groupNameListを無限にループするイテレータに変換
            #     group_name_iterator = itertools.cycle(groupNameList)
            #     futures = {}

            #     while True:
            #         # 必要な場合にスレッドを追加
            #         while len(futures) < max_Threads:
            #             group = next(group_name_iterator)
            #             # future = executor.submit(wrap_GetHtmlDiff, group)
            #             future = executor.submit(scrape_url, group, g_TargetGroupDic)
            #             futures[future] = group

            #         # 完了したスレッドを待つ
            #         for future in as_completed(futures):
            #             group = futures.pop(future)
            #             Log.LoggingWithFormat(groupName = 'MainProc', logCategory = 'I', logtext = f'Popped:{group}', note = '')

            #             try:
            #                 future.result()
            #             except Exception as exc:
            #                 print(f'{group} generated an exception: {exc}')
                        
            #             # 完了したスレッドのスペースを新しいスレッドで埋める
            #             new_group = next(group_name_iterator)
            #             Log.LoggingWithFormat(groupName = 'MainProc', logCategory = 'I', logtext = f'Push Next:{new_group}', note = '')

            #             # new_future = executor.submit(wrap_GetHtmlDiff, new_group)
            #             new_future = executor.submit(scrape_url, new_group, g_TargetGroupDic)
            #             futures[new_future] = new_group
            #             Log.LoggingWithFormat(groupName = 'MainProc', logCategory = 'I', logtext = f'Pushed Next:{new_group}', note = '')
    except Exception as e:
        Log.LoggingWithFormat(groupName = 'MainProc', logCategory = 'E', logtext = f'{str(e)}', note = '')
        messageBox('main_threadVer', str(e))

        # TODO:ファイル決めてログ書き出し

    finally:
        threadWait_SendAccessLog()

    Log.LoggingWithFormat(groupName = 'MainProc', logCategory = 'I', logtext = f'main_threadVer End', note = '')

if __name__ == "__main__":
    # ----------------------------------------------------------------
    # 自身の終了をハンドリング
    # ----------------------------------------------------------------
    # atexitで正常終了時の処理を登録
    atexit.register(handle_exit)
    # SIGTERMをハンドル
    signal.signal(signal.SIGTERM, handle_sigterm)

    main_threadVer()
