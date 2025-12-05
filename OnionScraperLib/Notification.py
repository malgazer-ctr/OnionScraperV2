import os
import re
import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import Config as cf
from Config import Config as cf
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import GenerativeAI as ga
from OnionScraperLib import CheckJapanese as cj
from OnionScraperLib import Log
from OnionScraperLib import exception_tracker

def createSubject_HTMLVer(groupName, isUrgent, getHtmlStatus, retIsNoImportantMail = False, isOnleyDeleted = False, extraSubject = '',htmlDataSize = 0):
    ret = ''

    subject_Opt1 = ''
    subject_Opt2 = ''

    # 削除差分に重要単語が見つかった場合（メールボディ作成時）は件名を特別なものにする
    if isUrgent and retIsNoImportantMail == True:
        subject_Opt1 = "【重要(削除差分)】"
    elif isUrgent == True:
        subject_Opt1 = "【重要】"

    if isOnleyDeleted == True:
        subject_Opt2 = "【削除差分のみ】"

    # 個別対応対象なのに情報取れてないときはHTML構造変わった疑惑
    if getHtmlStatus & cf.SUB_RETURNCODE_GETHTML_INDIVISUAL_FAILED:
        subject_Opt2 = subject_Opt2 + '【サイト構成変更の可能性】'

    # HTMLが一切取得できてない（forceNotification ==TRUE）の時は件名固定でこれ
    if htmlDataSize == 0:
        subject_Opt1 = '【アクセス不可】'
        subject_Opt2 = ''

    ret = "[V2]{}{}{} ★{} --更新あり (MBSD リークサイトモニター3)".format(subject_Opt1, subject_Opt2, extraSubject, groupName)

    return ret


def escapeRegexpChar(str):
    escapeTargetArray = ['\\', '*', '+', '.', '?', '{' '}', '(', ')', '[', ']', '^', '$', '-', '|', '/']

    retStr = str
    replacedStr = str
    for i in escapeTargetArray:
        replacedStr = retStr.replace(i, f'\\{i}')
        retStr = replacedStr

    return retStr

# 重要単語をハイライトする
def setHighLightImportantWord(str, extraWordList):
    strTmp = str
    
    if strTmp != '' and len(extraWordList) > 0:
        for i in extraWordList:
            diffPlaneTxtTmp =strTmp
            replaceStr = '<span style="background-color:#FFFF00"><font color="red"><b>{}</b></font></span>'.format(i)
            
            strTmp = diffPlaneTxtTmp.replace(i, replaceStr)

            # 正規表現でやると置換で全部小文字になるので
            # pattern = re.compile(i, re.IGNORECASE)
            # strTmp = re.sub(pattern, replaceStr, diffPlaneTxtTmp)

    ret = strTmp

    return ret

