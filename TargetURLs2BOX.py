#Windows標準のタスクマネージャーにて自動実行→バッチでもいいけど
import os
import shutil
import datetime
import json
import base64
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from deepdiff import DeepDiff  # 差分検出用ライブラリ

# --- Box API 関連 ---
from boxsdk import JWTAuth, Client

# --- Gmail API 関連 ---
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# --- 自前 ---
from Config import Config as cf

# -------------------------------
# 設定（各自環境に合わせて変更）
# -------------------------------
# ローカルの設定
CONFIG_DIR = 'E:\MonitorSystem\Source\OnionScraperV2\Config'
TARGET_JSON_FILE = os.path.join(CONFIG_DIR, 'TargetURL.json' )  # アップロード対象ファイル
LOCAL_BACKUP_DIR = os.path.join(CONFIG_DIR, 'BackUpTargetURL' ) # バックアップ用フォルダ（存在しなければ作成）
MAX_LOCAL_FILES = 10                                            # ローカルバックアップ最大保存数

# Box の設定
BOX_CONFIG_FILE = os.path.join(CONFIG_DIR, 'Box_config.json' )  # Box SDK 用JWT認証設定ファイル（Box Developer Consoleで取得）
MAX_BOX_FILES = 10                             # Boxアップロード先フォルダ内最大保存数
# アップロード先はルート直下に作成する「TargetURLs」フォルダを使用
TARGET_BOX_FOLDER_NAME = 'TargetURLs'
TARGET_BOX_SHARE_EMAIL = cf.SENDTO_REPORT
send_address = cf.SENDTO_REPORT
# send_address = cf.SENDTO_REPORT_YUICHI

# Gmail の設定
EMAIL_SUBJECT = '監視URLリストが更新されました (MBSD リークサイトモニター3)'
# Gmail APIの認証情報は token.json などで管理する前提（詳しくはGoogle APIのチュートリアル参照）
GMAIL_CREDENTIALS_FILE = 'gmail_credentials.json'  # 認証情報ファイルのパス（OAuth2クライアント情報）

# -------------------------------
# 関数定義
# -------------------------------

def ensure_local_backup_dir():
    """バックアップ用ローカルフォルダが存在しなければ作成"""
    if not os.path.exists(LOCAL_BACKUP_DIR):
        os.makedirs(LOCAL_BACKUP_DIR)

def backup_file():
    """
    TARGET_JSON_FILE をバックアップフォルダに日時付きでコピーする。
    戻り値は新規バックアップファイルのパス
    """
    ensure_local_backup_dir()
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    backup_filename = f"TargetURL_{now_str}.json"
    backup_filepath = os.path.join(LOCAL_BACKUP_DIR, backup_filename)
    shutil.copy2(TARGET_JSON_FILE, backup_filepath)
    print(f"バックアップファイルを作成しました: {backup_filepath}")
    return backup_filepath

def cleanup_local_backups():
    """
    ローカルバックアップフォルダ内のファイルが MAX_LOCAL_FILES を超えた場合、
    一番古いファイルを削除して、最大保存数を維持する。
    """
    files = [os.path.join(LOCAL_BACKUP_DIR, f) for f in os.listdir(LOCAL_BACKUP_DIR) if f.endswith('.json')]
    files.sort(key=lambda x: os.path.getmtime(x))
    while len(files) > MAX_LOCAL_FILES:
        file_to_delete = files.pop(0)
        os.remove(file_to_delete)
        print(f"古いローカルバックアップファイルを削除しました: {file_to_delete}")

def get_previous_backup(current_backup):
    """
    現在のバックアップファイル以外の中で最新のファイルパスを返す。
    なければ None を返す。
    """
    files = [os.path.join(LOCAL_BACKUP_DIR, f) for f in os.listdir(LOCAL_BACKUP_DIR)
             if f.endswith('.json') and os.path.join(LOCAL_BACKUP_DIR, f) != current_backup]
    if not files:
        return None
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[0]

