from pickle import NONE
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys #sys._getframe().f_code.co_name
from bs4 import BeautifulSoup
from OnionScraperLib import jsonController
from OnionScraperLib import utilFuncs as uf


TOR_PATH = r'E:\MonitorSystem\Source\OnionScraper\Tor Browser\Browser\firefox.exe'
FIREFOX_PROFILE = r'E:\MonitorSystem\Source\OnionScraper\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default'
EXECUTABLE_PATH = r'E:\MonitorSystem\Source\GeckoDriver'
binary = FirefoxBinary(r"E:\MonitorSystem\Source\OnionScraper\Tor Browser\Browser\firefox.exe")
driver = None

#CSV フォーマット
# 情報取得日,グループ名,情報掲載日,被害組織名,被害組織国籍,被害組織年商,被害組織URL,その他情報,重複情報(過去取得済み)

COLUMN_FORMAT = ["","","","","","","","",""]

import subprocess
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
import os
def Func_GetFFDriver_():
    # result = subprocess.run('taskkill /f /im firefox.exe',shell=True)
    # result = subprocess.run(TOR_PATH)

    try:
        torexe = os.popen(r'E:\MonitorSystem\Source\OnionScraper\Tor Browser\Browser\tor.exe')
        profile = FirefoxProfile(r'E:\MonitorSystem\Source\OnionScraper\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default')
        profile.set_preference('network.proxy.type', 1)
        profile.set_preference('network.proxy.socks', '127.0.0.1')
        profile.set_preference('network.proxy.socks_port', 9050)
        profile.set_preference("network.proxy.socks_remote_dns", False)
        profile.update_preferences()
        driver = webdriver.Firefox(firefox_profile= profile, executable_path=r'C:\Webdriver\geckodriver.exe')
    except Exception as e:
        print(sys.exc_info())

    return driver    

def Func_GetFFDriver():
 
    try:
        result = subprocess.run('taskkill /f /im firefox.exe',shell=True)
        result = subprocess.run(TOR_PATH)  
        driver = webdriver.Firefox(firefox_binary = binary)
    except Exception as e:
        print(sys.exc_info())

    return driver

def Func_FindElementByClassName(ffDriver, className):
    #全要素に対して見つかるまで指定時間のwaitかます
    #retDriver.implicitly_wait(20)
 
    try:
        #ret = retDriver.find_element_by_class_name(className)
        ret = WebDriverWait(ffDriver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, className)))
        #ret = WebDriverWait(retDriver, 20).until(EC.presence_of_element_located((By.ID, className))
    except Exception as e:
        print(sys.exc_info())
        return None

    return ret

def Func_FindElemtsByClassName(ffDriver, className):
    try:
        ret = WebDriverWait(ffDriver, 20).until(EC.presence_of_all_elements_located((By.CLASS_NAME, className)))
    except:
        print(sys.exc_info())
        return None

    return ret

def Func_FindElemtsByCssSelector(ffDriver, selector):
    try:
        # ret = ffDriver.find_element_by_css_selector(selector)
        ret = WebDriverWait(ffDriver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
    except:
        print(sys.exc_info())
        return None

    return ret
    
def Func_scraping_LockBit(ffDriver,jsonElement):
    ret = []

    #LockBitのメインページを開く 
    #TODO：エラーになるようならミラーのURLを変更してトライするロジック
    ffDriver.get(jsonElement[1]['url'])

    #LockBitはすべての被害組織が1ページに配置されているが、スクロールしないと下のほうはおそらくロードされておらず取得できない(2021/12/20)
    #しかし現段階では三か月前くらいまでのものは取得できているのでひとまずオッケー
    victims = Func_FindElemtsByClassName(ffDriver, "post-more-link")

    victimsURLList = []

    try:
        if victims != None:
            for item in victims:
                victimsURLList.append(item.get_attribute("href"))
        
        if victimsURLList != None:
            for item in victimsURLList:
                ffDriver.get(item)
                victimName = Func_FindElementByClassName(ffDriver, "post-big-title")
                victimDesce = Func_FindElementByClassName(ffDriver, "desc")

                if victimName != None:
                    # 情報取得日,グループ名,情報掲載日,被害組織名,被害組織国籍,被害組織年商,被害組織URL,その他情報,重複情報(過去取得済み)
                    ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],"","","","",victimName.text.strip(),victimDesce.text,""])
    except Exception as e:
        print(sys.exc_info())

    
    return ret

