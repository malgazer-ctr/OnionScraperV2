import threading
import re
import json
from Config import Config as cf
from OnionScraperLib import Log
from OnionScraperLib import GenerativeAI as ga
from OnionScraperLib import GetHTML
from OnionScraperLib import CheckJapanese as cj
from OnionScraperLib import BoxAPI as ba
from OnionScraperLib import Notification
from OnionScraperLib import FileOperate as fo
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import SetupBrowser as sb
import MonitorMainV2 as mm2
import MonitorSub as ms

Log.g_Lock = threading.Lock()

# -------------------------------------------------------------------------------------------
# debug
# -------------------------------------------------------------------------------------------
try:
    url = 'https://worldleaksartrjm3c6vasllvgacbi5u3mgzkluehrzhk2jz4taufuid.onion/companies'
    torProc, driver, service, temp_dir, torConfFile = sb.setup_driver('YuichiTest', headless_ = False)
    driver.get(url)
    sb.clear_driver(torProc, driver, service, temp_dir, torConfFile)
except Exception as e:
    print(e)

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
#     "Accept": "*/*",
#     "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
#     "Accept-Encoding": "gzip, deflate",
#     "Referer": "http://ks5424y3wpr5zlug5c7i6svvxweinhbdcqcfnptkfcutrncfazzgz5id.onion/posts.php",
#     "X-API-Token": "ks-blog-x7g9k2-2024",
#     "Connection": "keep-alive"
# }

# response = sb.getHtmlResponseByRequest(databaseUrl, headers=headers, verify=False)

# raw_bytes = response.content
# if len(raw_bytes) > 0:
#     text = raw_bytes.decode("utf-8")
#     dataArray = json.loads(text)
#     # ..get('objects', [])
test  = 1

# -------------------------------------------------------------------------------------------
# ret = uf.Google_Translate('hello world')

# def waitForPageLoadComplete(driver, timeout=180):
#     """
#     実用的なページロード完了待機
#     """
#     import time
#     from selenium.webdriver.support.ui import WebDriverWait
    
#     start_time = time.time()
    
#     try:
#         # 1. document.readyState = complete を待つ
#         WebDriverWait(driver, timeout).until(
#             lambda d: d.execute_script("return document.readyState") == "complete"
#         )
        
#         # 2. すべての画像のロード完了を待つ
#         WebDriverWait(driver, timeout).until(
#             lambda d: d.execute_script("""
#                 const images = Array.from(document.images);
#                 return images.length === 0 || images.every(img => img.complete);
#             """)
#         )
        
#         # 3. jQueryがある場合、Ajaxリクエストの完了を待つ
#         WebDriverWait(driver, timeout).until(
#             lambda d: d.execute_script("""
#                 if (typeof jQuery !== 'undefined') {
#                     return jQuery.active === 0;
#                 }
#                 return true;
#             """)
#         )
        
#         # 4. ネットワークアイドル状態を待つ（500ms間新規リクエストなし）
#         idle_start = None
#         while time.time() - start_time < timeout:
#             active = driver.execute_script("""
#                 return window.performance.getEntriesByType('resource')
#                     .filter(r => r.responseEnd === 0).length;
#             """)
            
#             if active == 0:
#                 if idle_start is None:
#                     idle_start = time.time()
#                 elif time.time() - idle_start >= 0.5:
#                     return True
#             else:
#                 idle_start = None
            
#             time.sleep(0.1)
        
#         return True
        
#     except Exception as e:
#         print(f"Page load wait error: {e}")
#         return False

# torProc, driver, service, temp_dir, torConfFile = sb.setup_driver('Qilin_YuichiTest', headless_ = True)
# driver.get('http://ijzn3sicrcy7guixkzjkib4ukbiilwc3xhnmby4mcbccnsd7j2rekvqd.onion')
# waitForPageLoadComplete(driver)
# successScreenShot, resultPNG_now, resultPNGBefore, resultPNGAfter = ms.saveScreenShot('Qilin_YuichiTest', driver)
# sb.clear_driver(torProc, driver, service, temp_dir, torConfFile)

test  = 1
