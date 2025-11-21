import os
from datetime import datetime, timedelta
import pytz
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import Log
from OnionScraperLib import utilFuncs as uf
from Config import Config as cf

from boxsdk import JWTAuth
from boxsdk import Client

configFile = r'E:\MonitorSystem\Source\OnionScraperV2\Config\Box_config.json'

def upload2BOX(groupName, file = ''):
    ret = False
    retURL = ''

    try:
        # deleteFromBOX()

        if fo.Func_IsFileExist(file):
            auth = JWTAuth.from_settings_file(settings_file_sys_path = configFile)
            client = Client(auth)

            root_folder = client.root_folder().get()

            # ルートはアクセス拒否
            # BOX_addCollaborator(groupName, client, root_folder.id, 'y.yasuda@mbsd.jp', role = 'editor')

            file_name = os.path.basename(file)
            stream = open(file, 'rb')

            uploadItem = client.folder(root_folder.id).upload_stream(stream, file_name)

            retURL = client.file(uploadItem.id).get_shared_link_download_url()
            ret = True
        else:
            retURL = 'アップロードの対象ファイルが存在しません'
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

    if ret == False:
        retURL = 'アップロード失敗'

    return ret, retURL

# ----------------------------------------------------------------------------------------
# BOX関連（アクセスログのアップロード）
# ----------------------------------------------------------------------------------------
# フォルダ名からフォルダIDを列挙
def BOX_get_folder_id_by_name(client, folder_name, parent_folder_id='0', groupName = 'MainProc'):
    try:
        folder_id = ''
        items = client.folder(folder_id=parent_folder_id).get_items()
        for item in items:
            if item.type == 'folder' and item.name == folder_name:
                # folder_ids.append(item.id)
                folder_id = item.id
                break
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

    return folder_id

# フォルダ作成
def BOX_createBoxFolder(client, parentFolderId, newFolderName, groupName = 'MainProc'):
    new_folderId = ''

    try:
        folderIds = BOX_get_folder_id_by_name(client, newFolderName, parentFolderId, groupName)

        # すでに作成済みならそのIDを返す
        if len(folderIds) == 0:
            new_folder = client.folder(parentFolderId).create_subfolder(newFolderName)
            new_folderId = new_folder.id
        else:
            new_folderId = folderIds
    except Exception as e:
            Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')
    
    return new_folderId

# フォルダの共有リンク取得
def BOX_get_or_create_shared_link(client, folder_id, groupName = 'MainProc'):
    ret = ''
    try:
        ret = client.folder(folder_id).get_shared_link(access='open', allow_download=True)
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')
    
    return ret

# フォルダにコラボレータを追加して閲覧可能にする（CIGのみなので編集権もつける）
def BOX_addCollaborator(groupName, client, folder_id, collaborator_email, role = 'editor'):
    ret = False
    try:
        # コラボレーターを追加
        folder = client.folder(folder_id=folder_id)
        # 戻りは使ってない
        collaboration = folder.add_collaborator(collaborator_email, role, notify = True)
        ret = True
    except Exception as e:
            if e.code == 'user_already_collaborator':
                ret = True
            else:
                Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')
    return ret

def BOX_SetAccessLogStockFolder(groupName):
    logMainFolderId = ''
    shareFolderLink = ''

    try:
        # deleteFromBOX()
        config = JWTAuth.from_settings_file(settings_file_sys_path = configFile)
        client = Client(config)

        logMainFolderId = BOX_createBoxFolder(client, parentFolderId = '0', newFolderName = 'Logs_HTMLDiffDetectSystem')
        shareFolderLink = BOX_get_or_create_shared_link(client, logMainFolderId)

        collaboratorList = ['y.yasuda@mbsd.jp', 'takashi.yoshikawa.el@d.mbsd.jp', 'm.fukuda@mbsd.jp']
        # collaboratorList = ['y.yasuda@mbsd.jp']
        for collaborator in collaboratorList:
            BOX_addCollaborator(groupName, client, logMainFolderId, collaborator_email=collaborator)
        
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

    return logMainFolderId, shareFolderLink