def createNotificationBody_HTMLVer(
    groupName = '',
    actualNewVictimsDict = {},
    actualDeletedVictimsDict = {},
    updateInfo = {},
    updateInfoDel = {},
    importantWordsList = [],
    importantWordsReplaceList = [],
    diffPlaneTxt = '',
    diffHtmlData = '',
    diffTime_before_ = '',
    diffTime_after_ = '',
    diffSize_before_ = '',
    diffSize_after_ = '',
    imageURL = '',
    successScreenShot = False,
    urgentMailInfo = {},
    japanRelatedOrganizations_VicList = [],
    setUrgentFlgByAI_VicList = [],
    importantWordsList_jp = [],
    importantWordsReplaceList_jp = [],
    ):

    tempExtraWord = ''
    tempExtraWord2 = ''
    isImportantMail = False
    retIsNoImportantMail = False
    AccessLogTable_ = ''

    try:
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
                    diffPlaneTxtTmp2 = diffPlaneTxtTmp
                    diffPlaneTxtTmp = setHighLightImportantWord(diffPlaneTxtTmp, importantWordsReplaceList+importantWordsReplaceList_jp)
                    if diffPlaneTxtTmp != diffPlaneTxtTmp2:
                        isImportantMail = True

                    diffPlaneTxtArray.append(diffPlaneTxtTmp)
                elif i.startswith('-') == True:
                    diffPlaneTxtTmp = '<span style="color:red">{}</span><br>'.format(i)

                    # 削除差分のみに重要ワードがある場合はメールに重要フラグ立てたくない
                    diffPlaneTxtTmp2 = diffPlaneTxtTmp
                    diffPlaneTxtTmp = setHighLightImportantWord(diffPlaneTxtTmp, importantWordsReplaceList+importantWordsReplaceList_jp)
                    if diffPlaneTxtTmp != diffPlaneTxtTmp2:
                        retIsNoImportantMail = True

                    diffPlaneTxtArray.append(diffPlaneTxtTmp)
                else:
                    if i != '':
                        diffPlaneTxt += i
            
            diffPlaneTxt = '\n'.join(diffPlaneTxtArray)

            # 削除差分のみに重要ワードがある場合はメールに重要フラグ立てたくない
            if isImportantMail:
                retIsNoImportantMail = False

        actualNewVictimsStr = ''
        if len(actualNewVictimsDict) > 0:
            actualNewVictimsStr = '<h3>■ 追加された被害組織</h3>'

            # 差分画像でcid:image3まで確定なので4から
            for i in actualNewVictimsDict.keys():
                companyName_ = setHighLightImportantWord(i, importantWordsReplaceList+importantWordsReplaceList_jp)
                # if companyName_ != i:
                #     isImportantMail = True
                companyUrl_ = setHighLightImportantWord(actualNewVictimsDict[i]['url'], importantWordsReplaceList+importantWordsReplaceList_jp)
                # if companyUrl_ != actualNewVictimsDict[i]['url']:
                #     isImportantMail = True
                companysummary_ = setHighLightImportantWord(actualNewVictimsDict[i]['summary'], importantWordsReplaceList+importantWordsReplaceList_jp)
                # if companysummary_ != actualNewVictimsDict[i]['summary']:
                #     isImportantMail = True     
                summary_JP = actualNewVictimsDict[i].get('summary_JP', '')
                companysummary_JP_ = setHighLightImportantWord(summary_JP, importantWordsReplaceList+importantWordsReplaceList_jp)
                updateTime_ = actualNewVictimsDict[i]['updateDate']
                detectedDate_ = actualNewVictimsDict[i].get('detectedDate','')
                detailScreenShotTag_ = actualNewVictimsDict[i].get('detailScreenshotTag','')
                searchOnGenerativeAI_ = setHighLightImportantWord(actualNewVictimsDict[i].get('searchOnGenerativeAI',''), importantWordsReplaceList+importantWordsReplaceList_jp)
                screenShotURL_ = actualNewVictimsDict[i].get('screenShotUrl', '')
                if len(companyName_) <= 0:
                    companyName_ = '(該当項目存在せず)'
                else:
                    # 現状generateDiffDataIndivisualInfo関数内で過去検知済みのものは排除してるのでこのロジック封印してもいい 2023/7/26
                    isDetected = actualNewVictimsDict[i].get('isDetected',False)
                    if isDetected == True:
                        companyName_ = companyName_ + ' (過去検知済み)'
                if len(companyUrl_) <= 0:
                    companyUrl_ = '(該当項目存在せず)'
                if len(companysummary_) <= 0:
                    companysummary_ = '(該当項目存在せず)'
                if len(companysummary_JP_) <= 0:
                    companysummary_JP_ = '(該当項目存在せず)'
                if len(updateTime_) <= 0:
                    updateTime_ = '(該当項目存在せず)'
                if len(detectedDate_) <= 0:
                    detectedDate_ = '(該当項目存在せず)'
                if len(detailScreenShotTag_) <= 0:
                    detailScreenShotTag_ = '(該当項目存在せず)'
                if len(searchOnGenerativeAI_) <= 0:
                    searchOnGenerativeAI_ = '(該当項目存在せず)'
                else:
                    searchOnGenerativeAI_ = searchOnGenerativeAI_.replace('\n', '<br>') + '<br>(生成AIによる自動調査はベータ版であり結果を保証するものではありません。)'

                actualNewVictimsStr += Template(cf.DATA_TEMPLATE_DIFFINFO).substitute(companyName = uf.defungURL(companyName_),
                                                                                    companyUrl = uf.defungURL(companyUrl_),
                                                                                    companysummary = uf.defungURL(companysummary_).replace('\n', '<br>'),
                                                                                    companysummary_jp = uf.defungURL(companysummary_JP_).replace('\n', '<br>'),
                                                                                    updateTime = updateTime_,
                                                                                    detectedDate = detectedDate_,
                                                                                    searchOnGenerativeAI = uf.defungURL(searchOnGenerativeAI_).replace('\n', '<br>'),
                                                                                    searchOnWeb = f'<a href="https://www.google.com/search?q=&quot;{i}&quot;">"{i}"をGoogleで検索</a>',
                                                                                    detailScreenShot = detailScreenShotTag_,
                                                                                    screenShotURL = screenShotURL_
                                                                                    )

        actualDelVictimsStr = ''
        if len(actualDeletedVictimsDict) > 0:
            actualDelVictimsStr = '<h3>■ 削除された可能性のある被害組織</h3><font size="-2">(※古いページへの移動などで表示されなくなったケースを含みます)</font><br><br>'
            for i in actualDeletedVictimsDict.keys():
                companyName_ = setHighLightImportantWord(i, importantWordsReplaceList+importantWordsReplaceList_jp)
                # setHighLightImportantWordでハイライト処理されてきたら重要単語があったということ。新規追加差分に重要単語があるなら重要メール。
                # 削除差分にしか見つからない場合は件名を変えて重要フラグを呼び元で落とす
                # retIsNoImportantMailが立たなければ呼び元で何もしない。気持ち悪いけど後付け処理なので妥協
                # if isImportantMail == False and companyName_ != i:
                #     retIsNoImportantMail = True
                companyUrl_ = setHighLightImportantWord(actualDeletedVictimsDict[i]['url'], importantWordsReplaceList+importantWordsReplaceList_jp)
                # if isImportantMail == False and companyUrl_ != actualDeletedVictimsDict[i]['url']:
                #     retIsNoImportantMail = True
                companysummary_ = setHighLightImportantWord(actualDeletedVictimsDict[i]['summary'], importantWordsReplaceList+importantWordsReplaceList_jp)
                # if isImportantMail == False and companysummary_ != actualDeletedVictimsDict[i]['summary']:
                #     retIsNoImportantMail = True
                summary_JP = actualDeletedVictimsDict[i].get('summary_JP', '')      
                companysummary_JP_ = setHighLightImportantWord(summary_JP, importantWordsReplaceList+importantWordsReplaceList_jp)
                updateTime_ = actualDeletedVictimsDict[i]['updateDate']
                # あとから追加したのでないことも想定
                detectedDate_ = actualDeletedVictimsDict[i].get('detectedDate','')

                if len(companyName_) <= 0:
                    companyName_ = '(該当項目存在せず)'
                if len(companyUrl_) <= 0:
                    companyUrl_ = '(該当項目存在せず)'
                if len(companysummary_) <= 0:
                    companysummary_ = '(該当項目存在せず)'
                if len(companysummary_JP_) <= 0:
                    companysummary_JP_ = '(該当項目存在せず)'
                if len(updateTime_) <= 0:
                    updateTime_ = '(該当項目存在せず)'  
                if len(detectedDate_) <= 0:
                    detectedDate_ = '(該当項目存在せず)'  
                actualDelVictimsStr += Template(cf.DATA_TEMPLATE_DIFFINFO_DEL).substitute(companyName = uf.defungURL(companyName_),
                                                                                    companyUrl = uf.defungURL(companyUrl_),
                                                                                    companysummary = uf.defungURL(companysummary_).replace('\n', '<br>'),
                                                                                    companysummary_jp = uf.defungURL(companysummary_JP_).replace('\n', '<br>'),
                                                                                    updateTime = updateTime_,
                                                                                    detectedDate = detectedDate_,
                                                                                    searchOnGenerativeAI = '(該当項目存在せず)',
                                                                                    searchOnWeb = f'<a href="https://www.google.com/search?q=&quot;{i}&quot;">"{i}"をGoogleで検索</a>',
                                                                                    detailScreenShot = '(削除対象は未取得のため情報無し)',
                                                                                    screenShotURL = '(削除対象は未取得のため情報無し)'
                                                                                    )

        # URLをデファング
        defangDiffPlaneTxt = '<font size="-2">\
        <span style="color:green;background-color:gainsboro"> + </span>は追加された行を、<span style="color:red;background-color:gainsboro"> - </span>は削除された行を意味します。</br>\
        (TOPページから古いページに移動された場合も<span style="color:red;background-color:gainsboro"> - </span>として表示される場合があります。)</br></font><hr size="2" width="100%" align="center">'+uf.defungURL(diffPlaneTxt)

        # ChatGPTにサマリー生成依頼
        summaryText = ''

        setUrgentInfo = False
        setUrgentInfo = True if True in urgentMailInfo.values() else setUrgentInfo

        if setUrgentInfo:
            tempExtraWordList = []

            urgent_hasImportantWords = urgentMailInfo.get('urgent_hasImportantWords',False)
            notUrgent_OnlyDeleted = urgentMailInfo.get('notUrgent_OnlyDeleted',False)
            hasJapanRelatedOrganizations = urgentMailInfo.get('hasJapanRelatedOrganizations',False)
            urgent_ByAI = urgentMailInfo.get('urgent_ByAI',False)
            urgent_UserSpecified = urgentMailInfo.get('urgent_UserSpecified',False)
            urgent_infoUpdate = urgentMailInfo.get('urgent_infoUpdate',False)
            changedHTMLStructure = urgentMailInfo.get('changedHTMLStructure',False)
            isSiteChange2Unavailable = urgentMailInfo.get('isSiteChange2Unavailable',False)
            isSiteChange2Available = urgentMailInfo.get('isSiteChange2Available',False)

            if changedHTMLStructure:
                tempExtraWordList.append(f'<font color="red">(サイト構成)サイト構成が変更された可能性があります</font><br>')

            if isSiteChange2Unavailable:
                tempExtraWordList.append(f'<font color="red">(サイト接続)サイトに接続できなくなった可能性があります</font><br>')
                defangDiffPlaneTxt = 'アクセス不可のため取得できませんでした。'
            elif isSiteChange2Available:
                tempExtraWordList.append(f'<font color="red">(サイト接続)サイトに接続できるようになった可能性があります</font><br>')
                # defangDiffPlaneTxt = 'アクセス不可のため取得できませんでした。'

            #重要ワード
            if urgent_hasImportantWords:
                if len(importantWordsList) > 0:
                    txt = ', '.join(importantWordsList)
                    tempExtraWordList.append(f'<font color="red">(重要ワード)以下の単語が含まれています</font><span style="background-color:#FFFF00"><font color="red"><b>[ {txt} ]</b></font></span><br>')
                
                if len(importantWordsList_jp) > 0:
                    txt = ', '.join(importantWordsList_jp)
                    tempExtraWordList.append(f'<font color="red">(生成AIによる日本語検知)以下の言葉が含まれています</font><span style="background-color:#FFFF00"><font color="red"><b>[ {txt} ]</b></font></span><br>')
                  
                tempExtraWordList.append('<font size="-2">※"重要情報の自動識別機能"ベータ版稼働中。日本に関連しない組織情報が重要情報として扱われている可能性があります。</font>')

            # 重要ワード（削除のみ）
            if notUrgent_OnlyDeleted:
                tempExtraWordList.append('<br><font color="green"><b>（※本メールは重要ワードが含まれますが、【削除/移動】された情報に対する検知のためご注意ください。）</b></font>')

            # tempExtraWordList.append(tempExtraWord)

            # 指定された重要組織の更新
            if urgent_infoUpdate and (len(updateInfo) > 0 or len(updateInfoDel) > 0):
                str = ', '.join(list(updateInfo.keys()) + list(updateInfoDel.keys()))
                tempExtraWordList.append(f'<font color="red">(指定情報更新)以下の更新情報が含まれています</font><span style="background-color:#FFFF00"><font color="red"><b>[ {str} ]</b></font></span>')
            
            # CIGにより指定された個別情報の更新（TargetURL.jsonで指定されている）
            if urgent_UserSpecified:
                tempExtraWordList.append(f'<font color="red">(指定情報更新-個別)指定された個別情報が更新された可能性があります。</font>')

            # 生成AI調査による重要組織以外の情報
            try:
                if hasJapanRelatedOrganizations:
                    strJPVic = ', '.join(japanRelatedOrganizations_VicList)
                    tempExtraWordList.append(f'<font color="red">(生成AI調査)日本に関係する組織が含まれる可能性があります。以下を参照してください。</font>\
                                            <br>■対象：<font color="red">[ {strJPVic} ]</font>')
                if urgent_ByAI:
                    strVic = ', '.join(setUrgentFlgByAI_VicList)
                    # tempExtraWordList.append(f'<font color="red">(生成AI調査)生成AIによる調査の結果、以下の被害組織情報に重要情報が含まれている可能性があります。「生成AIによる調査」を参照してください。</font>\
                    #                         <br>■対象となる被害組織情報：<font color="red">[ {strVic} ]。</font>\
                    #                         <br>■重要情報と判断した理由：一般的な被害組織名だけでなく、文章として構成された情報が含まれています。')
                    tempExtraWordList.append(f'<font color="red">(生成AI調査)被害組織名に文章等が含まれる可能性があります。以下を参照してください。</font>\
                                            <br>■対象：<font color="red">[ {strVic} ]</font>')
            except:
                if hasJapanRelatedOrganizations:
                    tempExtraWordList.append(f'<font color="red">(生成AI調査)被害組織に日本に関係する組織が含まれる可能性があります。</font>')   
                if urgent_ByAI:
                    tempExtraWordList.append(f'<font color="red">(生成AI調査)被害組織名に文章等が含まれる可能性があります。</font>\
                                            <br><font size="-2">※攻撃グループによるアナウンスなどと判断された可能性</font>')           
            
            tempExtraWord = '<h3>■重要情報</h3>' + '<br><br>'.join(tempExtraWordList) + '<br>'

        accessLogArray = Log.readAccessLog(groupName, Log.getAccessLogPath(groupName))
        cnt = 0
        for item in accessLogArray:
            if cnt >= cf.ACCESSLOG_ON_DETECTMAIL_MAX:
                break

            logCntStr = '今回'
            if cnt > 0:
                logCntStr = f'-{cnt}'

            accessStartTime = item['accessStartTime']
            accessEndTime = item['accessEndTime']
            getHTMLStatus = item['getHTMLStatus']
            htmlSize = item['htmlSize']
            AccessLogTable_ += \
                f'<tr>\
                    <td align="center">{logCntStr}</td>\
                    <td>{accessStartTime}</td>\
                    <td>{accessEndTime}</td>\
                    <td>{getHTMLStatus}</td>\
                    <td>{htmlSize}</td>\
                </tr>'
            cnt += 1

        # if isUrgent:
        #     if len(importantWordsList) > 0:
        #         txt = ', '.join(importantWordsList)
        #         tempExtraWord = f'<font color="red">以下の単語が含まれています</font><span style="background-color:#FFFF00"><font color="red"><b>[ {txt} ]</b></font></span><br>\
        #         <font size="-2">※"重要情報の自動識別機能"ベータ版稼働中。日本に関連しない組織情報が重要情報として扱われている可能性があります。</font><br>'
            
        #     else:
        #         tempExtraWord = f'<font color="red">日本の組織が含まれている可能性があります</font><br>\
        #         <font size="-2">※"重要情報の自動識別機能"ベータ版稼働中。日本に関連しない組織情報が重要情報として扱われている可能性があります。</font><br>'

        #     if importantWord_OnlyDeleted:
        #         tempExtraWord = tempExtraWord + '<font color="green"><b>（※本メールは重要ワードが含まれますが、【削除/移動】された情報に対する検知のためご注意ください。）</b></font><br>'

        #     if setMailUrgentFlg:
        #         if tempExtraWord == '':
        #             tempExtraWord = f'<font color="red">被害組織情報以外の重要情報が含まれている可能性があります。</font><br>'
        #         else:
        #             tempExtraWord += '<br><font color="red">被害組織情報以外の重要情報が含まれている可能性があります。</font><br><br>' 

        # if len(updateInfo) > 0 or len(updateInfoDel) > 0:
        #     str = ', '.join(list(updateInfo.keys()) + list(updateInfoDel.keys()))
        #     tempExtraWord2 = f'<h3>■サイトの更新あり</h3><font color="red">以下の更新情報が含まれています</font><span style="background-color:#FFFF00"><font color="red"><b>[ {str} ]</b></font></span><br>'

        if successScreenShot == False:
            screenShotFailed_ = 'スクリーンショットの取得に失敗しました。<br>'
        else:
            screenShotFailed_ = ''

        ret = Template(cf.DATA_TEMPLATE_HTML).substitute(
            TargetName = groupName,
            AISummery = summaryText,
            ExtraWord = tempExtraWord,
            ExtraWord2 = tempExtraWord2,
            ActualNewVictims = actualNewVictimsStr,
            ActualDelVictims = actualDelVictimsStr,
            diffText = defangDiffPlaneTxt,
            diffHTML = diffHtmlData,
            diffImage = '',
            fileDateTime_Before = diffTime_before_,
            fileDateTime_After = diffTime_after_,
            fileDateSize_Before = diffSize_before_,
            fileDateSize_After = diffSize_after_,
            imageURL = imageURL,
            screenShotFailed = screenShotFailed_,
            AccessLogTable = AccessLogTable_
            )
        
    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        ret = f'【Function】createNotificationBody_HTMLVer\n【GroupName】{groupName}\n【ERROR】{str(e)}'

    return ret

