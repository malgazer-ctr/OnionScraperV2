from ast import And
import os
import sys
from re import I
import datetime
import numpy as np
import time
import subprocess
import shutil
import MonitorSub as ms
import base64
import asyncio
import psutil
import fasteners
from Config import Config as cf
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import Notification
from OnionScraperLib import Diff as df
from OnionScraperLib import Log

globalProcessTimer_ReportMail = 0
globalProcessTimerYuichi_ReportMail = 0
globalProcessTimer_Report = 0

#--------------------------------------------------------------------------------------
# 初期処理系関数
#--------------------------------------------------------------------------------------
def init():
    # fo.Func_removeAllFiles(cf.PATH_HTMLDIFF_DATA)
    # fo.Func_removeAllFiles(cf.PATH_HTMLDIFF_RESULTS)
    fo.Func_removeAllFiles(cf.TARGET_URL_LISTSUB_DIR)

    uf.killProccess('tor.exe', True)

    fo.Func_CreateDirectry(cf.PATH_LOG_DIR)
    # uf.startProcess(cf.PATH_TOREXE)
    dateTime = uf.getDateTime('%Y%m%d_%H%M%S')
    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'Crawl_All_{}.log'.format(dateTime))
    fo.Func_RenameFileEx(cf.PATH_ALLLOG_FILE, tmpPath)
    
    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'AccessLogLock')
    fo.Func_DeleteFile(tmpPath)
    tmpPath = os.path.join(cf.PATH_LOG_DIR, r'AccessLog_{}.log'.format(dateTime))
    fo.Func_RenameFileEx(cf.PATH_ACCESSLOG_FILE, tmpPath)

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
    new_path = os.path.join(cf.PATH_TOR_DATA, 'tor'+str(num))
    
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

#--------------------------------------------------------------------------------------
# 監視対象URLリストの読み込みと配列作成
#--------------------------------------------------------------------------------------
def getTargetList(path = ''):
    targetPath = path
    if targetPath == '':
        targetPath = cf.TARGET_URL_LIST_PATH

    ret = []
    
    tempRet = fo.Func_CSVReadist(targetPath)

    for item in tempRet:
        if len(item) > 0:
            if  len(item[0]) > 0 and item[0][0] != '#':
                ret.append(item)
                
    return ret

def getTargetList_Dict(path = ''):
    try:
        ret = {}
        targetPath = path
        if targetPath == '':
            targetPath = cf.TARGET_URL_JSON_PATH

        ret = fo.Func_ReadJson2Dict(targetPath)

    except Exception as e:
        locationInfo_file_, locationInfo_line_, locationInfo_func_ = Log.Trace.execution_location2()
        Log.LoggingWithFormat(groupName = 'MainProx',
                               file = locationInfo_file_,
                               line = locationInfo_line_,
                               func = locationInfo_func_,
                               logCategory = 'e',
                               logtext = str(e.args),
                               note = '')

    return ret

