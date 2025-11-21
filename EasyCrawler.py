import re
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import difflib
import os

notificationMailTemplate = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html><head>\
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><title></title></head\>\
        <body>Web page changed:</br>-------------------------------------------</br>{}</br></br>\
        {}\
        </body>'

MAIL_ADDRESS_LIST_YUICHI = [
    'y.yasuda@mbsd.jp'
]
MAIL_ADDRESS_LIST_CIG = [
    'y.yasuda@mbsd.jp',
    'takashi.yoshikawa.el@d.mbsd.jp',
    'm.fukuda@mbsd.jp'
]

MAIL_ADDRESS_LIST_NIDEC = [
    'y.yasuda@mbsd.jp',
    'takashi.yoshikawa.el@d.mbsd.jp',
    'm.fukuda@mbsd.jp',
    'ds-nid@mbsd.jp'
]

# 設定
# urls = ['https://example.com', 'https://anotherexample.com']
urls = [
    {
        'displayName':'NIDEC_FILELEAK',
        'url':'https://gofile.io/d/6hm16f',
        'mailto':MAIL_ADDRESS_LIST_NIDEC,
        'mailSubject':'NIDEC_FILELEAK(the page of gofile.io):Change Detection',
        'extraBodyEndText':'-----</br>\
                            ※ これはgofileのNIDEC個別ページ (https[://]gofile.io/d/6hm16f) を定期監視しているメールです。</br>\
                            ※ ファイルの追記や何か変化があった場合はCIGへご連絡いただきダウンロードなどはお控えください。</br>\
                            -----'
    }
]

exceptWords = [
    {
        'group':'NIDEC_FILELEAK',
        'word':'loading',
        'regexp':False
    }
]

wait_time = 600  # 10分
storage_dir = r'E:\MonitorSystem\Source\OnionScraperV2\Data\EasyCrawler'

# ストレージディレクトリを作成
if not os.path.exists(storage_dir):
    os.makedirs(storage_dir)

# ヘッドレスChromeの設定
def createChromeDriver():
    try:
        options = Options()
        # options.headless = True
        options.add_argument('--headless')
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
    
    except Exception as e:
        send_email(f'{str(e)}', f'{displayName}:Error Detection', sendTo=MAIL_ADDRESS_LIST_YUICHI)
        return None

    return  webdriver.Chrome(options=options)

def is_html_tag(string):
    # 簡単なHTMLタグの正規表現
    pattern = re.compile(r'<[^>]+>')
    return bool(pattern.match(string))

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
                            if is_html_tag(child.string.strip()) == False:
                                direct_text.append(child.string.strip())
                        else:
                            direct_text.extend(get_direct_text(child))
                    elif isinstance(child, str):
                        if is_html_tag(child.strip()) == False:
                            direct_text.append(child.strip())
                return direct_text

            retArray = get_direct_text(elem)

    except Exception as e:
        send_email(f'{groupName}:getTextAll Error 1', f'{displayName}:Error Detection', sendTo=MAIL_ADDRESS_LIST_YUICHI)

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
            send_email(f'{groupName}:getTextAll Error 2', f'{displayName}:Error Detection', sendTo=MAIL_ADDRESS_LIST_YUICHI)
            retArray = []
            retText = ''

    return retText

def isIgnoreData(displayName, text):

    ret = False
    textTemp = text.lower()

    for item in exceptWords:
        word = item['word'].lower()
        usgroupName  = item.get('group', False)
        useRegExp = item.get('regexp', False)

        if usgroupName and usgroupName != displayName:
            continue
            
        if useRegExp == False:
            if word in textTemp:
                send_email(f'[{word}]の条件にマッチしたので取得テキストをすべて無視。取得失敗として扱う。', 'CIG EasyCrawler', sendTo = MAIL_ADDRESS_LIST_YUICHI)
                ret = True

    return ret