def createNotificationBody_AccessLogReport(leaksiteDict):
    # global globalTargetDict
    ret = ''
    statistics_ = ''
    tableBody_ = ''

    try:
        try:
            sortedDic = dict(sorted(leaksiteDict.copy().items()))
        except:
            sortedDic = leaksiteDict

        totalAmount = len(sortedDic.keys())
        # IsActive指定がないものがもしあったらActive扱い
        # activeAmount = len(dict(filter(lambda x: ('IsActive' in x[1]) == False or uf.strstr('○', x[1]['IsActive']), sortedDic.items())).keys())

        dict_ransomwareGroupSite = dict(filter(lambda x: ('SiteCategory' in x[1]) == True and x[1]['SiteCategory'] == 'RansowareLeakSite', sortedDic.items()))
        ransomwareLeakSiteCount_ = len(dict_ransomwareGroupSite)
        ransomwareLeakSiteCount_Active_ = len(dict(filter(lambda x: ('IsActive' in x[1]) == False or uf.strstr('○', x[1]['IsActive']), dict_ransomwareGroupSite.items())).keys())
        ransomwareLeakSiteCount_InActive_ = ransomwareLeakSiteCount_ - ransomwareLeakSiteCount_Active_
        otherSiteCount_ = totalAmount - ransomwareLeakSiteCount_
        # statistics_Tmp = f'監視対象URL件数(※1): {str(totalAmount)} 件<br>ランサムウェアグループのリークサイト：{str(ransomwareLeakSiteCount)}件<br>アクティブ(※2): {str(activeAmount)} / {str(totalAmount)}件<br>非アクティブ: {str(nonActiveAmount)} / {str(totalAmount)} 件<br>'
        # note = '※1: 一部リークサイト以外も含む<br>※2: 一週間以内にサイトアクセス可能である<br>'
        # statistics_ = statistics_Tmp + note
        # いったん使ってないので空いれとく
        statistics_ = ''

        # コラボレートするフォルダの最上階
        box_shareFolderLink = ''

        # Table内に特定のOnionURLあるとGmailのセキュリティにはじかれるっぽいので別でメール本文にいれてみる
        onionUrlArray = []

        for groupName in sortedDic.keys():
            item = sortedDic[groupName]
            
            IsActive = ''
            lastAccessSuccessTime = item.get('lastAccessSuccessTime', '記録なし')
            if lastAccessSuccessTime == '':
                lastAccessSuccessTime = '記録なし'
            lastAccessTime_0 = ''
            lastAccessTime_1 = ''
            lastAccessTime_2 = ''
            url = item.get('url', '-')
            siteCategory = item.get('SiteCategory', '-')

            IsActive = item.get('IsActive', '-')
            if uf.strstr('○', IsActive):
                IsActive = f'<td nowrap bgcolor="green" align="center"><font color="white"><b>{IsActive}</b></font></td>'
            elif uf.strstr('×', IsActive):
                IsActive = f'<td nowrap bgcolor="red" align="center"><font color="white"><b>{IsActive}</b></font></td>'
            elif uf.strstr('△', IsActive):
                IsActive = f'<td nowrap bgcolor="yellow" align="center"><font color="black"><b>{IsActive}</b></font></td>'
            else:
                IsActive = f'<td nowrap bgcolor="yellow" align="center"><font color="black"><b>{IsActive}</b></font></td>'

            lastAccessTime_0 = item.get('lastAccess-0', '-')
            accessStatus = item.get('accessStatus-0', '-')
            if uf.strstr('○', accessStatus):
                lastAccessTime_0 = f'<td nowrap bgcolor="green" align="center"><font color="white"><b>{lastAccessTime_0}({accessStatus})</b></font></td>'
            elif uf.strstr('×', accessStatus):
                lastAccessTime_0 = f'<td nowrap bgcolor="red" align="center"><font color="white"><b>{lastAccessTime_0}({accessStatus})</b></font></td>'
            else:
                lastAccessTime_0 = f'<td nowrap bgcolor="black" align="center"><font color="white"><b>{lastAccessTime_0}({accessStatus})</b></font></td>'
                
            lastAccessTime_1 = item.get('lastAccess-1', '-')
            accessStatus = item.get('accessStatus-1', '-')
            if uf.strstr('○', accessStatus):
                lastAccessTime_1 = f'<td nowrap bgcolor="green" align="center"><font color="white"><b>{lastAccessTime_1}({accessStatus})</b></font></td>'
            elif uf.strstr('×', accessStatus):
                lastAccessTime_1 = f'<td nowrap bgcolor="red" align="center"><font color="white"><b>{lastAccessTime_1}({accessStatus})</b></font></td>'
            else:
                lastAccessTime_1 = f'<td nowrap bgcolor="black" align="center"><font color="white"><b>{lastAccessTime_1}({accessStatus})</b></font></td>'

            lastAccessTime_2 = item.get('lastAccess-2', '-')
            accessStatus = item.get('accessStatus-2', '-')
            if uf.strstr('○', accessStatus):
                lastAccessTime_2 = f'<td nowrap bgcolor="green" align="center"><font color="white"><b>{lastAccessTime_2}({accessStatus})</b></font></td>'
            elif uf.strstr('×', accessStatus):
                lastAccessTime_2 = f'<td nowrap bgcolor="red" align="center"><font color="white"><b>{lastAccessTime_2}({accessStatus})</b></font></td>'
            else:
                lastAccessTime_2 = f'<td nowrap bgcolor="black" align="center"><font color="white"><b>{lastAccessTime_2}({accessStatus})</b></font></td>'

            groupFolder = item.get('box_groupFolderUrl', '-')
            groupNameWithLink = groupName
            if groupFolder != '':
                groupNameWithLink = f'<a href="{groupFolder}">{groupName}</a>'

            # tableBody_ += f'<tr>\
            #                 <td nowrap>{groupNameWithLink}</td>\
            #                 {IsActive}\
            #                 <td nowrap>{lastAccessSuccessTime}</td>\
            #                 {lastAccessTime_0}\
            #                 {lastAccessTime_1}\
            #                 {lastAccessTime_2}\
            #                 <td nowrap>{uf.defungURL(url)}</td>\
            #                 <td nowrap>{siteCategory}</td>\
            #                 </tr>'
            tableBody_ += f'<tr>\
                            <td nowrap>{groupNameWithLink}</td>\
                            {IsActive}\
                            <td nowrap>{lastAccessSuccessTime}</td>\
                            {lastAccessTime_0}\
                            {lastAccessTime_1}\
                            {lastAccessTime_2}\
                            <td nowrap>掲載保留</td>\
                            <td nowrap>{siteCategory}</td>\
                            </tr>'
            # onionUrlArray.append(f'{groupName}:{uf.defungURL(url)}')

            # 一回入れればいいけどまぁいっか
            box_shareFolderLink = item.get('box_shareFolderLink', '-')

        if tableBody_ != '':
            # retOnionUrls = '<br>'.join(onionUrlArray)
            # 保留
            retOnionUrls = ''

            ret = Template(cf.DATA_TEMPLATE_REPORTHTML).substitute(
                statistics = statistics_,
                totalCount = totalAmount,
                ransomwareLeakSiteCount = ransomwareLeakSiteCount_,
                ransomwareLeakSiteCount_Active = ransomwareLeakSiteCount_Active_,
                ransomwareLeakSiteCount_InActive = ransomwareLeakSiteCount_InActive_,
                otherSiteCount = otherSiteCount_,
                tableBody = tableBody_,
                collaborateFolderLink = box_shareFolderLink,
                leaksiteURL = retOnionUrls)
            
    except Exception as e:
        # ログ
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))
        print(str(e))

    return ret

def createNotificationBody_Error(Errortext,subject):
    return """
            <html>
                <body>
                    <p style="color:green">！注意！監視システムでエラーが発生、停止しています：[ <br>"""+subject +"""</b> ]</p>
                    <p>""" + Errortext + """</p><br>
                </body>
            </html>"""

# 何も登録しない場合はFalseを返す→すでに登録済みの場合
# extraImportantInfo:MBK対応で追加。xxxx_NotifiedImportantInfo.jsonで登録済みだとMBKの重要ワードが無視される可能性があるので別ファイルにする
def registAsKnownImportantInfo(groupName, importantWordFile, str, extraImportantInfo = ''):
    ret = False

    extraImportantInfoTmp = ''
    if extraImportantInfo != '':
        extraImportantInfoTmp = '_' + extraImportantInfo

    # 重要通知済みリスト読み込み
    recordPath = os.path.join(cf.PATH_NOTIFIED_IMPORANT_INFO, '{}_NotifiedImportantInfo{}.csv'.format(groupName, extraImportantInfoTmp))
    notifiedRecordList = fo.Func_CSVReadist(recordPath)
    searchTarget = fo.Func_CSVReadist(importantWordFile)
 
    diffLines = str.splitlines()
    newRecordList = []
    for j in diffLines:
        noChkLine = False
        # +とか-は外す
        orgText = j[2:]

        # 差分の行が重要通知済みリストに登録されているかチェック
        if len(notifiedRecordList) > 0:
            chkRet =  [s for s in notifiedRecordList if s[0].lower() == orgText.lower()]
    
            if len(chkRet) > 0:
                noChkLine = True

        if noChkLine == False:
            for i in searchTarget:
                if len(i[0]) > 0 and i[0][0] != '#':
                    ret_findall = re.findall(i[0], orgText, re.IGNORECASE)
                    if len(ret_findall) > 0:
                        newRecordList.append([orgText])
                        # 何かしら見つかったらその行を登録
                        break

    if len(newRecordList) > 0:
        notifiedRecordList.extend(newRecordList)
        fo.Func_CSVWriteList(recordPath, notifiedRecordList)
        ret = True

    return ret
    
