import datetime
import subprocess
import re
import json
from deep_translator import GoogleTranslator
from PIL import Image

def getDateTime(format = '%Y%m%d', useTimeData = False):
    t_delta = datetime.timedelta(hours=9)
    JST = datetime.timezone(t_delta, 'JST')
    now = datetime.datetime.now(JST)

    if useTimeData:
        return now

    return now.strftime(format)

def convert_datetime_to_number(date_string, orgFormat = '%Y/%m/%d %H:%M:%S'):
    # 日付と時刻のフォーマットに合わせて datetime オブジェクトを生成
    datetime_obj = datetime.strptime(date_string, orgFormat)
    
    # 指定されたフォーマットで日付を文字列に変換
    number_format = datetime_obj.strftime('%Y%m%d%H%M%S')
    
    # 文字列を整数に変換
    return int(number_format)

def killProccess(procName , force = False):
    cmd = cmd = 'taskkill /im {}'.format(procName)

    if force == True:
        cmd = 'taskkill /f /im {}'.format(procName)
        
    return subprocess.run(cmd,shell=True)

def startProcess(path):
    return subprocess.Popen(path)

# 戻り
# True：str1がstr2に含まれる
# False：str1がstr2に含まない
def strstr(str1, str2 , ignoreCase = True):
    ret = False
    if len(str1) > 0 and len(str2) > 0:
        if ignoreCase == True:
            if str1.lower() in str2.lower():
                ret = True
        else:
            if str1 in str2:
                ret = True

    return ret

def strcmp(str1, str2 , ignoreCase = True):
    ret = False
    if len(str1) > 0 and len(str2):
        if ignoreCase == True:
            if str1.lower() == str2.lower():
                ret = True
        else:
            if str1 == str2:
                ret = True

    return ret

def defungURL(str):
    ret = ''

    if len(str) > 0:
        retTmp = str.replace("http","hxxp").replace("://","[://]")
        ret = re.sub('\.([a-zA-Z])', '[.]\\1', retTmp)

    return ret

# beginとendで指定された文字列で挟まれた文字列を抽出。
# delstrがTrueの時はbegen、endを含まない文字列を返す
def extractStrging(begin, end, str, delstr = True):
    import re
    r = re.compile( '(%s.*%s)' % (begin,end), flags=re.DOTALL) # 途中の改行も含める
    m = r.search(str)
    ret = ''
    extract = ''
    if m is not None:
        extract = m.group(0)

    if delstr == True:
        temp = extract[len(begin):]
        ret = temp[:-len(end)]
    else:
        ret = extract

    return ret

def Dict2String(dict):
    # ensure_ascii=Falseしてしないと日本語がUnicodeエスケープの形式で表示される
    ret = json.dumps(dict,ensure_ascii=False)

    return ret

# googletransだと'NoneType' object has no attribute 'group'になるので 4.0.0-rc1をインストールしてある
# 参考：https://sig9.org/archives/4023
def Google_Translate(input_text):
    translated_jp_text = ''
    try:
        if len(input_text) > 0:
            translator = GoogleTranslator(source='auto', target='ja')
            translated_jp_text = translator.translate(str(input_text))
    except Exception as e:
        translated_jp_text = '翻訳に失敗しました。'
    return translated_jp_text

# 指定した要素を除外して新しいDictionary作成
def create_dict_with_removed_elements(original, elements_to_remove):
    modified_dict = {}

    try:
        for key in original.keys():
            if (key in elements_to_remove) == False:
                modified_dict[key] = original[key]

            # modified_dict[key] = {k: v for k, v in value.items() if k not in elements_to_remove}
    except Exception as e:
        err = 'err create_dict_with_removed_elements'
    return modified_dict

def create_dict_with_selected_elements(original, elements_to_remove):
    modified_dict = {}

    try:
        for key in original.keys():
            if (key in elements_to_remove):
                modified_dict[key] = original[key]

            # modified_dict[key] = {k: v for k, v in value.items() if k not in elements_to_remove}
    except Exception as e:
        err = 'err create_dict_with_selected_elements'
    return modified_dict

import hashlib

def string_to_sha256(input_string):
    """
    与えられた文字列をSHA256ハッシュに変換します。

    Args:
    input_string (str): SHA256ハッシュに変換する文字列

    Returns:
    str: 入力文字列のSHA256ハッシュ
    """
    # 文字列をバイトに変換
    input_bytes = input_string.encode()

    # SHA256ハッシュオブジェクトを作成
    sha256_hash = hashlib.sha256()

    # ハッシュオブジェクトを更新
    sha256_hash.update(input_bytes)

    # ハッシュの16進数表現を返す
    return sha256_hash.hexdigest()

