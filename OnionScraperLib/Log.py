import datetime
import os
import inspect
from Config import Config as cf
from OnionScraperLib import FileOperate as fo
import fasteners
import threading


# プロセス開始時にメイン関数で格納

g_Lock = None
# Python 3.7以降
from contextlib import nullcontext
import sys

if sys.version_info >= (3, 7):
    g_Lock = nullcontext()  # 最初からnullcontextで初期化
else:
    # Python 3.6以前用のダミーロック
    class DummyLock:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    
    g_Lock = DummyLock()  # 最初からDummyLockで初期化
    
class Trace():
    """
    ログ出力とセットで使う処理をまとめたクラス
    """
    @classmethod
    def execution_location(self):
        """
        処理の実行場所を出力する。[ファイル名: 行番号  メソッド名]
        """
        frame = inspect.currentframe().f_back
        return "{}:LINE({}):Function({})".format(os.path.basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name)
        # return os.path.basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name

    def execution_location2():
        """
        処理の実行場所を出力する。[ファイル名: 行番号  メソッド名]
        """
        frame = inspect.currentframe().f_back
        return os.path.basename(frame.f_code.co_filename), frame.f_lineno, frame.f_code.co_name
    
def Logging(RansomName, logtext, logFilePath = cf.PATH_ALLLOG_FILE):
    dt_now = datetime.datetime.now()
    dt_now_tstr = dt_now.strftime("%Y/%m/%d %H:%M:%S")

    if RansomName == "None":
        outtext = '[' + dt_now_tstr + ']:' + logtext + '\n'
    else:
        outtext = '[' + dt_now_tstr + ']:' + "【" + RansomName + "】"+ logtext + '\n'

    with g_Lock:
        with open(logFilePath, mode='a', encoding='utf-8') as f:
            f.write(outtext)

def get_caller_info():
    # 現在のスタックフレームを取得
    stack = inspect.stack()

    # 呼び出し元の情報を取得
    # stack[2] が呼び出し元(LoggingWithFormat)のさらに一個上（ログをとりたい場所）のスタックフレーム
    # stack[0] は現在の関数（get_caller_info）のスタックフレーム
    caller_info = stack[2]
    frame = caller_info[0]
    info = {
        'file_name': caller_info.filename,
        'function_name': caller_info.function,
        'line_number': caller_info.lineno
    }
    return caller_info.filename, caller_info.lineno, caller_info.function

# logCategory
def LoggingWithFormat(groupName = '', file = '', line = '', func = '', logCategory = 'I', logtext = '', note = '', logFilePath = cf.PATH_ALLLOG_FILE):
    dt_now = datetime.datetime.now()
    dt_now_tstr = dt_now.strftime("%Y/%m/%d %H:%M:%S")
    logFileExceptionPath = ''

    file_ = file
    line_ = line
    func_ = func
    # これらがわたってきたらそっちを優先
    if file_ == '' and line_ == '' and func_ == '':
        file_, line_, func_ = get_caller_info()

    name = 'Unknown'
    if groupName != '':
        name = groupName

    cate = 'Info'
    if logCategory.lower() == 'e':
        cate = 'Exception'
        logFileExceptionPath = cf.PATH_ALLLOG_EXCEPTION_FILE

    outtext = f'{dt_now_tstr},{name},{file_},{line_},{func_},{cate},{logtext},{note}\n'
    with g_Lock:
        with open(logFilePath, mode='a', encoding='utf-8') as f:
            f.write(outtext)
        if logFileExceptionPath != '':
            with open(logFileExceptionPath, mode='a', encoding='utf-8') as f:
                f.write(outtext)

# def Logging(RansomName, logtext, logFilePath = defaultLogFile):
        
#     try:
#         dt_now = datetime.datetime.now()
#         dt_now_tstr = dt_now.strftime("%Y/%m/%d %H:%M:%S")

#         if RansomName == "None":
#             outtext = '[' + dt_now_tstr + ']:' + logtext + '\n'
#         else:
#             outtext = '[' + dt_now_tstr + ']:' + "【" + RansomName + "】"+ logtext + '\n'

#         with fasteners.InterProcessLock(cf.PATH_ACCESSLOGLOCK_FILE):
#             with open(logFilePath, mode='a', encoding='utf-8') as f:
#                 f.write(outtext)