# 何も登録しない場合はFalseを返す→すでに登録済みの場合
# extraImportantInfo:MBK対応で追加。xxxx_NotifiedImportantInfo.jsonで登録済みだとMBKの重要ワードが無視される可能性があるので別ファイルにする
def registAsKnownImportantInfo_Dict(groupName, importantWordFile, dict, extraImportantInfo = ''):
    ret = False

    if len(dict) > 0:
        extraImportantInfoTmp = ''
        if extraImportantInfo != '':
            extraImportantInfoTmp = '_' + extraImportantInfo
            
        # 重要通知済みリスト読み込み
        recordPath = os.path.join(cf.PATH_NOTIFIED_IMPORANT_INFO, '{}_NotifiedImportantInfo{}.json'.format(groupName, extraImportantInfoTmp))
        notifiedRecordDic = fo.Func_ReadJson2Dict(recordPath)
        searchTarget = fo.Func_CSVReadist(importantWordFile)

        # ここで取得した文字列はメール作成時に使うのでDictionaryの便利なメソッドは使わずにfindallで検索
        for j in dict.keys():
            # すでに重要通知済みの情報ならスキップ
            noChkKey = False
            noChkUrl = False
            noChksummary = False

            if j in notifiedRecordDic.keys():
                noChkKey = True
                # url情報やサマリーが変わっている可能性もあるので完全一致する情報かチェック
                if dict[j]['url'] == notifiedRecordDic[j]['url']:
                    noChkUrl = True
                if dict[j]['summary'] == notifiedRecordDic[j]['summary']:
                    noChksummary = True

            if noChkKey == False or noChkUrl == False or noChksummary == False:
                for i in searchTarget:
                    if len(i[0]) > 0 and i[0][0] != '#':
                        ret_findall_Key = []
                        ret_findall_url = []
                        ret_findall_summary = []

                        # 重要単語が入ってるか
                        if noChkKey == False:
                            ret_findall_Key = re.findall(i[0], j, re.IGNORECASE)
                        if noChkUrl == False:
                            ret_findall_url = re.findall(i[0], dict[j]['url'], re.IGNORECASE)
                        if noChksummary == False:
                            ret_findall_summary = re.findall(i[0], dict[j]['summary'], re.IGNORECASE)

                        if len(ret_findall_Key) > 0 or len(ret_findall_url) > 0 or len(ret_findall_summary) > 0:
                            notifiedRecordDic[j] = {'url': dict[j]['url'], 'summary':dict[j]['summary']}
                            ret = True
                            break

    if ret:
        fo.Func_WriteDict2Json(recordPath, notifiedRecordDic)

    return ret

# def search_value(dictionary, target):
#     found_values = []
#     for value in dictionary.values():
#         if isinstance(value, dict):
#             found_values.extend(search_value(value, target))
#         elif isinstance(value, str) and target in value:
#             found_values.append(value)
#     return found_values

def search_value(dictionary, search_string):
    if isinstance(dictionary, dict):
        for key, value in dictionary.items():
            # キーに対するチェック
            if search_string.lower() in key.lower():
                return True
            # 値に対するチェック（ネストされた辞書を再帰的に調べる）
            if isinstance(value, dict):
                if search_value(value, search_string):
                    return True
            elif search_string.lower() in str(value).lower():
                return True
    return False

def check_include_word(word, Msgbody):
    common_english_words = ['Saudi Arabia']
    tempArray = fo.Func_CSVReadist(cf.IGNOREWORD_IFINCLUDED_LIST_PATH)
    common_english_words = [row[0] for row in tempArray]


    # 大文字小文字を区別しないため、全て小文字に変換
    word = word.lower()
    Msgbody = Msgbody.lower()
    local_common_english_words = set(word.lower() for word in common_english_words)

    pattern = word
    # 正規表現で検索
    for match in re.finditer(pattern, Msgbody):
        surrounding_str = Msgbody[max(0, match.start() - 8):min(len(Msgbody), match.end() + 8)]
        # 周囲に一般的な英単語が含まれているかチェック
        # local_common_english_words のいずれかの単語が surrounding_str 内に存在する場合、
        # この式は真（True）を返します。そうでない場合は偽（False）を返します。
        if any(common_word in surrounding_str for common_word in local_common_english_words):
            continue
        return True
    return False

# 単次元リストに未登録のアイテムのみ登録する
# @exception_tracker.trace_exceptions
# def append_case_insensitive(lst, item):
#     ret = False
#     # 既存のリストの要素を小文字に変換してチェック
#     if item.lower() not in [x.lower() for x in lst]:
#         lst.append(item)
#         ret = True
#     return ret

# def append_case_insensitive4List(lst, items):
#     # itemsが単一の文字列の場合はリストに変換
#     if isinstance(items, str):
#         items = [items]
    
#     for item in items:
#         # 既存のリストの要素を小文字に変換してチェック
#         if item.lower() not in [x.lower() for x in lst]:
#             lst.append(item)
#     return lst
# @exception_tracker.trace_exceptions

# 概要の文章を改行やピリオドでリストビューに分割する
def split_text(text):
    """
    Split text by newlines and periods, while preserving domains intact.
    
    Args:
        text (str): Input text to split
        
    Returns:
        list: List of text segments
    """
    # まず改行で分割
    lines = text.split('\n')
    
    result = []
    
    for line in lines:
        if not line.strip():  # 空行はスキップ
            continue
            
        # ドメインパターンを検出 (例: example.com, sub.example.co.jp など)
        domain_pattern = r'[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z]'
        
        # ドメインを一時的なプレースホルダーに置換
        domains = re.findall(domain_pattern, line)
        temp_line = line
        
        for i, domain in enumerate(domains):
            placeholder = f"DOMAIN_PLACEHOLDER_{i}"
            temp_line = temp_line.replace(domain, placeholder)
        
        # ピリオドで分割
        segments = temp_line.split('.')
        
        # プレースホルダーを元のドメインに戻す
        for i, segment in enumerate(segments):
            for j, domain in enumerate(domains):
                placeholder = f"DOMAIN_PLACEHOLDER_{j}"
                if placeholder in segment:
                    segments[i] = segment.replace(placeholder, domain)
        
        # 空白を除去し、結果に追加
        segments = [seg.strip() for seg in segments if seg.strip()]
        result.extend(segments)
    
    return result

def group_word_combinations(data):
    """
    重要な言葉と文章の組み合わせを整理する関数
    
    Args:
        data (list): 元のデータ配列
        
    Returns:
        list: 整理された組み合わせの配列
    """
    # 文章ごとに含まれる重要単語を収集
    sentence_words = {}
    for item in data:
        for sentence in item['found_at']:
            if sentence not in sentence_words:
                sentence_words[sentence] = set()
            sentence_words[sentence].add(item['word'][0])
    
    # 結果を格納する辞書（キーは文章のタプル）
    result_dict = {}
    
    # 文章ごとに処理
    for sentence, words in sentence_words.items():
        # 単語をソートしてタプルに変換
        words_key = tuple(sorted(words))
        
        # 結果辞書にキーが存在しない場合は新しいsetを作成
        if words_key not in result_dict:
            result_dict[words_key] = set()
        
        # 文章を追加
        result_dict[words_key].add(sentence)
    
    # 辞書から最終的な形式に変換
    result = []
    for words, sentences in result_dict.items():
        result.append({
            'word': list(words),
            'found_at': sorted(list(sentences))
        })
    
    return result

# 日本語判定入れる。
# 生成AIの調査結果（概要とか職種とか）をログとして登録する
def IsImportantInfo2(groupName, importantWordFile, targetDictArray = {}, extraImportantInfo = '', force = False, autoCheckJapanese = False):

    retHasImportantInfo = False
    retArray = []
    prevNotifiedRecordDicLen = 0
    try:

        if len(targetDictArray) > 0:
            extraImportantInfoTmp = ''
            if extraImportantInfo != '':
                extraImportantInfoTmp = '_' + extraImportantInfo
                
            # 重要通知済みリスト読み込み
            recordPath = os.path.join(cf.PATH_NOTIFIED_IMPORANT_INFO, '{}_NotifiedImportantInfo{}.json'.format(groupName, extraImportantInfoTmp))
            notifiedRecordDic = fo.Func_ReadJson2Dict(recordPath)
            prevNotifiedRecordDicLen = len(notifiedRecordDic)
            searchTarget = fo.Func_CSVReadist(importantWordFile)

            # ここで取得した文字列はメール作成時に使うのでDictionaryの便利なメソッドは使わずにfindallで検索
            for targetDicKey in targetDictArray.keys():
                victimsName = targetDicKey
                victimsUrl = targetDictArray[targetDicKey].get('url', '')
                victimsSummary = targetDictArray[targetDicKey].get('summary', '')

                isRegistered = False
                if victimsName in notifiedRecordDic.keys():
                    isRegistered = True

                if not isRegistered:
                    importantWordDicArrayTmp = []
                    for i in searchTarget:
                        searchPattern = i[0]
                        isRegExp = False

                        if len(searchPattern) > 0 and searchPattern[0] != '#':
                            if len(i) >= 3:
                                # 検知メールに表示する文言。正規表現をそのまま出したくないので。これがないと正規表現検索されない仕様にしておく
                                displayWord = i[2]
                                if uf.strstr('regexp', i[1]):
                                    isRegExp = True

                            # 重要単語が入ってるか
                            if isRegExp:
                                if (displayWordLst := re.findall(searchPattern, victimsName, re.IGNORECASE)):
                                    importantWordDicArrayTmp.append({'word':[displayWordLst[0]], 'found_at':[victimsName]})
                                elif (displayWordLst := re.findall(searchPattern, victimsUrl, re.IGNORECASE)):
                                    importantWordDicArrayTmp.append({'word':[displayWordLst[0]], 'found_at':[victimsUrl]})
                                else:
                                    sentenceArray = split_text(victimsSummary)
                                    for sentence in sentenceArray:
                                        if (displayWordLst := re.findall(searchPattern, sentence, re.IGNORECASE)):
                                            importantWordDicArrayTmp.append({'word':[displayWordLst[0]], 'found_at':[sentence]})
                            else:
                                # どれかで見つかった時点で重要単語なのでOR
                                if uf.strstr(searchPattern, victimsName):
                                    try:
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-victimsName:{victimsName}')
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-searchPattern:{searchPattern}')
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-importantWordFile:{importantWordFile}')
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-targetDictArray:{targetDictArray}')
                                    except:
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-LogEror')


                                    importantWordDicArrayTmp.append({'word':[searchPattern], 'found_at':[victimsName]})
                                elif uf.strstr(searchPattern, victimsUrl):
                                    try:
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-victimsName:{victimsName}')
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-searchPattern:{searchPattern}')
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-importantWordFile:{importantWordFile}')
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-targetDictArray:{targetDictArray}')
                                    except:
                                        Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-LogEror')

                                    importantWordDicArrayTmp.append({'word':[searchPattern], 'found_at':[victimsUrl]})

                                # 掲載された概要の場合は、改行コードやピリオドで分を区切り、一番最初に見つかった場所を登録する
                                else:
                                    sentenceArray = split_text(victimsSummary)
                                    for sentence in sentenceArray:
                                        if uf.strstr(searchPattern, sentence):
                                            try:
                                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-victimsName:{victimsName}')
                                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-searchPattern:{searchPattern}')
                                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-importantWordFile:{importantWordFile}')
                                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-targetDictArray:{targetDictArray}')
                                            except:
                                                Log.LoggingWithFormat(groupName, logCategory = 'I', logtext = f'重要ワード-LogEror')  

                                            importantWordDicArrayTmp.append({'word':[searchPattern], 'found_at':[sentence]})
                    
                    if len(importantWordDicArrayTmp) > 0:
                        importantInfoDict = {
                            'groupName':groupName,
                            'victimsName':victimsName,
                            'importantWords':[],
                        }
                        importantInfoDict['importantWords'] = group_word_combinations(importantWordDicArrayTmp)

                        retArray.append(importantInfoDict)
                        notifiedRecordDic[victimsName] = {'url': targetDictArray[victimsName]['url'], 'summary':targetDictArray[victimsName]['summary']}

            if prevNotifiedRecordDicLen < len(notifiedRecordDic):
                fo.Func_WriteDict2Json(recordPath, notifiedRecordDic)
                retHasImportantInfo = True
    except Exception as e:
        print(f'Exception:{str(e)}')

    return retHasImportantInfo, retArray