def createTargetURLList_forDict(separateCnt = 5, targetURLListPath = ''):
    try:
        ret = []

        targetList = cf.getTargetLeakSite(cf.TARGET_URL_JSON_PATH)
        i = 1
        activeSite = []
        nonActiveSite = []

        # プロセスを2つ以上湧かす指定の場合は一つを非アクティブサイト用に割り当てる
        if separateCnt > 1:
            # 非アクティブのサイトも監視するけどアクティブとリストを混在させると遅くなるので、非アクティブのみのリストにする
            # 非アクティブのサイトは必ず三つ目の要素にコメントあり
            # result = filter(lambda item: item[0]['IsActive'] == True and item[0]['exclude'] == False, targetList.items())
            activeCount = 0
            inActiveCount = 0

            activeGroupDictArray = dict(filter(lambda x: uf.strstr('InActive', x[1].get('IsActive', 'Active')) == False, targetList.items()))
            inActiveGroupDictArray = dict(filter(lambda x: uf.strstr('InActive', x[1].get('IsActive', 'Active')) == True, targetList.items()))
            activeCount = len(activeGroupDictArray)
            inActiveCount = len(inActiveGroupDictArray)

            # 1起源のsubファイルを作るので、非アクティブ用に1マイナスした値をmaxにしとく
            if inActiveCount > 0:
                rangeMax = separateCnt - 1
            else:
                rangeMax = separateCnt

            # アクティブサイトの件数を指定プロセス数で割ってなるべく均等に分割
            separateCntArray = [(activeCount + i) // rangeMax for i in range(rangeMax)]

            tmpDict = {}
            for cnt in separateCntArray:
                activeGroupDictArrayTmp = activeGroupDictArray.copy()
                tmpDict.clear()
                for key in activeGroupDictArrayTmp.keys():
                    tmpDict[key] = activeGroupDictArrayTmp[key]
                    # 次のループは続きからにするのでコピーしたやつは消しとく
                    activeGroupDictArray.pop(key)

                    if len(tmpDict) == cnt:
                        break

                path = os.path.join(cf.TARGET_URL_LISTSUB_DIR, 'TargetURL_Sub{}.json'.format(i))
                fo.Func_WriteDict2Json(path, tmpDict)
                ret.append(path)
                i += 1
            
            if len(inActiveGroupDictArray) > 0:
                    path = os.path.join(cf.TARGET_URL_LISTSUB_DIR, 'TargetURL_Sub{}.json'.format(i))
                    fo.Func_WriteDict2Json( path, inActiveGroupDictArray )
                    ret.append(path)                                
        else:
            # シングルでやる場合はまるまるコピー
            path = os.path.join(cf.TARGET_URL_LISTSUB_DIR, 'TargetURL_Sub{}.json'.format(i))
            fo.Func_CopyFile(cf.TARGET_URL_JSON_PATH, path)
            ret.append(path)

    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return ret

#--------------------------------------------------------------------------------------
# クローリング用のサブプロセス呼び出し
#--------------------------------------------------------------------------------------
async def async_func(num):
    loop = asyncio.get_event_loop()
    print("async_funcで処理（num=" + str(num)  + ")")
    await loop.run_in_executor(None, wrap_CallPyFileForCrawl, num)


def wrap_CallPyFileForCrawl(num):
    try:
        print("wrap_CallPyFileForCrawlが呼ばれた(num="+ str(num) + ")")
        portnum = 9061 + num*10
        
        #無限ループさせる=同一ポートのプログラムで繰り返しを完結させる
        while True:
            #randam_sleep = random.randint(0, 15)
            #print("ランダムな秒数待機(randam_sleep="+ str(randam_sleep) + ")")
            #time.sleep(randam_sleep)

            path = os.path.join(cf.TARGET_URL_LISTSUB_DIR, 'TargetURL_Sub{}.json'.format(num))
            
            CallPyFileForCrawl(path, num, portnum)

            time.sleep(5)
    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        print("wrap_CallPyFileForCrawlでエラーが発生:" + str(e.args))

def generateAccessStatusStr(retunCode):
    ret = ''

    accessStatusStr_Option = ''
    if retunCode & cf.SUB_RETURNCODE_GETHTML_FINDOBJECT:
        accessStatusStr_Option = '(オブジェクト待機成功)'
    elif retunCode & cf.SUB_RETURNCODE_GETHTML_NOTFINDOBJECT:
        accessStatusStr_Option = '(オブジェクト待機失敗)'
    
    if retunCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL:
        ret = "HTML取得成功 差分あり(個別対応)" + accessStatusStr_Option
    elif retunCode & cf.SUB_RETURNCODE_DIFF:
        ret = "HTML取得成功 差分あり" + accessStatusStr_Option
    elif retunCode & cf.SUB_RETURNCODE_NODIFF_INDIVISUAL:
        ret = "HTML取得成功 差分なし(個別対応)" + accessStatusStr_Option
    elif retunCode & cf.SUB_RETURNCODE_NODIFF:
        ret = "HTML取得成功 差分なし" + accessStatusStr_Option
    elif retunCode & cf.SUB_RETURNCODE_GETHTML_FAILED:
        ret = "HTML取得失敗" + accessStatusStr_Option
    elif retunCode == cf.SUB_RETURNCODE_ERR:
        ret = "何らかのエラーのためHTML取得処理に到達できませんでした" + accessStatusStr_Option
        
    return ret

def getDateTimeDiff(dateTimeStr1, dateTimeStr2, datetimeFormat = '%Y/%m/%d %H:%M:%S'):
    
    dateTime1 = datetime.datetime.strptime(dateTimeStr1, datetimeFormat)
    dateTime2 = datetime.datetime.strptime(dateTimeStr2, datetimeFormat)

    ret = dateTime2 - dateTime1

    return ret

import wmi
def CheckWindowsUpdate_WMI():
    try:
        # WMIオブジェクトの取得
        wmi_obj = wmi.WMI()
        # update = wmi_obj.Win32_QuickFixEngineering()
        # update_needed = False

        # for i in update:
        #     if i.InstalledOn is None:
        #         update_needed = True

        # if update_needed:
        #     print("未適用のWindows Updateがあります。")
        # else:
        #     print("未適用のWindows Updateはありません。")

        query = "SELECT HotFixID, Description FROM Win32_QuickFixEngineering WHERE HotFixID LIKE 'KB%' AND InstalledOn = NULL"

        # WMIクエリを実行して、Hotfixの情報を取得
        hotfixes = wmi_obj.query(query)

        # 結果を表示
        list = []
        for hotfix in hotfixes:
            hotfix_info = hotfix.HotFixID + ": " + hotfix.Description
            list.append(hotfix_info)

        if len(list) > 0:
            text = '\n'.join(hotfix_info)
            Notification.sendMail_Nofication(text, '【重要】未インストールのWindowsUpdateがあります', cf.SENDTO_REPORT_YUICHI)
    except Exception as e:
        print(str(e.args))

def CheckWindowsUpdate():
    resultFile = r"E:\MonitorSystem\Source\OnionScraper\Config\IsNeedToUpdate\ResultChkWinUpdate.txt"

    fo.Func_DeleteFile(resultFile)

    # WindowsUpdateチェック用
    ps_script_path = r"E:\MonitorSystem\Source\OnionScraper\Config\IsNeedToUpdate\IsNeedToWinUpdate.ps1"

    # PowerShellの実行ポリシーをUnrestrictedに設定
    # set_execution_policy = "Set-ExecutionPolicy Unrestricted"
    # subprocess.run(["powershell.exe", "-Command", set_execution_policy], shell=True)

    # PowerShellスクリプトを実行
    subprocess.run(["powershell.exe", "-File", ps_script_path], shell=True)

    cnt = 0
    for cnt in range(60):
        if fo.Func_IsFileExist(resultFile) == False:
            time.sleep(1)
        else:
            break

    if fo.Func_GetFileSize(resultFile) <= 0:
        resultFile = ''

    if resultFile != '':
        data = fo.Func_ReadFile(resultFile, encoding_='utf-16')
        Notification.sendMail_Nofication(data, '【重要】未インストールのWindowsUpdateがあります', cf.SENDTO_REPORT_YUICHI)

# import requests
# from bs4 import BeautifulSoup
# # from webdriver_manager import ChromeDriverManager
# from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.core.utils import ChromeType

# def CheckChromeDriverUpdate():
#     # from webdriver_manager.chrome import ChromeDriverManager
#     # from webdriver_manager.utils import ChromeType
#     # driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())

#     # 現在のバージョンを取得
#     current_version = ChromeDriverManager(chrome_type=ChromeType.GOOGLE).get_browser_version()
#     current_version_CM = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).get_browser_version()

#     # 最新のバージョンを取得
#     base_url = "https://chromedriver.chromium.org/downloads"
#     response = requests.get(base_url)
#     soup = BeautifulSoup(response.content, "html.parser")
#     # latest_version = soup.find("a", string="Latest Release").find_next("a").get_text()

#     # # 現在のバージョンと最新バージョンを比較
#     # if current_version == latest_version:
#     #     output = f"現在のバージョンは最新バージョンと同じです。バージョン: {current_version}"
#     # else:
#     #     output = f"新しいバージョンが利用可能です。現在のバージョン: {current_version}、最新バージョン: {latest_version}"
#     # print(output)

def updateTargetDictForReport(groupName, subProcRetCode):
    retDict = {}

    try:
        with fasteners.InterProcessLock(cf.PATH_JSON_REPORTLOCK_FILE):
            # アクセス日時や、非アクティブからの復帰ステータスの記録更新
            if fo.Func_IsFileExist(cf.TARGET_URL_JSON_REPORT_PATH) == False:
                fo.Func_CopyFile(cf.TARGET_URL_JSON_PATH, cf.TARGET_URL_JSON_REPORT_PATH)

            retDict = cf.getTargetLeakSite(cf.TARGET_URL_JSON_REPORT_PATH)

            item = retDict[groupName]
            datetimeFormat = '%Y/%m/%d %H:%M:%S'
            lastAccessTime = uf.getDateTime(datetimeFormat)

            # 永遠に接続できないやつもいつつ、n日間オフラインみたいな情報を出すためにプログラム起動時
            # の初回アクセストライした日時を覚えておく。これは書きえないでOKのはず
            # if ('firstAccessTime' in item) == False:
            #     item['firstAccessTime'] = lastAccessTime
            item.setdefault('firstAccessTime',lastAccessTime)

            if 'lastAccessTime' in item:
                item['prevAccessTime'] = item['lastAccessTime']
            
            item['lastAccessTime'] = lastAccessTime

            if 'siteStatus' in item:
                item['prevSiteStatus'] = item['siteStatus']

            if subProcRetCode & cf.SUB_RETURNCODE_GETHTML:
                item['lastAccessSuccessTime'] = lastAccessTime

                # HTMLが取得できたらActive扱いとする
                item['IsActive'] = 'Active'
                item['elapsedTime'] = ''
            else:
                # 最終アクセス成功日から7日以上経過していたらレポートメールで赤にする
                if 'lastAccessSuccessTime' in item:
                    offlineStartDate = item['lastAccessSuccessTime']

                    if offlineStartDate != 'None':
                        diffDate = getDateTimeDiff(offlineStartDate, lastAccessTime)
                else:
                    # item['firstAccessTime']は必ず入ってるはず
                    offlineStartDate = item['firstAccessTime']

                # 失敗したときは、最後の成功日時 or (ずっとアクセスできてない場合)初回アクセストライ日時からの経過時間だす
                diffDate = getDateTimeDiff(offlineStartDate, lastAccessTime)
                tmpStr = ''
                if diffDate.days > 0:
                    tmpStr = f'{diffDate.days}日'
                    
                    if diffDate.days > 6:
                        item['IsActive'] = 'InActive'                    

                item['elapsedTime'] = tmpStr

            if subProcRetCode & cf.SUB_RETURNCODE_GETHTML:
                item['siteStatus'] = '成功'
            else:
                item['siteStatus'] = '失敗'
                
            # ファイルも更新しておく 
            fo.Func_WriteDict2Json(cf.TARGET_URL_JSON_REPORT_PATH, retDict)
    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        
    return cf.TARGET_URL_JSON_REPORT_PATH, retDict

def CallPyFileForCrawl(ReakSiteListFile,num,socksport):
    try:
        global globalProcessTimer_Report
        global globalProcessTimer_ReportMail
        global globalProcessTimerYuichi_ReportMail

        print("CallPyFileForCrawlが呼ばれた(num="+ str(num) + ")")
        
        try:
            targetDict = getTargetList_Dict(ReakSiteListFile)
        except Exception as e:
            Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
            
        try:
            Log.Logging('None',"Torの設定ファイルとデータフォルダを生成")
            DataDirectoryPath = CreateTorDataDirectory(num)
            torrc_file = CreateTorrc(num, socksport, DataDirectoryPath)
        except Exception as e:
            Log.Logging('Exception',"{}: Exception:{} DataDirectoryPath:{} num:{}".format(Log.Trace.execution_location(), str(e.args),DataDirectoryPath, str(num)))

        for key in targetDict.keys():
            RansomName = key
            logName = os.path.join(cf.PATH_LOG_DIR, "{}_MonitorSub.log".format(RansomName))
            torURLList = []
            torURLList = targetDict[key].get('urlList', [])
            if len(torURLList) == 0:
                torURLList.append(targetDict[key]['url'])     

            Log.Logging(f'{RansomName}_Group({num})',"{}: ----------------------------------巡回の開始----------------------------------マルチプロセスグループ:{}".format(Log.Trace.execution_location(),ReakSiteListFile))

            for torURL in torURLList:
                base64_encode_byte = base64.b64encode("{},{}".format(RansomName,torURL).encode())
                base64_encode_string = base64_encode_byte.decode("ascii") 

                try:
                    # --------------------------------------------------------------------------
                    # 子プロセスを起動してスクレイピング
                    # --------------------------------------------------------------------------
                    Log.Logging(f'{RansomName}_Group({num})',"{}:子プロセス起動開始 {} {} {} {}".format(Log.Trace.execution_location(), base64_encode_string, torrc_file, logName, socksport))
                    
                    proc = ExecuteSubProcess(cf.PATH_SUBMOD,base64_encode_string,torrc_file,logName,socksport)
                    
                    Log.Logging(f'{RansomName}_Group({num})',"{}: 子プロセス起動終了待ち".format(Log.Trace.execution_location()))
                    
                    try:
                        #proc.wait(timeout=1200)
                        outs, errs = proc.communicate(timeout = 1200)
                    except subprocess.TimeoutExpired as e:
                        proc.kill()
                        outs, errs = proc.communicate()
                        Log.Logging(f'{RansomName}_Group({num})',"{}: 子プロセス proc.communicate 終了(Timeout)".format(Log.Trace.execution_location()))
                    
                    Log.Logging(f'{RansomName}_Group({num})',"{}: 子プロセス proc.communicate 終了".format(Log.Trace.execution_location()))
                    
                    accessStatusStr = generateAccessStatusStr(proc.returncode)

                    Log.Logging(f'{RansomName}_Group({num})',"{}: 子プロセス generateAccessStatusStr 終了".format(Log.Trace.execution_location()))
                    if accessStatusStr != '':
                        Log.Logging(f'{RansomName}_Group({num})', accessStatusStr, cf.PATH_ACCESSLOG_FILE)
                    
                    # 各リークサイトのアクセス記録を保持しておいて一定期間でメール送信
                    retTmp = updateTargetDictForReport(RansomName, proc.returncode)
                    targetSitePathforReport = retTmp[0]
                    targetSiteDictforReport = retTmp[1]

                    ProcessTimerTmp = time.time()

                    if globalProcessTimer_Report == 0:
                        globalProcessTimer_Report = ProcessTimerTmp
                    if globalProcessTimer_ReportMail == 0:
                        globalProcessTimer_ReportMail = ProcessTimerTmp
                    if globalProcessTimerYuichi_ReportMail == 0:
                        globalProcessTimerYuichi_ReportMail = ProcessTimerTmp

                    # レポート用のログファイルとして保存
                    if  (ProcessTimerTmp - globalProcessTimer_Report) > cf.REPORTMAIL_LOG_INTERVAL:
                        globalProcessTimer_Report = ProcessTimerTmp
                        # 念のためロック
                        with fasteners.InterProcessLock(cf.PATH_TARGETURLLOCK_FILE):
                            backupFileName = os.path.join(cf.PATH_CURRNET,r'Config\TargetURL_{}.json'.format(uf.getDateTime('%Y%m%d%H%M')))
                            fo.Func_RenameFile(cf.TARGET_URL_JSON_PATH, backupFileName, True)
                            fo.Func_CopyFile(targetSitePathforReport, cf.TARGET_URL_JSON_PATH)

                            # 正常にファイルコピーできてたら一時ファイル消す
                            if fo.Func_IsFileExist(cf.TARGET_URL_JSON_PATH):
                                fo.Func_DeleteFile(backupFileName)

                    # レポートメールを送信
                    if  (ProcessTimerTmp - globalProcessTimer_ReportMail) > cf.REPORTMAIL_INTERVAL:
                        globalProcessTimer_ReportMail = ProcessTimerTmp
                        # 12時間ごとにメール送信
                        htmlBody = Notification.createNotificationBody_AccessLogReport(targetSiteDictforReport)
                        Notification.sendMail(htmlBody,'【定期】リークサイトのアクセスログ', sendTo = cf.SENDTO_REPORT)
                    
                        # 未インストールのWindowsアップデートがあったら通知
                        CheckWindowsUpdate()
                        CheckWindowsUpdate_WMI()
                        
                        # 120日以上経過したらBOXから削除
                        ms.deleteFromBOX()

                        # ChromeDriverにアップデートがあるかチェック
                        # CheckChromeDriverUpdate()

                    # Yuichi Only
                    if  (ProcessTimerTmp - globalProcessTimerYuichi_ReportMail) > cf.REPORTMAIL_INTERVAL_YUICHI:
                        globalProcessTimerYuichi_ReportMail = ProcessTimerTmp
                        # 1時間ごとにメール送信
                        htmlBody = Notification.createNotificationBody_AccessLogReport(targetSiteDictforReport)
                        Notification.sendMail(htmlBody,'【定期】リークサイトのアクセスログ(Yuichi Only)', sendTo = cf.SENDTO_REPORT_YUICHI)

                    Log.Logging(f'{RansomName}_Group({num})',"{}: 子プロセス終了".format(Log.Trace.execution_location()))

                    if proc.returncode & cf.SUB_RETURNCODE_GETHTML:
                        break

                except subprocess.SubprocessError:
                    # タイムアウト時の例外で子プロセス終了
                    proc.kill()
                    outs, errs = proc.communicate()
                    Log.Logging(f'{RansomName}_Group({num})',"{}: 子プロセス強制終了(タイムアウト)".format(Log.Trace.execution_location()))
                    Log.Logging(f'{RansomName}_Group({num})'," 子プロセス強制終了(タイムアウト)", cf.PATH_ACCESSLOG_FILE)
                except Exception as e:
                    Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
                    Log.Logging(f'{RansomName}_Group({num})',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)), cf.PATH_ACCESSLOG_FILE)
                
            Log.Logging(f'{RansomName}_Group({num})',"{}: ----------------------------------巡回の終了----------------------------------".format(Log.Trace.execution_location()))
    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    time.sleep(15)