# --------------------------------------------------------------------------------------------------------------
# TODO:イメージ操作系のクラスかPyファイル作ったほうがいいかも。ほかにも散らばってる
# --------------------------------------------------------------------------------------------------------------
import os
import cv2
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
from Config import Config as cf

# メール送信時、差分画像に日時を書き込みたい
def Func_Write_text(inputimage, string_moji):
    img = cv2.imread(inputimage, 1)

    str = string_moji
    str_height = 30
    str_width = 340

    fontface = cv2.FONT_HERSHEY_TRIPLEX

    # ↓ getTextSizeだと幅がかなり大きくなるので自前で測って固定値入れる
    # # 画像内へ印字する文字列の大きさ。倍率指定。
    # fontscale = 2.0
    # # 画像内へ印字する文字列の太さ
    # thickness = 2

    # # 戻り値 ###############################
    # # w : 文字列の幅
    # # h : 文字列の高さ
    # # baseline : ベースライン
    # #####################################
    # (str_width, str_height), baseline = cv2.getTextSize(str, fontface, fontscale, thickness)

    height = img.shape[0]
    width = img.shape[1]

    #cyuushin = (width - str_width)/2
    #小数点以下を丸める
    #cyuushin_marume = round(cyuushin)

    x = width - str_width
    y = str_height

    # 塗りの背景を加える                                                                              
    cv2.rectangle(img, (x, y), (x+str_width, y-str_height), (0, 255, 0), cv2.FILLED, cv2.LINE_AA)

    # 線を加える                                                                                        
    cv2.rectangle(img, (x, y), (x+str_width, y-str_height), (0, 255, 0), 2, cv2.LINE_AA)

    # 文字を加える                                                                                      
    cv2.putText(img, str, (x+3, y-6),fontface, 0.9,(0, 0, 0), 2, cv2.LINE_AA)

    Func_ImageWrite(inputimage, img)
    # return img

def Func_Combine(imgPath1, imgPath2, dstPath):
    img1 = cv2.imread(imgPath1)
    img2 = cv2.imread(imgPath2)

    height_1, width_1 = img1.shape[:2]
    height_2, width_2 = img2.shape[:2]

    height_list = [height_1,height_2] 
    max_height = max(height_list)

    kuro_yoko = width_1 + width_2
    kuro_tate = max_height

    # yoko*tateの黒背景を用意
    img_main = np.zeros((kuro_tate, kuro_yoko, 3), dtype=np.uint8)

    # 左端に画像1を貼る(たて、よこ)
    img_main[0:height_1, 0:width_1] = img1

    yoko2 = width_1+width_2

    img_main[0:height_2, width_1:yoko2] = img2

    Func_ImageWrite(dstPath, img_main)
    # return img_main

def Func_ImageWrite(outPath, outImg, option = None):
    cv2.imwrite(outPath, outImg, option)

#出力画像のファイルサイズ圧縮率(jpeg)
Quality = 100
def Func_Img_encode(img_path):
    img = cv2.imread(img_path)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), Quality]
    result, encimg = cv2.imencode(".jpg", img, encode_param)
    ret_img = cv2.imdecode(encimg, cv2.IMREAD_UNCHANGED)
    Func_ImageWrite(img_path, ret_img)

#画像の枠を囲う
def Func_Draw_Rectangle_Red(img_path, num):
    img = cv2.imread(img_path, 1)
    height = img.shape[0]
    width = img.shape[1]
    cv2.rectangle(img, (0, 0), (width , height ), (0, 0, 255), num)

    Func_ImageWrite(img_path, img)
    return img

def Func_ResizeImage(orgFile = '', outFile = ''):
    # # 画像を開く
    # img = Image.open(orgFile)

    # # 画像のサイズを変更する (ここでは幅と高さを半分にしています)
    # img_resized = img.resize((img.width // 2, img.height // 2))

    # # 圧縮した画像を保存する
    # img_resized.save(outFile)

    img = cv2.imread(orgFile)
    # dst = cv2.resize(img, dsize=None, fx=0.7, fy=0.7)
    Func_ImageWrite(outFile, img, [cv2.IMWRITE_JPEG_QUALITY, 80])

def IsWhiteOutImage(imgFilePath):
    ret = False
    try:
        # # 画像の読み込み
        img = cv2.imread(imgFilePath)
        # 白以外のピクセルが存在するかどうかをチェック
        white_pixels = (img == [255, 255, 255]).all(axis=2)
        
        ret = white_pixels.all()

    except Exception as e:
        print(str(e))

    return ret

def Output_diff(RansomName,outputdir,result_img):
    now = datetime.datetime.now()
    OutPutFileName = 'DiffResult_'  + RansomName + "_" + '{0:%Y%m%d_%H%M%S}.jpg'.format(now)
    OutPutFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), outputdir + "\\" + OutPutFileName) 
    # Logging(RansomName,"差分結果の画像を出力：" + OutPutFilePath)
    cv2.imwrite(str(OutPutFilePath), result_img)
    return OutPutFilePath