def hasJapaneseWord(groupName, targetDictArray = {}):
    retHasImportantInfo = False
    retArray = []

    if len(targetDictArray) > 0:
        # 日本語検知の対象は概要のみ。掲載組織名が日本関連かどうかについてはinevstigateVictimsInfoAI関数で調査済みのはず
        for targetDicKey in targetDictArray.keys():
            importantWordDicArrayTmp = []
            victimsName = targetDicKey
            victimsSummary = targetDictArray[targetDicKey].get('summary', '')

            # 日本語ならノータイムで重要情報。該当単語とかないのでそのままフラグだけ返す
            if cj.Check_JP_Language(victimsSummary):
                JPWordDic = {
                    'word': [],
                    'found_at': []
                }
                importantWordDicArrayTmp.append({'word':['文章全体が日本語の可能性'], 'found_at':['文章が日本語で構成されている可能性が高いです']})
            else:
                # 重要単語とちがい、生成AIに投げるので、いったん概要文書全てを投げる。単語が見つかったらその単語を含む文書を抜粋する
                JPWordByAIArray = cj.CheckJapaneseMain(victimsSummary, v2 = True)

                if len(JPWordByAIArray) > 0:
                    sentenceArray = split_text(victimsSummary)
                    for word in JPWordByAIArray:
                        for sentence in sentenceArray:
                            if uf.strstr(word, sentence):
                                importantWordDicArrayTmp.append({'word':[word], 'found_at':[sentence]})

            if len(importantWordDicArrayTmp) > 0:
                JPWordsInfoDict = {
                    'groupName':groupName,
                    'victimsName':victimsName,
                    'JPWords':[],
                }
                JPWordsInfoDict['JPWords'] = group_word_combinations(importantWordDicArrayTmp)
                retArray.append(JPWordsInfoDict)

    return retArray


# 一つの文字列に対して重要単語を検索するロジック
# extraImportantInfoはImportantWord_xxx.csvのxxxの部分
def IsImportantInfo(groupName, importantWordFile, str = '', newItemDict = {}, delItemDict = {}, extraImportantInfo = '', force = False, autoCheckJapanese = False):
    ret = False
    retStr = ''
    retIsDeletedOnly = False

    strTmp = ''
    isDict = False
    retStrTmp = []
    retList = []
    retStr_jp = ''
    retStrTmp_jp = []
    retList_jp = []
    retReplaceList = []
    retReplaceList_jp = []
    newItemDict_ = {}
    delItemDict_ = {}

    try:
        # 個別対応なし
        if len(str) > 0:
            strTmp = str
        # 個別対応あり
        elif len(newItemDict) > 0 or len(delItemDict) > 0:
            # 指定した要素以外を除外して新しいDictionary作成
            def create_dict_with_selected_elements(original, elements_to_keep):
                modified_dict = {}
                try:
                    for key, value in original.items():
                        modified_dict[key] = {k: v for k, v in value.items() if k in elements_to_keep}
                except Exception as e:
                    err = 'err create_dict_with_selected_elements'

                return modified_dict 

            # 保持したい要素
            elements_to_keep = ['url', 'summary']
            newItemDict_ = create_dict_with_selected_elements(newItemDict, elements_to_keep)
            delItemDict_ = create_dict_with_selected_elements(delItemDict, elements_to_keep)
            isDict = True
            # 追加削除のDictionaryをまとめて重要単語検索にかけるため結合
            dictTmp = dict(**newItemDict_, **delItemDict_)
            strTmp = uf.Dict2String(dictTmp)

        if len(strTmp) > 0:
            # いったん重要単語があるかチェック
            searchTarget = fo.Func_CSVReadist(importantWordFile)
            ret_findall = []
            for targetWord in searchTarget:
                ret_findall.clear()
                useRegExp = False

                if len(targetWord)> 1 and len(targetWord[1]) > 0:
                    if uf.strstr('regexp', targetWord[1]):
                        useRegExp = True
                if len(targetWord[0]) > 0 and targetWord[0][0] != '#':
                    # ３文字以下の重要単語なら記号がくっついていることを考慮する「NHK-」など
                    isThreeLetterChk = True
                    if len(targetWord[0]) <= 3:
                        pattern = r'\b["(]*' + re.escape(targetWord[0]) + r'["\)\-_]*|_.*?\b'
                        if re.search(pattern, strTmp, re.IGNORECASE):
                            isThreeLetterChk = True
                        else:
                            isThreeLetterChk = False

                    if isThreeLetterChk:
                        if useRegExp:
                            # Jsonキーに[.jp]があってもJsonを文字列にならしてから探しちゃってるから
                            # 見つかるのが[.jp"]になってしまい、下のほうの追加差分に存在するかチェックで存在しない判定になっちゃう。
                            # （その判定はちゃんとDictionaryのキー、値を見ており、こっちとチェック方法が違うので）
                            # なので末尾が"のものが見つかったら消す。幸い重要ワードに"が入るものはない
                            # あくまでも応急処置なので時間があるときにちゃんとDictionaryのキー、値をそれぞれ見るように修正する
                            ret_findall_Tmp = re.findall(targetWord[0], strTmp, re.IGNORECASE)
                            ret_findall = []
                            for i in ret_findall_Tmp:
                                strReplace = i
                                if strReplace.endswith('"'):
                                    strReplace = strReplace.replace(i[len(i)-1], '')

                                ret_findall.append(strReplace)
                        else:
                            pattern = escapeRegexpChar(targetWord[0])
                            ret_findall = re.findall(pattern, strTmp, re.IGNORECASE)

                if len(ret_findall) > 0:
                    # 重複排除
                    tmpArray = ret_findall.copy()
                    tmpArray = set(tmpArray)
                    ret_findall.clear()
                    for word in tmpArray:
                        if check_include_word(word, strTmp): 
                            ret_findall.append(word)

                    if len(ret_findall) > 0:
                        retStrTmp.extend(ret_findall)

            # 重要単語が見つかった場合、行やDictionaryの要素ごとに既知リストに登録したいので再度回す
            registeredSuccess = False
        
            if len(retStrTmp) > 0:
                # 重複排除
                retStrTmp = list(dict.fromkeys(retStrTmp))

                if force == False:
                    if isDict:
                        dictTmp = dict(**newItemDict, **delItemDict)
                        registeredSuccess = registAsKnownImportantInfo_Dict(groupName, importantWordFile, dictTmp, extraImportantInfo)
                    else:
                        registeredSuccess = registAsKnownImportantInfo(groupName, importantWordFile, str, extraImportantInfo)
                else:
                    # forceがTrueのときはすでに通知済み重要単語として登録済み(二回目以降無視するリスト)であっても重要としてあつかう
                    # というか登録すらしない
                    registeredSuccess = True

            # 日本語が含まれているか判定
            if autoCheckJapanese == True:
                text = ''
                if isDict:
                    # dictArray = [newItemDict_, delItemDict_]
                    # 日本語検知は追加分だけやれば十分
                    dictArray = [newItemDict_]
                    for dict_ in dictArray:
                        for key in dict_.keys():
                            victimsName = key
                            summary = dict_[key]['summary']
                            text = victimsName + '\n\n' + summary

                            # 日本語ならノータイムで重要情報。該当単語とかないのでそのままフラグだけ返す
                            if cj.Check_JP_Language(text):
                                registeredSuccess = True
                            else:
                                retArray = cj.CheckJapaneseMain(text)

                                if len(retArray) > 0:
                                    retStrTmp_jp.extend(retArray)

                    if len(retStrTmp_jp) > 0:
                        # 生成AIの結果なので登録しないけど戻り値のためにフラグ立てる
                        registeredSuccess = True
                else:
                    # 日本語ならノータイムで重要情報。該当単語とかないのでそのままフラグだけ返す
                    if cj.Check_JP_Language(str):
                        registeredSuccess = True
                    else:
                        retArray = cj.CheckJapaneseMain(str)

                        if len(retArray) > 0:
                            # 生成AIの結果なので登録しないけど戻り値のためにフラグ立てる
                            registeredSuccess = True
                            retStrTmp_jp.extend(retArray)

            if registeredSuccess:
                # 重要単語が削除差分にしか存在しないのか確認
                if isDict:
                    if len(retStrTmp) > 0:
                        # 削除Dicにしかない場合注意書きをメールに書きたい
                        hasImportantWord = False
                        for i in retStrTmp:
                            hasImportantWord = search_value(newItemDict_, i)
                            if hasImportantWord:
                                break

                        if hasImportantWord == False:
                            retIsDeletedOnly = True
                    
                    if retIsDeletedOnly == False and len(retStrTmp_jp) > 0:
                        hasImportantWord = False
                        for i in retStrTmp_jp:
                            hasImportantWord = search_value(newItemDict_, i)
                            if hasImportantWord:
                                break

                        if hasImportantWord == False:
                            retIsDeletedOnly = True
                else:
                    retIsDeletedOnly = True
                    lineArray = str.splitlines()
                    for i in retStrTmp:
                        for line in lineArray:
                            if line.startswith('+ '):
                                ret_findall = re.findall(i, line, re.IGNORECASE)

                                if len(ret_findall) > 0:
                                    retIsDeletedOnly = False
                                    break
                        if retIsDeletedOnly == False:
                            break

                    if retIsDeletedOnly == False and len(retStrTmp_jp) > 0:
                        lineArray = str.splitlines()
                        for i in retStrTmp_jp:
                            for line in lineArray:
                                if line.startswith('+ '):
                                    ret_findall = re.findall(i, line, re.IGNORECASE)

                                    if len(ret_findall) > 0:
                                        retIsDeletedOnly = False
                                        break
                            if retIsDeletedOnly == False:
                                break
                    
                # ハイライト処理用のリスト。大文字小文字を区別せず重複排除するとハイライト処理でもともと大文字だったものが小文字になるので
                if len(retStrTmp) > 0:
                    retReplaceList = list(set(retStrTmp))
                    n_retStrTmp = []

                    for i in retReplaceList:
                        n_retStrTmp.append(i.lower())

                    # uniquie = set(n_retStrTmp)
                    retStr =','.join(n_retStrTmp)
                    retList = n_retStrTmp.copy()

                if len(retStrTmp_jp) > 0:
                    retReplaceList_jp_Tmp = list(set(retStrTmp_jp))

                    # 重要単語側にあるようなら日本語検知からは消す
                    if len(retStrTmp) > 0:

                        for item in retReplaceList_jp_Tmp:
                            is_in_list = any(item.lower() in element for element in retList)

                            if is_in_list == False:
                                retReplaceList_jp.append(item)
                                break
                    else:
                        retReplaceList_jp = retReplaceList_jp_Tmp

                    n_retStrTmp = []
                    for i in retReplaceList_jp:
                        n_retStrTmp.append(i.lower())

                    # uniquie = set(n_retStrTmp)
                    retStr_jp =','.join(n_retStrTmp)
                    retList_jp = n_retStrTmp.copy()

                ret = True
            else:
                ret = False
                retStr = ''
                retList = []
                retReplaceList = []
                retIsDeletedOnly = False
                retStr_jp = ''
                retList_jp = []
                retReplaceList_jp = []
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = {str(e.args)})

    return ret, retStr, retList, retIsDeletedOnly, retReplaceList, retStr_jp, retList_jp, retReplaceList_jp