def fetch_html(displayName, url):
    ret = ''
    driver = None
    try:
        driver = createChromeDriver()
        if driver:
            driver.set_page_load_timeout(30)
            driver.get(url)

            time.sleep(5)  # ページの完全な読み込みを待機

            if displayName == 'NIDEC_FILELEAK':
                ret = html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')       

                if soup:
                    elem = soup.find(id = 'main')
                    ret = getTextAll(displayName, elem)

                    # 無視対象なら空を返してリトライ
                    if isIgnoreData(displayName, ret):
                        ret = ''
            else:
                ret = html

    except TimeoutException:
        send_email(f'Timeout Error accessing\n\nThe page took too long to load and was aborted.', f'{displayName}:Error Detection', sendTo=MAIL_ADDRESS_LIST_YUICHI)
        return None
    except WebDriverException as e:
        send_email(f'WebDriverException Error accessing\n\nThe page took too long to load and was aborted.', f'{displayName}:Error Detection', sendTo=MAIL_ADDRESS_LIST_YUICHI)
        return None
    finally:
        if driver:
            driver.quit()

    return ret

import traceback

def setDiffColorForMail(diffPlaneTxt):
    try:
        ret = ''
        # 改行コードを<br>に変更しつつ+は緑に、-は赤に変更するタグをつける
        if len(diffPlaneTxt) > 0:
            temp = diffPlaneTxt.splitlines()

            diffPlaneTxtArray = []
            diffPlaneTxt = ''
            for i in temp:
                diffPlaneTxtTmp = ''
                diffPlaneTxtTmp2 = ''
                if i.startswith('+') == True:
                    diffPlaneTxtTmp = '<span style="color:green">{}</span><br>'.format(i)

                    # 削除差分のみに重要ワードがある場合はメールに重要フラグ立てたくない
                    # diffPlaneTxtTmp2 = diffPlaneTxtTmp
                    # diffPlaneTxtTmp = setHighLightImportantWord(diffPlaneTxtTmp, importantWordsReplaceList+importantWordsReplaceList_jp)
                    # if diffPlaneTxtTmp != diffPlaneTxtTmp2:
                    #     isImportantMail = True

                    diffPlaneTxtArray.append(diffPlaneTxtTmp)
                elif i.startswith('-') == True:
                    diffPlaneTxtTmp = '<span style="color:red">{}</span><br>'.format(i)

                    # 削除差分のみに重要ワードがある場合はメールに重要フラグ立てたくない
                    # diffPlaneTxtTmp2 = diffPlaneTxtTmp
                    # diffPlaneTxtTmp = setHighLightImportantWord(diffPlaneTxtTmp, importantWordsReplaceList+importantWordsReplaceList_jp)
                    # if diffPlaneTxtTmp != diffPlaneTxtTmp2:
                    #     retIsNoImportantMail = True

                    diffPlaneTxtArray.append(diffPlaneTxtTmp)
                else:
                    if i != '':
                        diffPlaneTxt += i
            
            ret = '\n'.join(diffPlaneTxtArray)

            # # 削除差分のみに重要ワードがある場合はメールに重要フラグ立てたくない
            # if isImportantMail:
            #     retIsNoImportantMail = False

    except Exception as e:
        send_email(f'{str(e)}', f'{displayName}:Error Detection', sendTo=MAIL_ADDRESS_LIST_YUICHI)
        print("An error occurred:", e)
        traceback.print_exc()

    return ret

def send_email(bodyText, subject, sendTo = MAIL_ADDRESS_LIST_CIG, isUrgent = True):
    retSuccess = False
    try:
        stmp_server = "smtp.gmail.com"
        stmp_port = 587
        stmp_user = 'iroiromonitaro1v2@gmail.com'
        stmp_password = 'drjvrclblfhzqxde'        
        from_address = stmp_user
        send_address = sendTo

        msg = MIMEMultipart('related')
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = from_address

        # body = f'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
        #         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\
        #         <html>\
        #             <body>{bodyText}</body>\
        #         </html>'
        body = bodyText

        msg.attach(MIMEText(body, "html"))

        # 重要メール
        if isUrgent:
            msg["X-Priority"] = '1'

        s = smtplib.SMTP(stmp_server, stmp_port)
        s.starttls()
        retLogtin = s.login(stmp_user, stmp_password)
        retSend = s.sendmail(from_address, send_address, msg.as_string())
        s.quit()
        retSuccess = True

    except Exception as e:
        retSuccess = False
        # Log.LoggingWithFormat('SendReportError', logCategory = 'E', logtext = {str(e)})
        print("An error occurred:", e)
        traceback.print_exc()
    return retSuccess