def compare_json_files(new_file, previous_file):
    """
    2つのJSONファイルを比較し、変更点を HTML で整形して返す。
    ステータス（新規／削除／更新）、更新されたキー、更新されたURL（もしくは削除されたURL）を記載します。
    """
    import json, re
    with open(new_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)
    with open(previous_file, 'r', encoding='utf-8') as f:
        prev_data = json.load(f)
    
    from deepdiff import DeepDiff
    diff = DeepDiff(prev_data, new_data, ignore_order=True)
    if not diff:
        return ''

    # 補助関数: diffパスからキーを抽出
    def extract_key(diff_path, isLast = False):
        import re
        matches = re.findall(r"\['([^']+)'\]", diff_path)
        if matches:
            if isLast:
                return matches[-1] 
            return matches[0]
        return diff_path
    
    # 補助関数: diffパスに沿って値を取得する
    def get_value_by_diff_path(data):
        ret = []
        url = data.get('url', '')
        urlList = data.get('urlList', '')

        if url:
            ret.append(url)
        if urlList:
            ret.extend(urlList)

        return ret

    html_content = """<html>
  <head>
    <meta charset="UTF-8">
    <style>
      body { font-family: Arial, sans-serif; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
      th { background-color: #f2f2f2; }
      .new { background-color: #d4edda; }
      .update { background-color: #fff3cd; }
      .delete { background-color: #f8d7da; }
    </style>
  </head>
  <body>
    <h2>アップロードJSONファイルの差分</h2>
    <table>
      <tr>
        <th>ステータス</th>
        <th>キー</th>
        <th>URL</th>
      </tr>
    """

    # 新規追加された項目
    if 'dictionary_item_added' in diff:
        for diff_path in diff['dictionary_item_added']:
            key_extracted = extract_key(diff_path)
            new_value = get_value_by_diff_path(new_data[key_extracted])
            if isinstance(new_value, list):
                new_value_str = "<br>".join(new_value)
            elif isinstance(new_value, dict):
                new_value_str = json.dumps(new_value, ensure_ascii=False)
            else:
                new_value_str = str(new_value)
            html_content += f"""<tr class="new">
        <td>新規</td>
        <td>{key_extracted}</td>
        <td>{new_value_str}</td>
      </tr>"""

    # 削除された項目
    if 'dictionary_item_removed' in diff:
        for diff_path in diff['dictionary_item_removed']:
            key_extracted = extract_key(diff_path)
            old_value = get_value_by_diff_path(prev_data[key_extracted])
            if isinstance(old_value, list):
                old_value_str = "<br>".join(old_value)
            elif isinstance(old_value, dict):
                old_value_str = json.dumps(old_value, ensure_ascii=False)
            else:
                old_value_str = str(old_value)
            html_content += f"""<tr class="delete">
        <td>削除(更新含む)</td>
        <td>{key_extracted}</td>
        <td>{old_value_str}</td>
      </tr>"""

    # 更新（値が変化した）項目
    if 'values_changed' in diff:
        for diff_path, change in diff['values_changed'].items():
            key_extracted = extract_key(diff_path, True)
            old_val = change.get('old_value')
            new_val = change.get('new_value')
            if isinstance(old_val, list):
                old_val = ", ".join(old_val)
            elif isinstance(old_val, dict):
                old_val = json.dumps(old_val, ensure_ascii=False)
            if isinstance(new_val, list):
                new_val = ", ".join(new_val)
            elif isinstance(new_val, dict):
                new_val = json.dumps(new_val, ensure_ascii=False)
            html_content += f"""<tr class="update">
        <td>更新</td>
        <td>{key_extracted}</td>
        <td>旧: {old_val}<br>新: {new_val}</td>
      </tr>"""
    
    html_content += "</table></body></html>"
    return html_content


def get_box_client():
    """
    BoxのJWT認証設定ファイルを使用して Box Client を生成する。
    ※事前に Box Developer Console にて設定が必要
    """
    auth = JWTAuth.from_settings_file(BOX_CONFIG_FILE)
    access_token = auth.authenticate_instance()  # トークン取得
    client = Client(auth)
    return client

def get_target_box_folder(client, folder_name, shareUserList=None):
    """
    ルートフォルダ('0')以下に指定した名前のフォルダが存在するかチェックし、
    存在しなければ作成する。さらに、share_with_email が指定されていれば
    そのユーザーとコラボレーション（閲覧権限）を設定する。
    """
    root_folder = client.folder(folder_id='0')
    items = root_folder.get_items(limit=100, offset=0)
    target_folder = None
    for item in items:
        if item.type == 'folder' and item.name == folder_name:
            target_folder = item
            break
    if target_folder is None:
        target_folder = root_folder.create_subfolder(folder_name)
        print(f"フォルダ '{folder_name}' を作成しました。ID: {target_folder.id}")
    else:
        print(f"既存のフォルダ '{folder_name}' を使用します。ID: {target_folder.id}")

    # コラボレーションの設定（既に設定済みの場合はエラーが出る可能性があります）
    if shareUserList:
        try:
            for userMailAddr in shareUserList:
                # ※role は 'viewer'（閲覧のみ）や 'editor'（編集可能）を指定可能です
                target_folder.add_collaborator(userMailAddr, 'viewer')
                print(f"フォルダ '{folder_name}' を {userMailAddr} と共有しました。")
        except Exception as e:
            print(f"コラボレーション設定時のエラー: {e}")
    return target_folder

def upload_to_box(file_path, client, target_folder):
    uploaded_file = ''
    file_shared_link = ''
    folder_shared_link = ''

    try:
        import os
        filename = os.path.basename(file_path)
        uploaded_file = target_folder.upload(file_path, file_name=filename)
        print(f"Boxへアップロード完了: {filename}")
        
        # ファイルの共有リンクを作成（編集不可のリンク）
        file_shared_link = uploaded_file.get_shared_link(access='open')
        # フォルダの共有リンクを取得または作成
        folder_shared_link = client.folder(target_folder.id).get_shared_link(access='open', allow_download=True)

    except Exception as e:
        print(f"アップロード時のエラー: {e}")
            
    return uploaded_file, file_shared_link, folder_shared_link