# stmp_user = 'iroiromonitaro1v2@gmail.com'
# stmp_password = 'drjvrclblfhzqxde'        
# stmp_user = 'iroiromonitaro1v2.2@gmail.com'
# stmp_password = 'ndzn vapx iyha eqch'    
stmp_user = 'iroiromonitaro1v2.3@gmail.com'
stmp_password = 'lppq gwwo ajvd kyzc'

stmp_user_v4 = 'iroiromonitaro1v2.4@gmail.com'
stmp_password_v4 = 'pnvy rvun ozbm myjf'

def sendMail_google(groupName, gmailUser, gmilAppPassword, stmp_server, stmp_port, from_address, send_address, msg):
    try:
        isSuccess = False
        s = smtplib.SMTP(stmp_server, stmp_port)
        s.starttls()
        retLogtin = s.login(gmailUser, gmilAppPassword)
        retSend = s.sendmail(from_address, send_address, msg.as_string())
        s.quit()

        isSuccess = True
    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = {str(e)})

    return isSuccess
    
def sendMail(body, subject, sendTo, insertImgBefore = '', insertImgAfter = '', insertImgDiff = '', isUrgent = False, newItems = {}, groupName = 'System', attatchImage = False ):
    isSuccess = False
    try:
        stmp_server = "smtp.gmail.com"
        stmp_port = 587
        from_address = stmp_user
        send_address = sendTo

        msg = MIMEMultipart('related')
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = from_address

        msg.attach(MIMEText(body, "html"))

        if isUrgent == True:
            msg["X-Priority"] = '1'

        # 新バージョンでは画像を挿入してないのでいったんコメント2024/12/11
        # → TargetUrls.jsonに"attatchImage"をセットすることで添付できるようにする。主に個別監視
        if attatchImage:
            if os.path.exists(insertImgBefore) and os.path.exists(insertImgAfter) and os.path.exists(insertImgDiff):
                with open(insertImgBefore, 'rb') as fp:
                    msgImage= MIMEImage(fp.read())
                    msgImage.add_header('Content-ID', '<image1>')
                    msg.attach(msgImage)

                with open(insertImgAfter, 'rb') as fp:
                    msgImage= MIMEImage(fp.read())
                    msgImage.add_header('Content-ID', '<image2>')
                    msg.attach(msgImage)

                with open(insertImgDiff, 'rb') as fp:
                    msgImage= MIMEImage(fp.read())
                    msgImage.add_header('Content-ID', '<image3>')
                    msg.attach(msgImage)
            
            try:
                # 詳細ページのスクショ対応してあったら挿入していく
                if len(newItems) > 0:
                    for key in newItems.keys():
                        detailScreenshot = newItems[key].get('detailScreenshot', '')
                        if detailScreenshot != '':
                            with open(detailScreenshot, 'rb') as fp:
                                detailScreenshotImgNo = newItems[key].get('detailScreenshotImgNo', 0)
                                
                                msgImage= MIMEImage(fp.read())
                                msgImage.add_header('Content-ID', '<image{}>'.format(detailScreenshotImgNo))
                                msg.attach(msgImage)

            except Exception as e:
                Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = {str(e)})

        try:
            isSuccess = sendMail_google(groupName, stmp_user, stmp_password, stmp_server, stmp_port, from_address, send_address, msg)
        except:
            isSuccess = sendMail_google(groupName, stmp_user_v4, stmp_password_v4, stmp_server, stmp_port, from_address, send_address, msg)

        # s = smtplib.SMTP(stmp_server, stmp_port)
        # s.starttls()
        # retLogtin = s.login(stmp_user, stmp_password)
        # retSend = s.sendmail(from_address, send_address, msg.as_string())
        # s.quit()
        # isSuccess = True

    except Exception as e:
        Log.LoggingWithFormat(groupName, logCategory = 'E', logtext = {str(e)})

    return isSuccess

def sendMail_Nofication(bodyText, subject, sendTo, isUrgent = True):
    retSuccess = False
    try:
        stmp_server = "smtp.gmail.com"
        stmp_port = 587
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

        try:
            retSuccess = sendMail_google('SendReportError', stmp_user, stmp_password, stmp_server, stmp_port, from_address, send_address, msg)
        except:
            retSuccess = sendMail_google('SendReportError', stmp_user_v4, stmp_password_v4, stmp_server, stmp_port, from_address, send_address, msg)
        # s = smtplib.SMTP(stmp_server, stmp_port)
        # s.starttls()
        # retLogtin = s.login(stmp_user, stmp_password)
        # retSend = s.sendmail(from_address, send_address, msg.as_string())
        # s.quit()
        # retSuccess = True

    except Exception as e:
        Log.LoggingWithFormat('SendReportError', logCategory = 'E', logtext = {str(e)})

    return retSuccess

# ----------------------------------------------------------------------------------------------------
def remove_case_insensitive_duplicates(arr):
    # 大文字小文字を無視して一意の値を保持する辞書
    seen = {}
    # 結果を格納する配列
    result = []
    
    for item in arr:
        # 小文字に変換して比較
        lower_item = item.lower()
        # まだ見ていない項目の場合、元の形式で保存
        if lower_item not in seen:
            seen[lower_item] = True
            result.append(item)
    
    return result

def ConvertVictimsData2MailBodyData(groupName,
                                    newItems,
                                    deletedItems,
                                    importantWordsList,
                                    urgentMailInfo,
                                    importantWordsList_jp,
                                    uploadUrl,
 
):
    retData = {}
    retUrgentFlg = False

    if len(newItems) > 0:
        retData['added_orgs'] = []
        retData['added_orgs_summary'] = []
        retData['important_info'] = {}
        retData['screenShotHome'] = uploadUrl
        announcementByAIArray = []
        japanRelatedOrganizations_VicList = []

        for key in newItems.keys():
            # AIによる調査結果をパース1
            victimsDicByAI = newItems[key].get('aiInvestigatement', {})

            victimNameByAI = victimsDicByAI.get('victimName', '不明')
            victimBizTypeByAI = victimsDicByAI.get('victimBizType', '不明')
            victimHQLocationByAI = victimsDicByAI.get('victimHQLocation', '不明')
            victimUrlByAI = victimsDicByAI.get('victimUrl', '不明')
            announcementByAI = victimsDicByAI.get('announcement', '')
            victimsRelationJPByAI = victimsDicByAI.get('victimsRelationJP', '')

            if victimsRelationJPByAI:
                japanRelatedOrganizations_VicList.append(key)
            else:
                victimsRelationJPByAI = '不明'

            tempDic = {}
            tempDic['victimName'] = key
            tempDic['url'] = newItems[key]['url']
            tempDic['updateDate'] = newItems[key]['updateDate']
            tempDic['detectedDate'] = newItems[key]['detectedDate']
            tempDic['screenshot_url'] = newItems[key].get('screenShotUrl','掲載組織別のページが存在しない、もしくはスクリーンショット取得失敗')
            tempDic['victimNameAI'] = victimNameByAI.replace('\n', '<br>')
            tempDic['victimHQLocation'] = victimHQLocationByAI.replace('\n', '<br>')
            tempDic['victimBizType'] = victimBizTypeByAI.replace('\n', '<br>')
            tempDic['victimUrlAI'] = victimUrlByAI.replace('\n', '<br>')
            tempDic['victimsRelationJPByAI'] = victimsRelationJPByAI.replace('\n', '<br>')
            if announcementByAI:
                tempDic['annoucementAI'] = announcementByAI
            
            tempDicsummary = {}

            tempDicsummary['victimName'] = f'{key}'
            tempDicsummary['victimNameAI'] = f"{victimNameByAI}"
            tempDicsummary['victimHQLocation'] = f'{victimHQLocationByAI}'
            tempDicsummary['victimBizType'] = f'{victimBizTypeByAI}'

            retData['added_orgs'].append(tempDic)
            retData['added_orgs_summary'].append(tempDicsummary)

            if announcementByAI:
                announcementByAIArray.append(key)

        # 犯行声明の可能性
        if len(announcementByAIArray) > 0:
            retData['important_info']['ai_text_announcement'] = []
            retData['important_info']['ai_text_announcement'] = announcementByAIArray  

    if len(deletedItems) > 0:
        retData['deleted_orgs'] = []
        for key in deletedItems.keys():
            tempDic = {}
            tempDic['victimName'] = key
            tempDic['url'] = deletedItems[key]['url']
            tempDic['updateDate'] = deletedItems[key]['updateDate']
            tempDic['detectedDate'] = deletedItems[key]['detectedDate']

            retData['deleted_orgs'].append(tempDic)

    # 重要単語
    if len(importantWordsList) > 0:
        retData['important_info']['importantWordsInfo'] = importantWordsList
        # retData['important_info']['keywords'] = remove_case_insensitive_duplicates(importantWordsList)
        retUrgentFlg = True

    # 日本関連組織の可能性
    if len(japanRelatedOrganizations_VicList) > 0:
        if victimsRelationJPByAI.startswith('あり'):
            retData['important_info']['ai_RelationJP'] = []
            retData['important_info']['ai_RelationJP'] = japanRelatedOrganizations_VicList

            retUrgentFlg = True

    # AIによる日本語検知
    if len(importantWordsList_jp) > 0:
        retData['important_info']['japanese_wordsByAI'] = importantWordsList_jp  
        retUrgentFlg = True

    # 指定された個別情報が更新
    flg = urgentMailInfo.get('urgent_UserSpecified', False)
    if flg:
        retData['important_info']['urgent_UserSpecified'] = flg
        retUrgentFlg = True

    # サイト構成変更の可能性
    flg = urgentMailInfo.get('changedHTMLStructure', False)
    if flg:
        retData['important_info']['changedHTMLStructure'] = flg
        retUrgentFlg = True

    # サイト接続不可/接続可に変更
    flg = urgentMailInfo.get('isSiteChange2Unavailable', False)
    if flg:
        retData['important_info']['isSiteChange2Unavailable'] = flg
        retUrgentFlg = True
    else:
        flg = urgentMailInfo.get('isSiteChange2Available', False)
        if flg:
            retData['important_info']['isSiteChange2Available'] = flg
            retUrgentFlg = True

    return retData, retUrgentFlg