def save_html(content, filepath):
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)

def read_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def defungURL(str):
    ret = ''

    if len(str) > 0:
        retTmp = str.replace("http","hxxp").replace("://","[://]")
        ret = re.sub('\.([a-zA-Z])', '[.]\\1', retTmp)

    return ret

def diff_Differ(before, after):
    ret = ""
    
    try:
        # file1 = open(before, encoding="utf-8")
        # file2 = open(after, encoding="utf-8")

        # lines_file1 = file1.readlines()
        # lines_file2 = file2.readlines()

        lines_file1 = before.splitlines()
        lines_file2 = after.splitlines()
    
        diff = difflib.Differ()

        chkStr = ''
        for elem1,elem2 in zip(lines_file1,lines_file2):
            # 一文字ずつ差分を確認。数字だけの差分行は無視する
            for i,s in enumerate(difflib.ndiff(elem1,elem2)):
                if s[0]==' ': continue
                elif s[0]=='-':
                    chkStr += s[-1]
                    # print(u'Delete "{}" from position {}'.format(s[-1],i))
                elif s[0]=='+':
                    chkStr += s[-1]
                    # print(u'Add "{}" to position {}'.format(s[-1],i))    
            
        isIgnoreDiff = False
        # 差分が数字だけなら無視
        if re.match(r"^\d+$", chkStr):
            isIgnoreDiff = True
        # 適当だけど500文字以上あってスペースないのは文章でも単語でもなさそうなのでむし
        # IMGのBase64データとか
        # elif len(chkStr) >= 500 and chkStr.find(' ') < 0:
        #     isIgnoreDiff = True

        if isIgnoreDiff == False:
            diff_ = diff.compare(lines_file1, lines_file2)

            # 差分のみにする
            retTmp = []
            for data in diff_ :
                if data[0:1] in ['+', '-'] :
                    if data != '+ ' and data != '- ':
                        
                        data = defungURL(data)
                        retTmp.append(data)

            ret = '\n'.join(retTmp)

        # file1.close()
        # file2.close()

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()

    return ret
  
# メインループ
try:
    while True:
        for item in urls:
            displayName = item['displayName']
            url = item['url']
            mailto = item['mailto']
            extraText = item.get('extraBodyEndText', '')

            for retryCnt in range(3):
                html = fetch_html(displayName, url)
                if html:
                    break
                
            if html:
                filename = os.path.join(storage_dir, f"{displayName}.html")
                
                old_html = ''
                if os.path.exists(filename):
                    old_html = read_html(filename)

                if old_html != html:
                    diff_text = diff_Differ(old_html, html)
                    if diff_text:
                        colored_diff_text = setDiffColorForMail(diff_text)
                        mailBody = notificationMailTemplate.format(colored_diff_text, extraText)

                        subject = item.get('mailSubject', f'{displayName}:Change Detection')
                        send_email(mailBody, subject, sendTo = mailto)
                
                    save_html(html, filename)
            else:
                send_email(f'fetch_htmlのリトライ三回失敗', 'CIG EasyCrawler', sendTo = MAIL_ADDRESS_LIST_YUICHI)

            j = 0
            for i in range(wait_time):
                time.sleep(1)
                j += 1

                if j == 30:
                    print(f'待機中:前回実行サイト{displayName}')
                    j = 0
            
            print("私は生きています")
            
except Exception as e:
    send_email(f'プログラム終了(Exception):{str(e)}', 'CIG EasyCrawler', sendTo = MAIL_ADDRESS_LIST_YUICHI)
finally:
    send_email('プログラム終了(finally)', 'CIG EasyCrawler', sendTo = MAIL_ADDRESS_LIST_YUICHI)
    print("Script execution finished")
