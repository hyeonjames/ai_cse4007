import sqlite3
import re
from konlpy.tag import Okt
okt = Okt()


def split(sentence):
    return okt.morphs(sentence)
'''
def split(sentence):
    l = list(sentence)
    words = []
    w = ''
    tp = -1
    for al in l:
        ntp = None
        if re.match('[ㄱ-ㅎ]', al) is not None:
            ntp = 0
        elif re.match('[a-zA-Z]', al) is not None:
            ntp = 1
        elif al == ' ' or al == '.' or al == ',':
            ntp = 2
        elif al == ';':
            ntp = 3
        elif al == '!':
            ntp = 4
        elif al == '?':
            ntp = 5
        elif re.match('[ㄱ-ㅎㅏ-ㅣ가-힣]', al) is not None:
            ntp = 6
        else:
            ntp = 7
        if ntp == 2 or tp != ntp:
            w = w.strip()
            if w != '':
                words.append(w)
            tp = ntp
            w = al
        else:
            w = w + al
    if w != '':
        words.append(w) 
        
    return words
'''
def createDb(fileName, outFileName):
    file = open(fileName,'r',encoding="utf-8")

    conn = sqlite3.connect(outFileName)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE documents (id text,sentence text, positive integer)''');
    except:
        print('TABLE EXISTS')
    documents = []
    for line in file.readlines():
        arr = line.split('\t')
        if len(arr) < 3 or not arr[0].isnumeric():
            continue
        id = int(arr[0])
        sentence = arr[1]
        positive = int(arr[2])
        documents.append((id, sentence, positive))
    c.executemany('''INSERT INTO documents (id, sentence, positive) VALUES (?,?,?)''', documents)
    conn.commit()
    conn.close()
    file.close()



def test1(fileName, outFileName):
    file = open(fileName,'r',encoding="utf-8")

    conn = sqlite3.connect(outFileName)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE dictionary (word text, pos integer, neg integer)''')
    except:
        print('TABLE EXISTS')
    dic = {}
    for line in file.readlines():
        arr = line.split('\t')
        if len(arr) < 3 or not arr[0].isnumeric():
            continue
        id = int(arr[0])
        sentence = arr[1]
        positive = int(arr[2])
        words = split(sentence)
        dic2 = {}
        for w in words:
            w = w.strip()
            if w == '':
                continue
            dic2[w] = True
        for w in dic2.keys():
            if w not in dic:
                dic[w] = {'p' : 0, 'n' : 0}
            if positive == 1:
                dic[w]['p'] = dic[w]['p']+1
            else:
                dic[w]['n'] = dic[w]['n']+1
    values = []
    for w in dic.keys():
        values.append((w, dic[w]['p'], dic[w]['n']))
    c.executemany('''INSERT INTO dictionary (word,pos, neg) VALUES (?,?,?)''', values)
    conn.commit()
    conn.close()
    file.close()


test1('ratings_train.txt', 'test4.db')

#print(split('엠마왓슨짱짱 연기너무 잘해요'))