def CreateNotificationMailBody(data):
    from jinja2 import Template, Environment
    from collections import defaultdict
    import json

    def highlight_words(text, word_list):
        """テキスト内の複数の単語を赤い太字で強調表示する"""
        if not word_list or not text:
            return text
        
        # リストでない場合はリストに変換
        if isinstance(word_list, str):
            word_list = [word_list]
        
        import re
        result = text
        for word in word_list:
            if word:
                pattern = re.compile(r'(' + re.escape(word) + r')', re.IGNORECASE)
                result = pattern.sub(r'<span style="color: red; font-weight: bold;">\1</span>', result)
        return result

    def group_word_info(group):
        """同じワードの検知箇所をまとめる"""
        word_groups = defaultdict(list)
        for word_info in group.get('importantWords', []):
            word_groups[word_info['word']].extend(word_info.get('found_at', []))
        return dict(word_groups)

    def to_json(value):
        """値をJSON文字列に変換するフィルター"""
        return json.dumps(value, ensure_ascii=False, indent=2)

    def defang_text(text):
        """URLやその他の文字列をデファングする"""
        if not text:
            return text

        # # スクリーンショットURLの場合はデファングしない
        # if 'screenshot_url' in text:
        #     return text
    
        # 文字列型でない場合は文字列に変換
        if not isinstance(text, str):
            text = str(text)
        
        # 置換ルール
        replacements = {
            'http': 'hxxp',
            '://': '[://]',
            '.': '[.]',
            '@': '[at]'
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result

    # フィルターを追加
    env = Environment()
    env.filters['highlight_words'] = highlight_words
    env.filters['group_word_info'] = group_word_info
    env.filters['to_json'] = to_json
    env.filters['defang'] = defang_text

    html_template = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>監視レポート</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 20px;
                background-color: #f0f2f5;
            }
            .container {
                border: 1px solid #ccc;
                padding: 20px;
                border-radius: 12px;
                background-color: #ffffff;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            .important-info {
                background-color: #ffcccc;
                padding: 2px;
                border-radius: 0 0 8px 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .important-info strong {
                display: block;
                margin-bottom: 4px;
                font-size: 0.95em;
            }
            .important-info .announcement-note {
                font-size: 0.7em;
                display: block;
                margin-top: -4px;
                margin-bottom: 4px;
            }
            .important-info .beta-note {
                font-size: 0.7em;
                display: block;
                margin-top: -4px;
                margin-bottom: 4px;
                color: #666;
            }
            .important-info-section {
                padding: 8px 12px;
                margin: 2px;
                border-radius: 6px;
                border-left: 4px solid #ff6666;
                background-color: #fff0f0;
            }
            .important-info-content {
                margin-left: 8px;
                font-size: 0.9em;
            }
            .summary-content {
                background-color: #ffefc5;
                padding: 15px;
                border-radius: 0 0 8px 8px;
                margin-bottom: 20px;
            }
            .info-section {
                margin-bottom: 20px;
            }
            .info-card {
                background-color: #ffffff;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin-bottom: 15px;
                border-left: 5px solid;
            }
            .info-card.added {
                border-left-color: #66b266;
                background-color: #f0fff0;
            }
            .info-card.deleted {
                border-left-color: #696969;
                background-color: #e0e0e0;
            }
            .info-header {
                color: #ffffff;
                padding: 10px;
                border-radius: 8px 8px 0 0;
                font-weight: bold;
                font-size: 1.1em;
            }
            .info-header.alert {
                background-color: #ff6666;
            }
            .info-header.summary {
                background-color: #ffaa00;
            }
            .info-header.added {
                background-color: #66b266;
            }
            .info-header.deleted {
                background-color: #696969;
            }
            .info-body {
                padding: 15px;
            }
            .info-body strong {
                font-weight: bold;
            }
            .info-card.deleted .info-body {
                color: #444;
            }
            .info-card.deleted a {
                color: #0066cc;
            }
            a {
                color: #0073e6;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .word-detection-card {
                border: 1px solid #eee;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                background-color: #fff;
                overflow: hidden;
            }
            .word-detection-header {
                background-color: #f8f9fa;
                padding: 12px 16px;
                border-bottom: 1px solid #eee;
            }
            .word-detection-header h3 {
                margin: 0;
                color: #333;
                font-size: 1.1em;
            }
            .word-detection-section {
                padding: 16px;
                border-bottom: 1px solid #eee;
            }
            .word-detection-section:last-child {
                border-bottom: none;
            }
            .word-label {
                display: inline-block;
                background-color: #e9ecef;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.95em;
                color: #495057;
                margin-bottom: 8px;
            }
            .locations-container {
                margin-left: 16px;
            }
            .location-title {
                font-size: 0.9em;
                color: #666;
                margin-bottom: 8px;
            }
            .detection-location {
                background-color: #f8f9fa;
                padding: 8px 12px;
                border-radius: 4px;
                margin-bottom: 8px;
                font-size: 0.95em;
                border: 1px solid #eee;
            }
            .detection-location:last-child {
                margin-bottom: 0;
            }
            .note-text {
                font-size: 0.85em;
                color: #666;
                margin-top: 12px;
                padding: 0 8px;
            }

            .note-text-alignRigit {
                font-size: 0.85em;
                color: #666;
                margin-top: 12px;
                padding: 0 8px;
                text-align: right;
            }

            .note-text-deleted {
                color: #ffffff !important; /* 親要素のcolor指定を確実に上書き */
                font-size: 0.85em !important;
                margin-top: 12px !important;
                padding: 0 8px !important;
            }

            .deleted-orgs-list {
                margin: 10px 0;
                padding-left: 20px;
            }
            
            .deleted-orgs-list li {
                margin-bottom: 4px;
            }

            .summary-table {
                width: 100%;
                table-layout: fixed;
                border-collapse: separate;
                border-spacing: 0;
                margin: 10px 0;
                background: #fff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            .summary-table th,
            .summary-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .summary-table th:nth-child(1),
            .summary-table td:nth-child(1) {
                width: 400px;
            }
            .summary-table th:nth-child(2),
            .summary-table td:nth-child(2) {
                width: 200px;
            }
            .summary-table th:nth-child(3),
            .summary-table td:nth-child(3) {
                width: 150px;
            }
            .summary-table th:nth-child(4),
            .summary-table td:nth-child(4) {
                width: auto;
            }
            .summary-table td.org-name {
                font-weight: 500;
                color: #333;
            }
            .summary-table td:hover {
                position: relative;
            }
            .summary-table td:hover::after {
                content: attr(title);
                position: absolute;
                left: 0;
                top: 100%;
                background: #333;
                color: #fff;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.9em;
                z-index: 1000;
                white-space: normal;
                max-width: 300px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .table-container {
                margin: 15px 0;
                border-radius: 8px;
                overflow: auto;
            }
            .separator {
                width: 100%;
                height: 1px;
                background-color: #aaa;
                margin: 12px 0;
                opacity: 0.85;
            }
            .important-info .separator {
                background-color: #ff8080;
                margin: 8px 0;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="info-section">
                <div class="note-text-alignRigit">詳細は本メールの「検知した企業情報」を参照してください。</div>
                <div class="info-header summary">概要</div>
                <div class="summary-content">
                    <strong>今回検知した企業 (合計: {{added_orgs_TotalCount}} 件中 {{ added_orgs|length if added_orgs else 0 }} 件を記載):</strong>
                    {% if totalMailCount > 1 %}
                        <div class="note-text">※検知件数が多いため、分割してメールが送られます。(現在 {{currentMailCount}} 通目 / 合計 {{totalMailCount}} 通)</div>
                    {% endif %}
                    {% if analyzeSummaryByAI %}
                    <div style="margin: 10px 0; padding: 10px; background-color: #f5f5f5; border-left: 4px solid #ffaa00; border-radius: 4px;">
                        {{ analyzeSummaryByAI|defang }}
                    </div>
                    {% endif %}
                    {% if added_orgs_summary %}
                    <div class="table-container">
                        <table class="summary-table">
                            <thead>
                                <tr>
                                    <th>掲載名</th>
                                    <th>組織名 (AI調査)</th>
                                    <th>国 (AI調査)</th>
                                    <th>業種 (AI調査)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for org in added_orgs_summary %}
                                <tr>
                                    <td class="org-name" title="{{ org.victimName|defang }}">{{ org.victimName|defang }}</td>
                                    <td class="org-name" title="{{ org.victimNameAI|defang }}">{{ org.victimNameAI|defang }}</td>
                                    <td class="location" title="{{ org.victimHQLocation|defang }}">{{ org.victimHQLocation|defang }}</td>
                                    <td class="business-type" title="{{ org.victimBizType|defang }}">{{ org.victimBizType|defang }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                    
                    {% else %}
                    <br>- 該当なし<br>
                    {% endif %}

                    {% if deleted_orgs %}
                    <strong>今回削除された企業 {{ deleted_orgs|length if deleted_orgs else 0 }} 件:</strong><br>
                    <ul class="deleted-orgs-list">
                        {% for org in deleted_orgs[:5] %}
                        <li>{{ org.victimName|defang }}</li>
                        {% endfor %}
                        {% if deleted_orgs|length > 5 %}
                        <li>＋ 他 {{ deleted_orgs|length - 5 }} 件</li>
                        {% endif %}
                    </ul>
                    {% endif %}

                    <strong>フルスクリーンショット (トップページ):</strong> 
                    {% if screenShotHome and screenShotHome.startswith('http') %}
                        <a href="{{ screenShotHome }}" target="_blank">フルスクリーンショットを表示</a>
                    {% else %}
                        スクリーンショット取得失敗
                    {% endif %}

                    <div class="note-text-alignRigit" align=”right”>検知日時 (前回日時: [{{detectedTimePrev}}]・今回日時: [{{detectedTimeNow}}]・差分時間: [{{diffDetectedTime}}])</div>
                </div>
            </div>
            
            {% if important_info %}
            <div class="info-section">
                <div class="info-header alert">重要情報</div>
                <div class="important-info">
                    {% if important_info.ai_RelationJP %}
                    <div class="important-info-section">
                        <strong>(生成AI調査) 日本に関係する組織が含まれている可能性があります。</strong>
                        <div class="important-info-content">
                            ■対象：{{ important_info.ai_RelationJP|join('、')|defang }}
                        </div>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.changedHTMLStructure %}
                    <div class="important-info-section">
                        <strong>(サイト構成)サイト構成が変更された可能性があります。</strong>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.isSiteChange2Unavailable %}
                    <div class="important-info-section">
                        <strong>(サイト接続)サイトに接続できなくなった可能性があります。</strong>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.isSiteChange2Available %}
                    <div class="important-info-section">
                        <strong>(サイト接続)サイトに接続できるようになった可能性があります。</strong>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.urgent_UserSpecified %}
                    <div class="important-info-section">
                        <strong>(指定情報更新-個別)指定された個別情報が更新された可能性があります。</strong>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.ai_text_announcement %}
                    <div class="important-info-section">
                        <strong>(生成AI調査) 組織名に文章等が含まれている可能性があります。</strong>
                        <strong class="announcement-note">※攻撃グループによるアナウンスなどと判断された可能性</strong>
                        <div class="important-info-content">
                            ■対象：{{ important_info.ai_text_announcement|join('、')|defang }}
                        </div>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.japanese_wordsByAI %}
                    <div class="important-info-section">
                        <strong>(生成AI検知)以下の言葉が日本語の可能性有と判断されました。</strong>
                        {% for group in important_info.japanese_wordsByAI %}
                            <div class="word-detection-card">
                                <div class="word-detection-header">
                                    <h3>掲載組織: {{ group.victimsName|defang }}</h3>
                                </div>

                                {% set location_word_map = {} %}
                                {% for word_info in group.importantWords %}
                                    {% for word in word_info.word %}
                                        {% for location in word_info.found_at %}
                                            {% if location_word_map[location] is not defined %}
                                                {% set _ = location_word_map.update({location: []}) %}
                                            {% endif %}
                                            {% if word not in location_word_map[location] %}
                                                {% set _ = location_word_map[location].append(word) %}
                                            {% endif %}
                                        {% endfor %}
                                    {% endfor %}
                                {% endfor %}

                                {% set word_location_map = {} %}
                                {% for location, words in location_word_map.items() %}
                                    {% set unique_words = words | unique | list %}
                                    {% if unique_words | length == 1 %}
                                        {% set word = unique_words[0] %}
                                        {% if word_location_map[word] is not defined %}
                                            {% set _ = word_location_map.update({word: []}) %}
                                        {% endif %}
                                        {% set _ = word_location_map[word].append(location) %}
                                    {% else %}
                                        <div class="word-detection-section">
                                            <div class="word-label">
                                                検知ワード: {{ unique_words|join(' / ')|defang }}
                                            </div>
                                            <div class="locations-container">
                                                <div class="location-title">該当箇所:</div>
                                                <div class="detection-location">
                                                    {% for word in unique_words %}
                                                        {{ location|highlight_words(word)|safe|defang }}
                                                    {% endfor %}
                                                </div>
                                            </div>
                                        </div>
                                    {% endif %}
                                {% endfor %}

                                {% for word, locations in word_location_map.items() %}
                                    <div class="word-detection-section">
                                        <div class="word-label">
                                            検知ワード: {{ word|defang }}
                                        </div>
                                        <div class="locations-container">
                                            <div class="location-title">該当箇所:</div>
                                            {% for location in locations %}
                                                <div class="detection-location">
                                                    {{ location|highlight_words(word)|safe|defang }}
                                                </div>
                                            {% endfor %}
                                        </div>
                                    </div>
                                {% endfor %}
                            </div>
                        {% endfor %}
                        <div class="note-text">※上記、"該当箇所"のうち一部情報は仕様上、本メールに記載していないことにご留意ください。</div>
                    </div>
                    <div class="separator"></div>
                    {% endif %}

                    {% if important_info.importantWordsInfo %}
                    <div class="important-info-section">
                        <strong>(重要ワード) 以下のワードは重要な情報の可能性があります。</strong>
                        {% for group in important_info.importantWordsInfo %}
                            <div class="word-detection-card">
                                <div class="word-detection-header">
                                    <h3>掲載組織: {{ group.victimsName|defang }}</h3>
                                </div>

                                {% set location_word_map = {} %}
                                {% for word_info in group.importantWords %}
                                    {% for word in word_info.word %}
                                        {% for location in word_info.found_at %}
                                            {% if location_word_map[location] is not defined %}
                                                {% set _ = location_word_map.update({location: []}) %}
                                            {% endif %}
                                            {% if word not in location_word_map[location] %}
                                                {% set _ = location_word_map[location].append(word) %}
                                            {% endif %}
                                        {% endfor %}
                                    {% endfor %}
                                {% endfor %}

                                {% set word_location_map = {} %}
                                {% for location, words in location_word_map.items() %}
                                    {% set unique_words = words | unique | list %}
                                    {% if unique_words | length == 1 %}
                                        {% set word = unique_words[0] %}
                                        {% if word_location_map[word] is not defined %}
                                            {% set _ = word_location_map.update({word: []}) %}
                                        {% endif %}
                                        {% set _ = word_location_map[word].append(location) %}
                                    {% else %}
                                        <div class="word-detection-section">
                                            <div class="word-label">
                                                検知ワード: {{ unique_words|join(' / ')|defang }}
                                            </div>
                                            <div class="locations-container">
                                                <div class="location-title">該当箇所:</div>
                                                <div class="detection-location">
                                                    {% for word in unique_words %}
                                                        {{ location|highlight_words(word)|safe|defang }}
                                                    {% endfor %}
                                                </div>
                                            </div>
                                        </div>
                                    {% endif %}
                                {% endfor %}

                                {% for word, locations in word_location_map.items() %}
                                    <div class="word-detection-section">
                                        <div class="word-label">
                                            検知ワード: {{ word|defang }}
                                        </div>
                                        <div class="locations-container">
                                            <div class="location-title">該当箇所:</div>
                                            {% for location in locations %}
                                                <div class="detection-location">
                                                    {{ location|highlight_words(word)|safe|defang }}
                                                </div>
                                            {% endfor %}
                                        </div>
                                    </div>
                                {% endfor %}
                            </div>
                        {% endfor %}
                        <div class="note-text">※上記、"該当箇所"のうち一部情報は仕様上、本メールに記載していないことにご留意ください。</div>
                    </div>
                    <div class="separator"></div>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            <!-- 追加された企業情報一覧 -->
            {% if added_orgs %}
            <div class="info-section">
                <div class="info-header added">検知した企業情報</div>
                {% for org in added_orgs %}
                <div class="info-card added">
                    <div class="info-body">
                        <strong>掲載組織名:</strong>{{ org.victimName|defang }}<br>
                        <strong>掲載されたURL:</strong>{{ org.url|defang }}<br>
                        <strong>更新日時 (公開予定日時含):</strong> {{ org.updateDate|defang }}<br>
                        <strong>検知日時 (システムの初情報取得日時):</strong> {{ org.detectedDate|defang }}<br>
                        <strong>フルスクリーンショット (詳細ページ):</strong> 
                        {% if org.screenshot_url and org.screenshot_url.startswith('http') %}
                            <a href="{{ org.screenshot_url }}" target="_blank">フルスクリーンショットを表示</a>
                        {% else %}
                            掲載組織別のページが存在しない、もしくはスクリーンショット取得失敗
                        {% endif %}<br>
                        <strong>組織名 (AI調査):</strong> {{ org.victimNameAI|defang }}<br>
                        <strong>国 (AI調査):</strong> {{ org.victimHQLocation|defang }}<br>
                        <strong>業種 (AI調査):</strong> {{ org.victimBizType|defang }}<br>
                        <strong>URL (AI調査):</strong> {{ org.victimUrlAI|defang }}<br>
                        <strong>日本との関係性 (AI調査):</strong> {{ org.victimsRelationJPByAI|defang }}<br>
                        {% if org.annoucementAI %}
                        <strong>声明の可能性 (AI調査):</strong> {{ org.annoucementAI|defang }}<br>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <!-- 削除された企業情報一覧 -->
            {% if deleted_orgs %}
            <div class="info-section">
                <div class="info-header deleted">削除された企業情報
                <span class="note-text-deleted">(※古いページへの移動などで表示されなくなったケースを含みます)</span>
                </div>
                
                {% for org in deleted_orgs %}
                <div class="info-card deleted">
                    <div class="info-body">
                        <strong>掲載組織名:</strong>{{ org.victimName|defang }}<br>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        ※本メールに返信しないでください。本メールに関する問い合わせはCIGまで別途ご連絡ください。<br>
        ※接続不安定なタイミングやページの読み込みが中断された場合などでも誤検知がみられることがあります。
    </body>
    </html>
    """
    html_output = ''
    try:
        # テンプレートをEnvironmentから作成
        template = env.from_string(html_template)
        html_output = template.render(**data)
    except Exception as e:
        print(e)
    return html_output