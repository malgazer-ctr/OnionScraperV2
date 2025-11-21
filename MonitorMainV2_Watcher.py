import time
import os
import MonitorSub as ms
from Config import Config as cf
from datetime import datetime
from OnionScraperLib import Notification
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import FileOperate as fo
import traceback

import shutil
import logging

def clean_temp_directory(temp_dir: str, hours: int = 2, max_retries: int = 3) -> tuple[list, list]:
    """
    指定されたテンポラリディレクトリ内の古いファイルとフォルダを削除します。

    Args:
        temp_dir (str): 削除対象のディレクトリパス
        hours (int): 経過時間の閾値（デフォルト：2時間）
        max_retries (int): 削除失敗時の最大リトライ回数（デフォルト：3回）

    Returns:
        tuple[list, list]: (成功したパスのリスト, 失敗したパスのリスト)
    """
    # ログの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    current_time = time.time()
    threshold = current_time - (hours * 3600)
    
    success_list = []
    failed_list = []

    try:
        # サブフォルダを含むすべてのファイルとディレクトリを走査
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            # まずファイルを処理
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    # ファイルの最終更新時刻を取得
                    mtime = os.path.getmtime(file_path)
                    
                    if mtime < threshold:
                        # 指定時間より古い場合、削除を試みる
                        success = False
                        for attempt in range(max_retries):
                            try:
                                os.remove(file_path)
                                success = True
                                success_list.append(file_path)
                                logging.info(f"ファイルを削除しました: {file_path}")
                                break
                            except Exception as e:
                                if attempt == max_retries - 1:
                                    logging.error(f"ファイルの削除に失敗: {file_path}, エラー: {str(e)}")
                                time.sleep(1)  # 少し待機してから再試行
                        
                        if not success:
                            failed_list.append(file_path)
                
                except Exception as e:
                    logging.error(f"ファイル処理中にエラーが発生: {file_path}, エラー: {str(e)}")
                    failed_list.append(file_path)

            # 次にディレクトリを処理
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    # ディレクトリの最終更新時刻を取得
                    mtime = os.path.getmtime(dir_path)
                    
                    if mtime < threshold:
                        # 指定時間より古い場合、削除を試みる
                        success = False
                        for attempt in range(max_retries):
                            try:
                                shutil.rmtree(dir_path)
                                success = True
                                success_list.append(dir_path)
                                logging.info(f"ディレクトリを削除しました: {dir_path}")
                                break
                            except Exception as e:
                                if attempt == max_retries - 1:
                                    logging.error(f"ディレクトリの削除に失敗: {dir_path}, エラー: {str(e)}")
                                time.sleep(1)  # 少し待機してから再試行
                        
                        if not success:
                            failed_list.append(dir_path)

                except Exception as e:
                    logging.error(f"ディレクトリ処理中にエラーが発生: {dir_path}, エラー: {str(e)}")
                    failed_list.append(dir_path)

    except Exception as e:
        logging.error(f"全体の処理中にエラーが発生: {str(e)}")

    return success_list, failed_list

def messageBox(title, text_):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    root.lift()
    messagebox.showwarning(title, text_)
    root.destroy()

def getTargetList_Dict(path = ''):
    try:
        ret = {}
        targetPath = path
        if targetPath == '':
            targetPath = cf.TARGET_URL_JSON_PATH

        ret = fo.Func_ReadJson2Dict(targetPath)

    except Exception as e:
        messageBox('ERROR:getTargetList_Dict')

    return ret

