import json

def loadJsonFile(path):
    jsn = None
    with open(path,encoding="utf-8") as f:
        jsn = json.load(f)

    return (f,jsn)

def closeJsonFile(fileObj):
    fileObj.close()


# KEYwを列挙してリストで返す
def enumKeys(jsonObj):
    ret = []
    for jsn_key in jsonObj:
        ret.append(jsn_key)

    return ret