#     except Exception as e:  
#         print("エラーが発生:" + str(e.args))


    
#----------------------------------------------------------------------------------------------------------
# サイトごとのログをファイルに保存・読み込みする関数
#----------------------------------------------------------------------------------------------------------
def mergeAccessLogDataList(accessLogDataList, logFilePath):
    from datetime import datetime

    # まずは既存のログを読み込み
    existDataStruct = fo.Func_ReadJson2Dict(logFilePath)
    newDataArray = existDataStruct.get('log',[])

    # 既存データに今回データを追加
    newDataArray.append(accessLogDataList)

    # 念のために新しい順に並べ替え
    return sorted(newDataArray, key=lambda x: datetime.strptime(x['accessEndTime'], cf.ACCESSDATETIME_FORMAT), reverse=True)    

def saveAccessLog2File(groupName, accessLogStruct, path):
    try:
        if groupName == '' or len(cf.g_dicAccessLogLock) == 0:
            fo.Func_WriteDict2Json(path, accessLogStruct)
        else:
            with cf.g_dicAccessLogLock[groupName]:
                # 書き込み
                fo.Func_WriteDict2Json(path, accessLogStruct)

        return True
    except Exception as e:
        location = Trace.execution_location()
        Logging(groupName, f'【Location】{location}【ExceptionMsg】{str(e.args)}:サイトごとのアクセスログの保存に失敗')

        return False

def readAccessLog(groupName, path):
    ret = []
    try:
        with cf.g_dicAccessLogLock[groupName]:
            # まずは既存のログを読み込み
            existData = fo.Func_ReadJson2Dict(path)
            ret = existData.get('log',[])
    except Exception as e:
        location = Trace.execution_location()
        Logging(groupName, f'【Location】{location}【ExceptionMsg】{str(e.args)}:サイトごとのアクセスログの保存に失敗')

    return ret

def readAccessLogStruct(groupName, path):
    ret = ''
    try:
        # groupNameがない場合はメインプロセスしか読み書きしないファイルなのでロックいらない
        if groupName == '' or len(cf.g_dicAccessLogLock) == 0:
            ret = fo.Func_ReadJson2Dict(path)
        else:
            with cf.g_dicAccessLogLock[groupName]:
                # まずは既存のログを読み込み
                ret = fo.Func_ReadJson2Dict(path)

    except Exception as e:
        location = Trace.execution_location()
        Logging('MainProc', f'【Location】{location}【ExceptionMsg】{str(e.args)}:サイトごとのアクセスログの保存に失敗')

    return ret

def getAccessLogPath(groupName, extraName = '', extraSubDir = ''):
    subDir = groupName
    if extraSubDir != '':
        subDir = extraSubDir

    ret = os.path.join(os.path.join(cf.PATH_LOG_DIR, subDir), f'{groupName}_Access.log')

    if extraName != '':
        ret = os.path.join(os.path.join(cf.PATH_LOG_DIR, subDir), f'{groupName}_Access_{extraName}.log')
    return ret

def getAccessLogConfigPath(groupName, extraSubDir = ''):
    subDir = groupName

    if extraSubDir != '':
        subDir = extraSubDir
    return os.path.join(os.path.join(cf.PATH_LOG_DIR, subDir), f'{groupName}_Access.Config')

def getHtmlStatus(retCode):
    ret = ''
    if retCode & cf.SUB_RETURNCODE_DIFF_INDIVISUAL:
        ret = "HTML取得成功 差分あり(個別対応)"
    elif retCode & cf.SUB_RETURNCODE_DIFF:
        ret = "HTML取得成功 差分あり"
    elif retCode & cf.SUB_RETURNCODE_NODIFF_INDIVISUAL:
        ret = "HTML取得成功 差分なし(個別対応)"
    elif retCode & cf.SUB_RETURNCODE_NODIFF:
        ret = "HTML取得成功 差分なし"
    elif retCode & cf.SUB_RETURNCODE_GETHTML_FAILED:
        ret = "HTML取得失敗"
    elif retCode == cf.SUB_RETURNCODE_ERR:
        ret = "何らかのエラーのためHTML取得処理に到達できませんでした"
    elif retCode & cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_SUCCESS:
        ret = "HTML取得成功 (個別取得成功)"
    elif retCode & cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED:
        ret = "HTML取得成功 (個別取得失敗)"
    elif retCode & cf.SUB_RETURNCODE_GETHTML:
        ret = "HTML取得成功"

    return ret