#arg1=base64_line, arg2=torConfigfile, arg3=LogName
def ExecuteSubProcess(pyfile,base64_line,torConfigfile,LogName,socksport):
    try:
        proc_str = 'python' + " " + pyfile + " " + base64_line + " " + torConfigfile + " " + LogName + " " + str(socksport)

        Log.Logging("None","{}: proc_str:{}".format(Log.Trace.execution_location(),proc_str))
        proc = subprocess.Popen(proc_str, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        time.sleep(10)
    except subprocess.subprocess.SubprocessError as err:
        print(err)

    return proc

def ProcessTerminate(pid):
    Log.Logging("None","Torプロセスを終了(pid=" + str(pid) + ")", cf.PATH_LOG_EACHGROUP)
    if psutil.pid_exists(pid):
        """         killcmd = "taskkill /F /PID " + str(pid) + " /T"
                proc = subprocess.Popen(killcmd,shell=True)
                time.sleep(5)
                if psutil.pid_exists(pid):
                    p = psutil.Process(proc.pid)
                    p.terminate() """ 
        ProcessTerminateTree(pid)
    else:
        Log.Logging("None","指定されたプロセスは存在しません(pid=" + str(pid) + ")", cf.PATH_LOG_EACHGROUP)

def ProcessTerminateTree(pid):
    try:
        Log.Logging("None","プロセスツリーを終了(pid=" + str(pid) + ")")
        parent_pid = pid   # my example
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True): 
            Log.Logging("None","子プロセスを終了")
            child.kill()
        Log.Logging("None","親プロセスを終了")
        parent.kill()
    except Exception as e:  
        print("ProcessTerminateTreeでエラーが発生:" + str(e.args))