def Func_scraping_Conti(ffDriver,jsonElement):
    ret = []
    try:
        #5ページ分くらい取得すれば前回分までは取得できるはず。さすがに。
        for i in range(8):
            url = jsonElement[1]['url'] + '/page/{}'.format(i+1)

            ffDriver.set_page_load_timeout(60)
            ffDriver.get(url)
            html = ffDriver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')

            cardItems = None
            if soup != None:
                cardItems = soup.find_all(class_="card")

            if cardItems != None:
                for i in cardItems:
                    #被害組織名取得
                    victimName = i.find(class_="title").get_text().replace("“","").replace("”","")
                    #URLすべて取得
                    links = i.find_all('a')
                    urlList = []
                    for link in links:
                        urlList.append(link.get('href'))

                    urlStr = ""
                    if urlList != None:
                        urlStr = '@'.join(urlList)

                    #住所
                    #fas fa-map-marker-alt fa-fw がいればその次のspanに住所がいるはず
                    addressStr = ""
                    addressElm = i.find(class_="fas fa-map-marker-alt fa-fw")
                    if addressElm != None:
                        #spanは次の要素のはずなのでnext_siblingで探す
                        addressElm = addressElm.next_sibling
                        addressStr = addressElm.get_text() if addressElm != None else ""

                    #日付は最初のdiv要素にあるはずと信じる
                    publishedDateElm = i.find(class_="footer").find('div')
                    publishedDate = publishedDateElm.get_text() if publishedDateElm != None else ""
                    # 情報取得日,グループ名,情報掲載日,被害組織名,被害組織国籍,被害組織年商,被害組織URL,その他情報,重複情報(過去取得済み)
                    ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],publishedDate,victimName,"",addressStr,urlStr,"",""])
    except Exception as e:
        print(sys.exc_info())

    
    return ret

def Func_scraping_Sabbath(ffDriver,jsonElement):
    ret = []
    try:
        ffDriver.set_page_load_timeout(60)
        ffDriver.get(jsonElement[1]['url'])
        html = ffDriver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        if soup != None:
            articleItems = soup.find_all("article")

            detailInfoList = []
            for i in articleItems:
                victimBlock = i.find(class_="entry-title")
                
                victimInfo = victimBlock.find("a") if victimBlock != None else None

                if victimInfo != None:
                    detailInfoList.append( victimInfo.get('href') )

        for detailItem in detailInfoList:
            ffDriver.get(detailItem)
            detailPage = ffDriver.page_source.encode('utf-8')
            soup = BeautifulSoup(detailPage, 'html.parser')

            victimName = soup.find(class_="page-title").get_text()
                
            date = soup.find(class_="ct-meta-element-date").get_text()
            # 文章中に埋まっている被害組織のURLをさがす
            entry = soup.find(class_="entry-content")

            urlStr = ""
            if entry != None:
                urlStr = entry.find("a").get('href') if entry.find("a") != None else ""

                # 情報取得日,グループ名,情報掲載日,被害組織名,被害組織国籍,被害組織年商,被害組織URL,その他情報,重複情報(過去取得済み)
                ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],'"'+date+'"',victimName,"","",urlStr,"",""])
    except Exception as e:
        print(sys.exc_info())

    if len(ret) == 0:
        ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],"NoData","","","","","",""])
    
    return ret