if __name__ == "__main__":
    try:
        # targetGroupDic = getTargetList_Dict()
        intervalOneHour = 60*60

        targetGroupDic = {}

        # システムと同時起動する予定なので（現状は別々のバッチを同時にたたく）
        # 最初の60分くらいはスリープで様子見
        # time.sleep(3600)

        while True:
            try:
                # 毎回読み直す
                # デバッグなどでシステムだけ再起動することもあるかもなので（システム再起動するとこのファイルは更新される可能性あり）
                targetGroupDic = fo.Func_ReadJson2Dict(cf.WATCHER_JSON_PATH)

                if len(targetGroupDic) <= 0:
                    time.sleep(3)
                    continue

                notificationGroup = {}
                notificationGroup_Accessed = {}
                # 現在時刻を取得
                dateTimeNow = uf.getDateTime(useTimeData=True)
                for groupName in targetGroupDic.keys():
                    isActive = True
                    isPreActive = False
                    isNonActive = False
                    status = targetGroupDic[groupName]

                    if status == 'Active':
                        isActive = True
                    elif status == 'PreActive':
                        isPreActive = True
                    elif status == 'NonActive':
                        isNonActive = True

                    if groupName == 'RANSOM_CORP':
                        debug = 1

                    accessLogFile = os.path.join(os.path.join(cf.PATH_LOG_DIR, groupName), f'{groupName}_Access.log')

                    notificationGroup[groupName] = {}
                    notificationGroup[groupName]['status'] = status
                    notificationGroup[groupName]['accessError'] = False
                    notificationGroup[groupName]['lastaccess'] = None
                    if fo.Func_IsFileExist(accessLogFile):
                        existData = fo.Func_ReadJson2Dict(accessLogFile)
                        logArray = existData.get('log',[])
                        if len(logArray) > 0:
                            lastAccess = logArray[0].get('accessEndTime', 'アクセス履歴なし')
                            # notificationGroup[groupName]['lastaccess'] = lastAccess
                            notificationGroup.setdefault(groupName, {})['lastaccess'] = lastAccess

                            # 文字列を datetime オブジェクトに変換
                            datetime_obj = datetime.strptime(lastAccess, cf.ACCESSDATETIME_FORMAT)
                            # datetime オブジェクトをエポック秒に変換
                            epoch_seconds = datetime_obj.timestamp()

                            interval = intervalOneHour*2

                            # 非アクティブたちはシングルスレッドなので眺めのインターバル
                            if isPreActive or isNonActive:
                                interval = intervalOneHour*4
                
                            if  ( dateTimeNow.timestamp() - epoch_seconds) >= interval:
                                notificationGroup[groupName]['accessError'] = True

                if len(notificationGroup) > 0:
                    dataStr = ''
                    dataStr_Accessed = ''

                    for groupName in notificationGroup.keys():
                        lastAccess = notificationGroup[groupName]['lastaccess']
                        statusTmp = notificationGroup[groupName]['status']
                        if notificationGroup[groupName].get('accessError', False):
                            dataStr += f'<tr><td>{groupName}</td><td>{lastAccess}</td><td>{statusTmp}</td></tr>'
                        else:
                            dataStr_Accessed += f'<tr><td>{groupName}</td><td>{lastAccess}</td><td>{statusTmp}</td></tr>'

                    bodyText = '以下のグループのサイトは２時間（準アクティブ、非アクティブは4時間）以上接続できていません'
                    groupsTable = f'\
                    <table border="1">\
                        <tr>\
                            <th>グループ名</th>\
                            <th>最終アクセス日時</th>\
                            <th>ステータス</th>\
                        </tr>\
                        {dataStr}\
                    </table>'
                    bodyText2 = '<br><br>以下は２時間（準アクティブ、非アクティブは4時間）以内に接続トライしたグループ'
                    groupsTable2 = f'\
                    <table border="1">\
                        <tr>\
                            <th>グループ名</th>\
                            <th>最終アクセス日時</th>\
                            <th>ステータス</th>\
                        </tr>\
                        {dataStr_Accessed}\
                    </table>'

                    Notification.sendMail_Nofication(bodyText+groupsTable+bodyText2+groupsTable2, '【重要】接続不良を検知', cf.SENDTO_REPORT_YUICHI, isUrgent = False)
                    # 一回送ったらスリープさせとく
                    hour = 60*60

                    # 臨時処理。ChromeDriverが作成したファイルが残ってしまうのでこちらで処理する
                    # 一定時間経過したファイルを削除
                    temp_directory = r"C:\Users\malga\AppData\Local\Temp"
                    clean_temp_directory(temp_directory)
                    time.sleep(hour*2)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                # 最後の行（エラーが発生した行）の情報を取得
                filename, line_no, func_name, text = tb[-1]
                print(f"エラー発生箇所: {filename}, {line_no}行目")

                continue
    except Exception as e:
        messageBox('ERROR', f'Main{str(e.args)}')