#--------------------------------------------------------------------------------------
# サブプロセスの並列処理
#--------------------------------------------------------------------------------------
def heiretu(n):
    ClearTorDataDirectory()
    ClearSettingDirectory()

    #URLリストの分割
    # 戻りは未使用。監視対象のURLリストを指定の数で分割
    # 指定されたプロセス数のうち一つはつながらないサイトの念のため監視用に割り当てるので-1する
    if fo.Func_IsFileExist(cf.TARGET_URL_JSON_PATH) == True:
        # csvやめてjson→Dictionaryにした
        # createTargetURLList(n)

        # Reportが存在してかつ更新時間が新しかったらReportをこぴーする
        if fo.Func_IsFileExist(cf.TARGET_URL_JSON_REPORT_PATH):
            time_org = fo.Func_GetFileUpdateTime(cf.TARGET_URL_JSON_PATH, formatStr='')
            time_report = fo.Func_GetFileUpdateTime(cf.TARGET_URL_JSON_REPORT_PATH, formatStr='')

            if time_report > time_org:
                fo.Func_CopyFile(cf.TARGET_URL_JSON_REPORT_PATH, cf.TARGET_URL_JSON_PATH)

        createTargetURLList_forDict(n)

    loop = asyncio.get_event_loop()

    list_func = list()

    for i in range(1,n+1):
        print("並列実行する関数リストに追加(i=" + str(i) + ")")
        list_func.append(async_func(i))
    
    gather = asyncio.gather(*list_func)

    """     gather = asyncio.gather(
            async_func(1),
            async_func(2),
            async_func(3),
            async_func(4),
            async_func(5)
        ) """

    loop.run_until_complete(gather)