def cleanup_box_files(target_folder):
    try:
        """
        指定フォルダ内のファイルが MAX_BOX_FILES を超えていた場合、
        一番古いファイルを削除して、最大保存数を維持する。
        """
        items = target_folder.get_items(limit=100, offset=0, fields=['modified_at'])
        files = [item for item in items if item.type == 'file']
        files.sort(key=lambda x: x.modified_at)
        while len(files) > MAX_BOX_FILES:
            file_to_delete = files.pop(0)
            file_to_delete.delete()
    except Exception as e:
        print(f"BOXファイル削除時のエラー: {e}")

def get_gmail_service():
    """
    Gmail APIの認証情報を使用してサービスオブジェクトを生成する。
    事前に OAuth2 認証（token.jsonなど）を実施しておく必要があります。
    """
    # token.json や credentials.json から認証情報をロードする例
    # 下記はシンプルな例です。実際には認証フローに沿ってトークンを取得してください。
    creds = Credentials.from_authorized_user_file(GMAIL_CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/gmail.send"])
    service = build('gmail', 'v1', credentials=creds)
    return service

def send_notification_email(gmail_service, sender, to, subject, html_body):
    """
    Gmail API を使用して通知メールを送信する。
    """
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = to
    part = MIMEText(html_body, 'html')
    message.attach(part)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_message = gmail_service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
    print(f"メール送信完了。Message Id: {send_message.get('id')}")

stmp_user_v4 = 'iroiromonitaro1v2.system@gmail.com'
stmp_password_v4 = 'koor cwrh bxhi gqdp'

def sendMail_google(subject, htmlBody):
    try:
        isSuccess = False
        stmp_server = "smtp.gmail.com"
        stmp_port = 587
        from_address = stmp_user_v4

        msg = MIMEMultipart('related')
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = from_address

        msg.attach(MIMEText(htmlBody, "html"))

        s = smtplib.SMTP(stmp_server, stmp_port)
        s.starttls()
        retLogtin = s.login(stmp_user_v4, stmp_password_v4)
        retSend = s.sendmail(from_address, send_address, msg.as_string())
        s.quit()

        isSuccess = True
    except Exception as e:
        print({str(e)})

    return isSuccess


def main():
    # --- 1. ローカルの TargetURL.json を日時付きでバックアップ ---
    current_backup = backup_file()
    previous_backup = get_previous_backup(current_backup)
    
    # --- 2. 直前のバックアップと比較し、差分HTMLを生成 ---
    try:
        diff_html = ""
        if previous_backup:
            diff_html = compare_json_files(current_backup, previous_backup)
        else:
            diff_html = "<html><body><p>初回アップロードのため差分はありません。</p></body></html>"
        
        if diff_html == '':
            return
    except Exception as e:
        print(str(e))
       
    # --- 3. Box にアップロード ---
    client = get_box_client()
    # ルート以下に「TargetURLs」フォルダを取得（または作成）し、指定ユーザーと共有
    target_folder = get_target_box_folder(client, TARGET_BOX_FOLDER_NAME, TARGET_BOX_SHARE_EMAIL)
    uploaded_file, file_shared_link, folder_shared_link = upload_to_box(current_backup, client, target_folder)

    # --- 4. 通知メールの本文を作成 ---
    # ※メール本文内に、差分HTMLとBox上の共有リンクを記載します
    email_body = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
        body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f0f2f5;
        margin: 0;
        padding: 20px;
        }}
        .container {{
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
        padding: 20px;
        background: #ffffff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-radius: 8px;
        }}
        h2 {{
        color: #333;
        margin-top: 0;
        }}
        .link-section {{
        margin: 20px 0;
        }}
        .link-section p {{
        margin: 10px 0;
        font-size: 16px;
        }}
        .link-section a {{
        color: #1a73e8;
        text-decoration: none;
        word-break: break-all;
        }}
        .diff-section {{
        margin-top: 30px;
        }}
        .diff-section h3 {{
        border-bottom: 2px solid #eee;
        padding-bottom: 10px;
        color: #444;
        }}
        table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        }}
        th, td {{
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
        }}
        th {{
        background-color: #4CAF50;
        color: white;
        }}
        tr:nth-child(even) {{
        background-color: #f9f9f9;
        }}
    </style>
    </head>
    <body>
    <div class="container">
        <h2>Boxへのファイルアップロードが完了しました</h2>
        <p>アップロードされたファイル: <strong>{os.path.basename(current_backup)}</strong></p>
        <div class="link-section">
        <p>Box上のファイルURL: <a href="{file_shared_link}" target="_blank">{file_shared_link}</a></p>
        <p>アップロード先フォルダURL: <a href="{folder_shared_link}" target="_blank">{folder_shared_link}</a></p>
        </div>
        <div class="diff-section">
        <h3>前回との差分</h3>
        {diff_html}
        </div>
    </div>
    </body>
    </html>
    """

    # --- 5. Gmail API を使用して通知メールを送信 ---
    sendMail_google(EMAIL_SUBJECT, email_body)

    # --- 6. ローカルおよびBOXに保管されたファイルの古いものを削除 ---
    cleanup_local_backups()
    cleanup_box_files(target_folder)

if __name__ == '__main__':
    main()
