import re

from Config import Config as cf
from OnionScraperLib import FileOperate as fo

# List of common Roman syllables used in Japanese words
roman_syllables = set([
    'a', 'i', 'u', 'e', 'o',
    'ka', 'ki', 'ku', 'ke', 'ko',
	'ga', 'gi', 'gu', 'ge', 'go',
    'sa', 'shi', 'su', 'se', 'so',
	'za', 'ji', 'zu', 'ze', 'zo',
    'ta', 'chi', 'tsu', 'te', 'to',
	'da', 'de', 'do', #'ji', 'zu'
    'na', 'ni', 'nu', 'ne', 'no',
    'ha', 'hi', 'fu', 'he', 'ho',
    'pa', 'pi', 'pu', 'pe', 'po',
    'ba', 'bi', 'bu', 'be', 'bo',
    'ma', 'mi', 'mu', 'me', 'mo',
    'ya', 'yu', 'yo',
    'ra', 'ri', 'ru', 're', 'ro',
    'wa', 'wo', 'n',
    'kya', 'kyo', 'kyu', 'sha', 'shu', 'sho',
    'cha', 'chu', 'cho', 'nya', 'nyu', 'nyo',
    'hya', 'hyu', 'hyo', 'mya', 'myu', 'myo',
    'rya', 'ryu', 'ryo', 'gya', 'gyu', 'gyo',
    'ja', 'ju', 'jo', 'bya', 'byu', 'byo',
    'pya', 'pyu', 'pyo',
    'tya', 'tyu', 'tyo'
    # 'kai', 'sappo',
    # 'saki', 'ji', 'sappo', 'ra', 'tako', 'naga',
    # 'fuji', 'hiro', 'kawa', 'wasa', 'kusa'
])

# Function to check if a word is a Roman word
def is_roman_word(word):
    try:
        i = 0
        wordTmp = word.lower()

        if len(wordTmp) > 0:
            while i < len(wordTmp):
                if i < len(wordTmp) - 2 and wordTmp[i:i + 3] in roman_syllables:
                    i += 3
                elif i < len(wordTmp) - 1 and wordTmp[i:i + 2] in roman_syllables:
                    i += 2
                elif wordTmp[i] in roman_syllables:
                    i += 1
                else:
                    return False
        else:
            return False
    except Exception as e:
        print(str(e))
        return False
    
    return True

# Function to find Roman words in a sentence
def find_roman_words(sentence):
    roman_words = []
    try:
        sentence = sentence.lower()
        wordsTmp = sentence.split()

        words = []
        for i in wordsTmp:
            # ローマ字にして最低三文字とかはないと日本語の単語とみなさない
            # → 三文字だと過検知が多いのでいったん四文字以上にしておく 2023/9/25
            if len(i) > 3:
                words.append(i)

        words = [re.sub(r'[^a-zA-Z]', '', word) for word in words]
        roman_words = [word for word in words if is_roman_word(word)]

    except Exception as e:
        print(str(e))

    return roman_words

import pickle
def isNoEngrishWord(wordArray):
    ret = []
    try:
        dicFile = r"E:\MonitorSystem\Source\OnionScraperV2\OnionScraperLib\dictionary.pkl"
        with open(dicFile, "rb") as f:  # "dictionary.pkl" is available from 
            obj = pickle.load(f)                 # http://ushitora.net/archives/456
        f.close()

        searchTarget = fo.Func_CSVReadist(cf.IGNOREWORD_JAPANESELIKE_LIST_PATH)
        ignoreWords = [x[0] for x in searchTarget]

        for i in wordArray:
            if (i in obj) == False and (i in ignoreWords) == False:
                ret.append(i)
    except Exception as e:
        print(str(e))
    
    return ret

from OnionScraperLib import GenerativeAI as ga

def CheckJapaneseMain(sentence, v2 = False):
    ret = []
    try:
        # else側使わないから消してもいい気がするけどひとまず放置
        if v2:
            wodrsTmp = find_roman_words(sentence)

            # 返ってきたら全部小文字にして重複カット
            if len(wodrsTmp) > 0:
                words = list(set(word.lower() for word in wodrsTmp))
                retTmp = isNoEngrishWord(words)
                
                if len(retTmp) > 0:
                    ret = ga.requestCheckJapaneseWord_ChatGPT(sentence, v2)
        else:
            wodrsTmp = find_roman_words(sentence)

            # 返ってきたら全部小文字にして重複カット
            if len(wodrsTmp) > 0:
                n_WordsTmp = []
                for i in wodrsTmp:
                    n_WordsTmp.append(i.lower())
                words = list(set(n_WordsTmp))
                retTmp = isNoEngrishWord(words)
                retTmp2 = []
                
                for i in retTmp:
                    retChkbyGpt = ga.requestCheckJapaneseWord_ChatGPT(i)
                    if retChkbyGpt.lower().startswith('true'):
                        retTmp2.append(i)

                # 大文字小文字区別なく返してくるので sentence 内のオリジナルの書式（大文字区別あり）でかえす
                # そうしないとメールでハイライトしてくれない
                if len(retTmp2) > 0:
                    for j in retTmp:
                        findItems = re.findall(j, sentence, re.IGNORECASE)
                        if len(findItems) > 0:
                            ret.extend(findItems)

    except Exception as e:
        print(str(e))
    
    return ret

import unicodedata
def Check_JP_Language(input_text):
    try:
        for ch in input_text:
            name = unicodedata.name(ch)
            if "CJK UNIFIED" in name \
            or "HIRAGANA" in name \
            or "KATAKANA" in name:
                return True
            
    except:
        translated_jp_text = '翻訳に失敗しました。'
    return False

# text = 'ito'
# ret = Check_JP_Language(text)
# a = 0
# sentence = 'The following companies refuse to protect foreigners citizens data:\
# - - Nishimura Asahi - rejected \
# - - Atsumi & Sakai - rejected \
# '
# print(CheckJapaneseMain(sentence))

 
# for i in obj:
#     print(str(i))

# 英単語チェック。いまいち
# import enchant
# dictionary = enchant.Dict("en_US")

# for i in ret:
#     print(f'{i}:{dictionary.check(i)}')  