#--------------------------------------------------------------------------------------------------------------
#   Main
#--------------------------------------------------------------------------------------------------------------
# import signal

# def sig_handler(signum, frame) -> None:
#     sys.exit(1)

def main(sysArgs):
    # signal.signal(signal.SIGTERM, sig_handler)

    try:
        # args = sysArgs

        init()

        args = sys.argv
        isStartMonitor = False

        heiretu(5)
    finally:
        test = 0
        # signal.signal(signal.SIGTERM, signal.SIG_IGN)
        # signal.signal(signal.SIGINT, signal.SIG_IGN)

        # cf.TARGET_URL_JSON_PATHのバックアップをとる
        # backupFileName = os.path.join(cf.PATH_CURRNET,r'Config\TargetURL_{}.json'.format(uf.getDateTime('%Y%m%d%H%M')))
        # fo.Func_RenameFile(cf.TARGET_URL_JSON_PATH, cf.TARGET_URL_JSON_PATH, True)
        # fo.Func_RenameFile(cf.TARGET_URL_JSON_REPORT_PATH, cf.TARGET_URL_JSON_PATH, True)

        # signal.signal(signal.SIGTERM, signal.SIG_DFL)
        # signal.signal(signal.SIGINT, signal.SIG_DFL)
# debug
# レポートメールテスト
# DictDebug = cf.getTargetLeakSite(cf.TARGET_URL_JSON_REPORT_PATH)
# htmlBody = Notification.createNotificationBody_AccessLogReport(DictDebug)
# Notification.sendMail(htmlBody,'【定期】リークサイトのアクセスログ', sendTo = cf.SENDTO_REPORT)

if __name__ == '__main__':
    CheckWindowsUpdate_WMI()

    sys.exit(main(sys.argv))

