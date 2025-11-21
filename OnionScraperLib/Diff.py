import re
import os
import difflib
from Config import Config as cf
from OnionScraperLib import Log
from OnionScraperLib import FileOperate as fo

def diff_Differ(before, after):
    ret = ""
    
    try:
        file1 = open(before, encoding="utf-8")
        file2 = open(after, encoding="utf-8")
        diff = difflib.Differ()

        lines_file1 = file1.readlines()
        lines_file2 = file2.readlines()

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
            
        # 差分が数字だけなら無視
        if re.match(r"^\d+$", chkStr) == None:
            diff_ = diff.compare(lines_file1, lines_file2)

            # 差分のみにする
            for data in diff_ :
                if data[0:1] in ['+', '-'] :
                    ret += data            

        file1.close()
        file2.close()

    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return ret

def diff_Differ2(before, after):
    ret = ""
    
    try:
        with open(before, encoding="utf-8") as file1:
            lines_file1 = file1.readlines()
            # lines_file1 = [s.replace('\n', '') for s in lines_file1_]

        with open(after, encoding="utf-8") as file2:
            lines_file2 = file2.readlines()
            # lines_file2 = [s.replace('\n', '') for s in lines_file2_]
        
        diff = difflib.Differ()

        # diff_ = difflib.unified_diff(lines_file1, lines_file2, n = 10, lineterm='')
        # diff_ = difflib.ndiff(lines_file1, lines_file2)
        diff_ = diff.compare(lines_file1, lines_file2)
        # 差分のみにする
        for data in diff_ :
            if data[0:2] in ['+ ', '- '] :
                ret += data  
        # chkStr = ''
        # for elem1,elem2 in zip(lines_file1,lines_file2):
        #     # 一文字ずつ差分を確認。数字だけの差分行は無視する
        #     for i,s in enumerate(difflib.ndiff(elem1,elem2)):
        #         if s[0]==' ': continue
        #         elif s[0]=='-':
        #             chkStr += s[-1]
        #             # print(u'Delete "{}" from position {}'.format(s[-1],i))
        #         elif s[0]=='+':
        #             chkStr += s[-1]
        #             # print(u'Add "{}" to position {}'.format(s[-1],i))    
            
        # # 差分が数字だけなら無視
        # if re.match(r"^\d+$", chkStr) == None:
        #     diff_ = diff.compare(lines_file1, lines_file2)

        #     # 差分のみにする
        #     for data in diff_ :
        #         if data[0:1] in ['+', '-'] :
        #             ret += data            
    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return ret    

def diff_HTML(before, after):
    try:    
        Log.Logging('diff_HTML',"{}".format(Log.Trace.execution_location()))
        file1 = open(before, encoding="utf-8")
        file2 = open(after, encoding="utf-8")

        diff = difflib.HtmlDiff(wrapcolumn=80)
        ret = diff.make_file(file1, file2)

        Log.Logging('diff_HTML',"{}".format(Log.Trace.execution_location()))

        file1.close()
        file2.close()
    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

    return ret

import subprocess
# from xhtml2pdf import pisa
import pdfkit
def createWinmergeReport(beforePath, afterPath, outPath, requirePDF = True):
    try:
        outFilePath = outPath + '_Diff2.html'
        beforeTime = fo.Func_GetFileUpdateTime(beforePath)
        afterTime = fo.Func_GetFileUpdateTime(afterPath)

        command = f'"C:\Program Files\WinMerge\WinMergeU.exe" "{beforePath}" "{afterPath}" -minimize -noninteractive -u -or "{outFilePath}" /dl "{beforeTime}" /dr "{afterTime}"'

        proc = subprocess.Popen(command, shell=True)

        proc.wait()

        if requirePDF == True and os.path.exists(outFilePath) == True:
            outPDFFilePath = outPath + '_Diff.pdf'

            options = {
                'page-size': 'A4',
                'margin-top': '0.1in',
                'margin-right': '0.1in',
                'margin-bottom': '0.1in',
                'margin-left': '0.1in',
                'encoding': "UTF-8",
                'no-outline': None,
                'disable-smart-shrinking': '',
            }
            config = pdfkit.configuration(wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
           
            # source_html = fo.Func_ReadFile(outFilePath)
            # pdfkit.from_string(source_html, 'outPDFFilePath.pdf', configuration=config, options=options)
            pdfkit.from_file(outFilePath, outPDFFilePath, configuration=config, options=options)

            # PDF返したいとき
            return outPDFFilePath

        return outFilePath

    except Exception as e:
        Log.Logging('Exception',"{}: Exception:{}".format(Log.Trace.execution_location(), str(e.args)))

def convertHTML2PDF(outFilePath, outPDFFilePath):
    if os.path.exists(outFilePath) == True:
        options = {
            'page-size': 'A4',
            'margin-top': '0.1in',
            'margin-right': '0.1in',
            'margin-bottom': '0.1in',
            'margin-left': '0.1in',
            'encoding': "UTF-8",
            'no-outline': None,
            'disable-smart-shrinking': '',
        }
        config = pdfkit.configuration(wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
        
        # source_html = fo.Func_ReadFile(outFilePath)
        # pdfkit.from_string(source_html, 'outPDFFilePath.pdf', configuration=config, options=options)
        pdfkit.from_file(outFilePath, outPDFFilePath, configuration=config, options=options)

        # PDF返したいとき
        return outPDFFilePath

    return ''