# ALPHVはデフォルト最大5個しかアイテムが表示されないが、次ページへの遷移もURLに変化がないため5個以上取ろうとするとめんどいので
# あとまわし
def Func_scraping_ALPHV(ffDriver,jsonElement):
    ret = []
    try:
        ffDriver.set_page_load_timeout(300)
        ffDriver.get(jsonElement[1]['url'])
        # java使ってるのでレンダリング前のしか取得できない
        # html = ffDriver.page_source.encode('utf-8')
        # soup = BeautifulSoup(html, 'html.parser')

        # ただの要素見つかるまdの待機用
        # victimBlockList = Func_FindElemtsByClassName(ffDriver, "ng-star-inserted")
        victimBlockList = Func_FindElemtsByClassName(ffDriver, "container ng-star-inserted")

        for i in victimBlockList:
            # 被害組織名
            victimName = i.find(class_="mat-h2").get_text()
            date = i.find(class_="mat-hint").get_text()
            content = i.find(class_="body mat-body ck-content").get_text()

            text = content.find('p').get_text() if content.find('p') != None else ""
            # 情報取得日,グループ名,情報掲載日,被害組織名,被害組織国籍,被害組織年商,被害組織URL,その他情報,重複情報(過去取得済み)
            ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],date,victimName,"","","",text,""])
    except Exception as e:
        print(sys.exc_info())

    if len(ret) == 0:
        ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],"NoData","","","","","",""])

    return ret

def Func_scraping_Cuba(ffDriver,jsonElement):
    ret = []
    try:
        ffDriver.set_page_load_timeout(60)
        ffDriver.get(jsonElement[1]['url'])
        html = ffDriver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')

        btn_viewmore = Func_FindElemtsByCssSelector(ffDriver, '#ajax-load-more > div:nth-child(2) > button:nth-child(1)')

        if btn_viewmore != None:
            btn_viewmore.click()

        # ViewMoreボタン処理後の待機のために呼び出す
        # あっても困らないのでボタン処理なくても呼び出す
        Func_FindElemtsByClassName(ffDriver, 'list clearfix')

        html = ffDriver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')        

        if soup != None:
            victimBlockList = soup.find_all("list clearfix")

            victimsURLList = []
            for i in victimBlockList:
                # 詳細ページに飛ぶためのリンクを取得
                victimsURLList.append(i.find("list-img").find("a").get('href'))
            
            for victim in victimsURLList:
                ffDriver.get(victim)
                htmlDetail = ffDriver.page_source.encode('utf-8')
                soupDetail = BeautifulSoup(html, 'html.parser')                

                # 被害組織名
                victimName = soupDetail.find(class_="page-h1").get_text()
                text = soupDetail.find(class_="page-list-span")
                otherInfo = soupDetail.find(class_="page-list-ul").get_text()

                date = ""

                # 情報取得日,グループ名,情報掲載日,被害組織名,被害組織国籍,被害組織年商,被害組織URL,その他情報,重複情報(過去取得済み)
                ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],date,victimName,"","","",text,""])

    except Exception as e:
        print(sys.exc_info())

    if len(ret) == 0:
        ret.append([uf.getDateToday('%Y/%m/%d'),jsonElement[0],"NoData","","","","","",""])

    return ret

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# 以下本ロジックメイン関数。外から呼ばれる
# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
def Func_scraping_Main():
    ret = []

    # URL一覧となるjsonファイルはMainと同階層にいるのでこのファイルから見ると一個上の階層
    # 混乱するのでとりあえず絶対パス
    retTuple = jsonController.loadJsonFile('E:\MonitorSystem\Source\OnionScraper\TargetLeakSite.json')

    jsonFileObj = retTuple[0]
    jsn = retTuple[1]

    if jsn != None:
        # キー(攻撃グループ名)を列挙
        # keys = jsonController.enumKeys(jsn)
        
        # aa = Func_GetFFDriver_old()
        ffDriver = Func_GetFFDriver()
        if ffDriver == None:
            return

        for item in jsn.items():
            if item[1]['isTarget'] == True:
                if item[0] == 'LockBit2.0':
                    ret.extend(Func_scraping_LockBit(ffDriver,item))
                elif item[0] == 'Conti':
                    ret.extend(Func_scraping_Conti(ffDriver,item))
                elif item[0] == 'Sabbath_54bb47h BLOG':
                    ret.extend(Func_scraping_Sabbath(ffDriver,item))
                elif item[0] == 'AlphVM(BlackCat)':
                    ret.extend(Func_scraping_ALPHV(ffDriver,item))
                elif item[0] == 'Cuba':
                    ret.extend(Func_scraping_Cuba(ffDriver,item))                    
                
    
        ffDriver.quit()

        jsonController.closeJsonFile(jsonFileObj)

    return ret