def BOX_UploadAccessLog(file, groupName):
    groupFolderUrl = ''
    fileUrl = ''

    fileName = os.path.basename(file)

    try:
        config = JWTAuth.from_settings_file(settings_file_sys_path = configFile)
        client = Client(config)
        # logMainFolderId, shareFolderLink = BOX_SetAccessLogStockFolder(groupName)

        # 何回もやりたくない重い処理なので再起動までは記憶しておく
        folderId = ''
        if groupName in cf.g_BoxFolderIds.keys():
            folderId = cf.g_BoxFolderIds[groupName]
        else:
            cf.g_BoxFolderIds[groupName] = folderId = BOX_createBoxFolder(client, cf.g_BoxFolderIds['SharedParent'], groupName)

        if folderId != '':
            groupFolderUrl = BOX_get_or_create_shared_link(client, folderId)

            # フォルダ直下のファイル削除　一時的
            # folder = client.folder(folderId).get()
            # items = folder.get_items()
            # for item in items:
            #     if item.object_type == 'file':
            #         ret = item.delete()
            BOX_DeleteLog_InGroupFolder(groupName, client, folderId)

            # グループごとのフォルダに日付フォルダを作成してファイルをアップロード
            dateFolderId = BOX_createBoxFolder(client, folderId, uf.getDateTime('%Y年%m月%d日'))
            BOX_DeleteFile_InGroupFolder(groupName, client, dateFolderId, fileName)

            file_name = os.path.basename(file)
            stream = open(file, 'rb')

            uploadItem = client.folder(dateFolderId).upload_stream(stream, file_name)
            fileUrl = client.file(uploadItem.id).get_shared_link_download_url()
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

    return groupFolderUrl, fileUrl, cf.g_shareFolderLink

def BOX_DeleteFile_InGroupFolder(groupName, client, folderId, fileName):
    try:
        # フォルダ直下のファイル削除　一時的
        folder = client.folder(folderId).get()
        items = folder.get_items()
        for item in items:
            if item.object_type == 'file' and item.name == fileName:
                    item.delete()
                    break

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

def BOX_DeleteLog_InGroupFolder(groupName, client, folderId):
    try:
        # フォルダ直下のファイル削除　一時的
        folder = client.folder(folderId).get()
        items = folder.get_items()
        for item in items:
            if item.object_type == 'folder':
                date_object = datetime.strptime(item.name, '%Y年%m月%d日')
                # 現在の日時との差を計算（日数）
                days_passed = (datetime.now() - date_object).days

                if days_passed > 3:
                    item.delete()

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

def deleteFromBOX(groupName = 'MainProc'):
    try:
        cf.g_deletingFromBox = True

        # JWTAuthオブジェクトを生成
        auth = JWTAuth.from_settings_file(configFile)

        # Clientオブジェクトを生成
        client = Client(auth)

        # フォルダID
        folder_id = '0'  # 適切なフォルダIDに変更してください

        # フォルダオブジェクトを取得
        folder = client.folder(folder_id).get()

        # フォルダ内のアイテム（ファイル）をリストアップ
        items = folder.get_items()

        # 削除したい期間を設定（ここでは90日前）
        # threshold_date = datetime.now() - timedelta(days=90)
        # 無制限にできるまで30にしとく。アップするもの増えて制限すぐくるので
        threshold_date = datetime.now() - timedelta(days=30)
        threshold_date = threshold_date.replace(tzinfo=pytz.utc)

        for item in items:
            itemTmp = item.get()

            if item.object_type == 'file':
                # ファイルの最終更新日を取得
                # '2023-01-09T12:02:57-08:00'
                updated_at = datetime.strptime(itemTmp.created_at, '%Y-%m-%dT%H:%M:%S%z')
                
                # 最終更新日が閾値よりも前であればファイルを削除
                if updated_at < threshold_date:
                    print('Deleting file: {0}'.format(item.name))
                    ret = item.delete()

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = f'e:{str(e)}')

    finally:
        cf.g_deletingFromBox = False