#応用差分検知の閾値(デフォルト1.8)5.8
limitNum_g = 1.5
# 単純差分でなく、細かい領域に分割して特徴点を探し一致させてから差分させる方法。
# 精度は単純差分と同じぐらい高い。閾値は１以上がよさそう。
def CheckByImageDiff2(RansomName,inputImage1,inputImage2):
    # Logging(RansomName,"応用差分比較法で比較開始：" + RansomName)
    # Logging(RansomName,"inputImage1:" + inputImage1 + "(FileSile:" + str(os.path.getsize(inputImage1)) + ")")
    # Logging(RansomName,"inputImage2:" + inputImage2+ "(FileSile:" + str(os.path.getsize(inputImage2)) + ")")

    # Logging(RansomName,"それぞれの画像を読み込み")
    #読み込み
    source_img = cv2.imread(inputImage1)
    target_img = cv2.imread(inputImage2)

    # Logging(RansomName,"画像比較処理を開始")

    kernel = np.ones((3, 3), np.uint8)

    max_hight = max(source_img.shape[0], target_img.shape[0])
    max_width = max(source_img.shape[1], target_img.shape[1])

    temp_img = source_img
    source_img = np.zeros((max_hight, max_width, 3), dtype=np.uint8)
    source_img[0:temp_img.shape[0], 0:temp_img.shape[1]] = temp_img

    temp_img = target_img
    target_img = np.zeros((max_hight, max_width, 3), dtype=np.uint8)
    target_img[0:temp_img.shape[0], 0:temp_img.shape[1]] = temp_img

    result_img = cv2.addWeighted(source_img, 0.5, target_img, 0.5, 0)

    #グレースケールに変換
    source_img = cv2.cvtColor(source_img, cv2.COLOR_BGR2GRAY)
    target_img = cv2.cvtColor(target_img, cv2.COLOR_BGR2GRAY)

    #差分計算
    img = cv2.absdiff(source_img, target_img)
    rtn, img = cv2.threshold(img, 0, 255, cv2.THRESH_OTSU)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)

    #RETR_EXTERNALが外側だけ
    #RETR_TREEが階層情報維持
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    #いったんグレーにしてカラーに変換
    result_img_gray = cv2.cvtColor(result_img, cv2.COLOR_BGR2GRAY)
    result_img = cv2.cvtColor(result_img_gray, cv2.COLOR_GRAY2RGB)
    

    #薄くする--------------------ここから

    ## γ値の定義(1より小さいと暗く、1より大きいと明るくなる)
    gamma = 5.0

    # ルックアップテーブルの生成
    look_up_table = np.zeros((256,1), dtype=np.uint8)
    for i in range(256):
        look_up_table[i][0] = 255* (float(i)/255) ** (1.0 / gamma)

    # γ変換後の画像取得
    result_img = cv2.LUT(result_img, look_up_table)

    #薄くする--------------------ここまで

    #差異部分を描画(赤色)
    result_img = cv2.drawContours(result_img, contours, -1, (0, 0, 255),1)

    #cv2.imshow('color', result_img) #この時点ではウィンドウは表示されない
    #cv2.waitKey(0) #ここで初めてウィンドウが表示される

      #2値画像に存在する輪郭の座標値を得る
    #contoursから一個ずつ輪郭を取り出し、輪郭の位置(x,y)とサイズ(width, height)を得る
    #サイズが 特定以上の輪郭を枠で囲う。
    temp = result_img.copy()
    for contour in contours:
  
        # remove small objects
        if cv2.contourArea(contour) < 100:
            continue

        x, y, width, height = cv2.boundingRect(contour)
        cv2.rectangle(temp, (x-2, y-2), (x+width+2, y+height+2), (0, 255, 0), 2)

    result_img = temp

    #差異スコアの計算
    score = 0
    for contour in contours:
        score += cv2.contourArea(contour)
    score /= max_hight * max_width
    score = score * 100

    #小数点以下を丸める
    score = round(score, 5)
    score = Decimal(score).quantize(Decimal('.00000'),rounding=ROUND_HALF_UP)

    # Logging(RansomName,"比較結果の値(score)：" + str(score))

    #検知フラグ
    scoreCheck = False
    
    global limitNum_g
    local_limitNum = limitNum_g

    #個別の閾値設定===================================

    if RansomName == "dotAdmin":
        local_limitNum = 4.0
        # Logging(RansomName,"個別の閾値を設定（変更後：" + str(local_limitNum) + ")")

    if RansomName == "LockBit2_0":
        local_limitNum = 0.6
    elif RansomName == "AlphVM":
        local_limitNum = 0.1
    elif RansomName == "LKB2_accenture":
        local_limitNum = 0.01
    elif RansomName == "LKB2_YazakiGroup":
        local_limitNum = 0.01
    elif RansomName == "LKB2_Abecho":
        local_limitNum = 0.01
    elif RansomName == "Groove":
        local_limitNum = 3.4
    elif RansomName == "MKT_Fujitsu":
        local_limitNum = 0.1
    elif RansomName == "CL0P_TA505":
        local_limitNum = 0.9
    elif RansomName == "RANSOM_SUPPORT":
        local_limitNum = 3.5
    elif RansomName == "MBC_Ransomware":
        local_limitNum = 9.0
    elif RansomName == "Hive":
        local_limitNum = 1.5
    elif RansomName == "CONTI_Ryuk":
        local_limitNum = 1.0
    elif RansomName == "CON_TI_SANOH":
        local_limitNum = 0.3
    elif RansomName == "Dark_Leak_Market":
        local_limitNum = 0.9
    elif RansomName == "Lorenz":
            local_limitNum = 2.4
    elif RansomName == "RansomEXX":
            local_limitNum = 1.2
    elif RansomName == "XING_Team":
            local_limitNum = 0.3
    elif RansomName == "Arvin_Club":
            local_limitNum = 0.9
    elif RansomName == "RAMP":
            local_limitNum = 2.3
    
    # Logging(RansomName,"個別の閾値を設定（変更後：" + str(local_limitNum) + ")")
    #個別の閾値設定===================================

    #グローバルに設定
    limitNum_g = local_limitNum

    ret_output_filepath = ''
    #閾値チェック
    if score >= local_limitNum:    

        # Logging(RansomName,"差分結果が閾値より大きいと判断 (現在の閾値設定：" + str(local_limitNum) + ")")

        outputdir = cf.PATH_SCREENSHOT_DIFF_DIR

        #差分画像を出力
        ret_output_filepath = Output_diff(RansomName,outputdir,result_img)

        #一時フォルダに2つの入力画像のコピーを念のため作成
        # BackUpImage(RansomName,inputImage1,inputImage2)
        scoreCheck = True

        # SendMail_Main(RansomName,score, outputdir, inputImage1,inputImage2,ret_output_filepath)

    else:
        # Logging(RansomName,"差分結果が閾値より小さいと判断 (現在の閾値設定：" + str(local_limitNum) + ")")

        outputdir = cf.PATH_SCREENSHOT_DIFF_DIR

        #差分画像を出力
        ret_output_filepath = Output_diff(RansomName,outputdir,result_img)

        scoreCheck = False

    return ret_output_filepath

