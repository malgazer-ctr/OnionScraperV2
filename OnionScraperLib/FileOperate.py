import csv
import sys #sys._getframe().f_code.co_name
from csv import reader
import os
import shutil
import datetime
import time
import json
from pathlib import Path


def Func_DeleteFile(filePath):
    try:    
        if Func_IsFileExist(filePath):
            if os.path.isfile(filePath):
                os.remove(filePath)
    except Exception as e:
        # print(sys._getframe().f_code.co_name+":\n"+e)
        # Conrig.pyが循環参照になるからちょっと保留
        # Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        print(sys.exc_info())

""" def Func_CSVWriteList(filePath, targetList, option="w"):
    try:
        with open(filePath, option, encoding='shift_jis') as f:
            writer = csv.writer(f, lineterminator="\n") # writerオブジェクトの作成 改行記号で行を区切る
            writer.writerows(targetList) 
    except Exception as e:
        # print(sys._getframe().f_code.co_name+":\n"+e)
        print(sys.exc_info()) """

def Func_CSVWriteList(filePath, targetList, option="w"):
    try:
        with open(filePath, option, encoding='utf-8') as f:
            writer = csv.writer(f, lineterminator="\n") # writerオブジェクトの作成 改行記号で行を区切る
            writer.writerows(targetList) 
    except Exception as e:
        # print(sys._getframe().f_code.co_name+":\n"+e)
        # Conrig.pyが循環参照になるからちょっと保留
        # Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        print(sys.exc_info())
        
def Func_CSVReadist(filePath, option='r'):
    ret = []
    try:
        if os.path.isfile(filePath) != False:
            with open(filePath, option, encoding='utf-8') as csv_file:
                csv_reader = reader(csv_file)
                # Passing the cav_reader object to list() to get a list of lists
                ret = list(csv_reader)
    except Exception as e:
        # Conrig.pyが循環参照になるからちょっと保留
        # Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        print(sys.exc_info())

    return ret

def Func_WriteDict2Json(filePath, targetDict, option="w"):
    try:
        with open(filePath, mode="w", encoding='utf-8') as json_file:
            json.dump(targetDict, json_file, indent=2, ensure_ascii=False)
    except Exception as e:
        print(sys.exc_info())

def Func_ReadJson2Dict(filePath, option='r'):
    json_dict = {}

    try:    
        if os.path.isfile(filePath) != False:
            with open(filePath, option, encoding='utf-8') as json_file:
                #辞書型で読み込む
                json_dict = json.load(json_file) 
    except Exception as e:
        print(sys.exc_info())
        
    return json_dict

def Func_IsFileExist(filePath):
    return os.path.exists(filePath)

def Func_IsDirectoryExist(dirPath):
    return os.path.isdir(dirPath)

def Func_DeleteFile(filePath):
    if os.path.exists(filePath):
        os.remove(filePath)

def Func_CopyFile(srcFile, dstFFile):
    if os.path.exists(srcFile):
        shutil.copy2(srcFile, dstFFile)

def Func_GetFileSize(filePath):
    ret = 0
    if os.path.exists(filePath):
        ret = os.path.getsize(filePath)

    return ret
    
def Func_RenameFile(filePath, newFilePath, force = False):
    if os.path.exists(filePath) == True:
        if force == True and os.path.exists(newFilePath) == True:
            os.remove(newFilePath)

        os.rename(filePath, newFilePath)
   
# エラー時リトライするバージョン
def Func_RenameFileEx(filePath, newFilePath, maxRetry = 20, force = True):
    # 元ファイルが存在しているか
    if os.path.exists(filePath) == True:
        i = 1
        isAllowRename = True

        # 先ファイルが存在する場合強制リネーム可否のフラグチェック 
        if os.path.exists(newFilePath) == True:
            isAllowRename = force

        if isAllowRename == True:
            # 元ファイルが存在し続けている間maxRetryカウントまでリトライ
            for i in range(maxRetry):
                if os.path.exists(newFilePath) == True:
                    time.sleep(1)
                    Func_DeleteFile(newFilePath)
                else:
                    break
                
            os.rename(filePath, newFilePath)


#本プログラムと同階層にバックアップ保管用フォルダを作成してバックアップ
def Func_CreateBackup(filePath):
    new_path = "ResultBackup"#フォルダ名
    
    if not os.path.exists(new_path):#ディレクトリがなかったら
        os.mkdir(new_path)#作成したいフォルダ名を作成

    shutil.copy2(filePath, new_path+'\Result_'+datetime.datetime.now().strftime('%Y%m%d_%H%M')+'.csv')

def Func_CreateBackupPrev(filePath, filePathBackup):
    new_path = "ResultBackup"#フォルダ名
    
    #既存ならリネームしておく
    if os.path.isfile(filePathBackup) == True:
        fileName = Path(filePathBackup).stem

        os.rename(filePathBackup, fileName + '_' + datetime.datetime.now().strftime('%Y%m%d_%H%M')+'.csv')

    shutil.copy2(filePath, filePathBackup)

def Func_WiteFile(path, data, option = 'w+'):
    # ファイルを読み書き両用でオープン
    with open(path, option, encoding='UTF-8') as f:
        # ファイル先頭から書き込み
        f.write(data) 
        # ファイル先頭にファイルポインタを移動
        f.seek(0)

def Func_ReadFile(path, option = 'r', encoding_ = 'UTF-8'):
    ret = ''

    # ファイルを読み専でオープン
    with open(path, option, encoding=encoding_) as f:
        ret = f.read() 

    return ret

def Func_CreateDirectry(path):

    if os.path.exists(path) == False:
        os.makedirs(path)

def Func_removeAllFiles(path):

    if os.path.exists(path) == True:
        shutil.rmtree(path)
    
    os.mkdir(path)

def Func_GetFileUpdateTime(path, formatStr = '%Y/%m/%d %H:%M:%S'):
    time_ = time.localtime(os.path.getmtime(path))

    if formatStr == '':
        ret = time_
    else:
        ret = time.strftime(formatStr, time_)
        
    return ret



def clean_temp_folder(path = os.path.expandvars(r'%LOCALAPPDATA%\Temp'), only_scoped_dir=True, hours=6, max_retries=3):
    import os
    import shutil
    import time
    from datetime import datetime, timedelta 

    """
    Clean temporary folders and files in the specified path.
    
    :param path: Path to the temp folder
    :param only_scoped_dir: If True, only delete folders starting with 'scoped_dir'
    :param hours: Number of hours old the folder/file should be to be deleted
    :param max_retries: Maximum number of retries for deletion
    """
    current_time = datetime.now()
    
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        
        # Check if the item is old enough
        creation_time = datetime.fromtimestamp(os.path.getctime(item_path))
        if current_time - creation_time < timedelta(hours=hours):
            continue
        
        # Check if we should delete this item
        if only_scoped_dir and (not item.startswith('scoped_dir') or not os.path.isdir(item_path)):
            continue
        
        # Try to delete the item
        for _ in range(max_retries):
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)

                    test = 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                print(f"Deleted: {item_path}")
                break
            except Exception as e:
                print(f"Failed to delete {item_path}: {str(e)}")
                time.sleep(1)  # Wait for 1 second before retrying
        else:
            print(f"Skipped after {max_retries} failed attempts: {item_path}")