#テンプレートマッチングでの存在判定
def Judge_TempleteMatching(logoimg,inputimg):
    img = cv2.imread(inputimg)
    template = cv2.imread(logoimg)
    _, w, h = template.shape[::-1]
    res = cv2.matchTemplate(img,template,cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    top_left = max_loc
    btm_right = (top_left[0] + w, top_left[1] + h)

    cv2.rectangle(img,top_left, btm_right, 255, 2)

    log_x = top_left[0]
    log_y = top_left[1]
    #cv2.imshow("test", img)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    if 0.99 < max_val:
        return True
    else:
        return False

# dictionaryを指定したサイズに分ける
def split_dict_fixed_size(data: dict, chunk_size: int) -> list[dict]:
    """
    ディクショナリを指定したサイズで分割する関数
    最後のグループは指定サイズより少なくなる可能性があります
    
    Args:
        data (dict): 分割したい元のディクショナリ
        chunk_size (int): 各グループの要素数
        
    Returns:
        list[dict]: 分割されたディクショナリのリスト
    """
    # キーのリストを取得
    keys = list(data.keys())
    
    # 結果を格納するリスト
    result = []
    
    # chunk_sizeごとに分割
    for i in range(0, len(keys), chunk_size):
        chunk_keys = keys[i:i + chunk_size]
        chunk_dict = {k: data[k] for k in chunk_keys}
        result.append(chunk_dict)
        
    return result

def diffDetectedTime(timePrev, timeNow):

    from datetime import datetime
    # 文字列を日時オブジェクトに変換
    dt1 = datetime.strptime(timePrev, '%Y/%m/%d %H:%M:%S')
    dt2 = datetime.strptime(timeNow, '%Y/%m/%d %H:%M:%S')

    # 差分を計算
    diff = dt2 - dt1

    # 日数を取得
    days = diff.days

    # 残りの時間（秒）から時間と分を計算
    seconds = diff.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    return days, hours, minutes

def cleanup_box_files(target_folder):
    try:
        MAX_BOX_FILES = 10
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
