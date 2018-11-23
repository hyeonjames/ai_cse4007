# -*- coding: utf-8 -*-
import json
import math
import re
import time
from threading import Thread
from konlpy.tag import Okt

import jpype
okt = Okt()

# main 함수 시간을 측정하기 위한 decorator
def timeit(method):
    def timed(*args):
        ts = time.time()
        result = method(*args)
        te = time.time()
        print('time [' + method.__name__ + ']: ' + str(te-ts) + 's')
        return result
    return timed


# 학습을 위한 병렬처리 메서드
def do_concurrent_train(lines, dic):
    jpype.attachThreadToJVM()
    for l in lines:

        words = split(l[1])
        dic2 = {}

        for w in words:
            dic2[w] = True
        for w in dic2.keys():
            if w not in dic:
                dic[w] = {'p' : 0, 'n' : 0}
            if l[2] == 1:
                dic[w]['p'] = dic[w]['p']+1
            else:
                dic[w]['n'] = dic[w]['n']+1
# 학습 후 결과를 합치기 위함
def merge_dic(dicts):
    dc = {}
    for dic in dicts:
        for x in dic.keys():
            if x in dc:
                dc[x]['p'] = dc[x]['p'] + dic[x]['p']
                dc[x]['n'] = dc[x]['n'] + dic[x]['n']
            else:
                dc[x] = {}
                dc[x]['p'] = dic[x]['p']
                dc[x]['n'] = dic[x]['n']
    return dc

# 한 문장을 여러개의 워드로 나눔
# 1-4번
def split(sentence):
    return set(okt.morphs(sentence))
'''
1-3
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
1-2
def split(sentence):
    return sentence.replace('.', ' ').replace(',',' ').strip().split(' ')
1-1
def split(sentence):
    return sentence.split(' ')
'''
#@timeit
def train(fileName, maxThread):
    # 학습할 파일 읽기
    file = open(fileName,'r',encoding="utf-8")

    # 데이터 초기화
    info = {
        'total' : 0,
        'positive' : 0,
        'negative' : 0,
        'words' : {}
    }
    
    # 파일을 읽어서 Q에 넣는다
    q = []
    for line in file.readlines():
        arr = line.split('\t')
        if len(arr) < 3 or not arr[0].isnumeric():
            continue
        q.append((int(arr[0]), arr[1], int(arr[2])))
        info['total'] = info['total']+1
        if int(arr[2]) == 1:
            info['positive'] = info['positive']+1
        else:
            info['negative'] = info['negative']+1
    file.close()

    # 로그 값들을 미리 저장합니다
    info['positive'] = math.log2(info['positive'])
    info['negative'] = math.log2(info['negative'])
    info['total'] = math.log2(info['total'])

    dicts = [{} for x in range(0, maxThread)]
    threads = []
    cur = 0
    step = math.ceil(len(q)/maxThread)
    for i in range(0, maxThread):
        qi = q[cur:min(len(q), cur+step)]
        threads.append(
            Thread(target=do_concurrent_train, args=(qi, dicts[i]))
        )
        cur = cur + step
    for t in threads:
        t.start()
    for t in threads:
        t.join()
            
    dic = merge_dic(dicts)
    for w in dic.keys():
        # 0이 나온 경우 1로 설정
        if dic[w]['p'] == 0:
            dic[w]['p'] = 1
        elif dic[w]['n'] == 0:
            dic[w]['n'] = 1
        # 로그 값은 먼저 계산
        info['words'][w] = (math.log2(dic[w]['p']), math.log2(dic[w]['n']))
    return info

def do_concurrent_query (info, lines, out):
    jpype.attachThreadToJVM()
    for l in lines:
        id = l[0]
        sent = l[1]
        positive = query(info, sent)
        out.append(str(id) + '\t' + sent + '\t' +('1' if positive == True else '0') + '\n')

# 문장의 긍부정을 판별하는 함수
# info : 학습된 데이터 ( 로그 값들은 미리 계산 되어 있음 )
# sentence : 문장
def query(info, sentence):
    words = split(sentence)
    pos = info['positive'] - info['total']
    neg = info['negative'] - info['total']
    dic = info['words']
    for w in words:
        if w in dic:
            pos = pos + (dic[w][0] - info['positive'])
            neg = neg + (dic[w][1] - info['negative'])
    if pos >= neg:
        return True
    return False
#@timeit
def test(info, testFileName, outFileName, maxThread = 1):
    file = open(testFileName, 'r', encoding='utf-8')
    out = open(outFileName, 'w', encoding='utf-8')

    # 테스트 파일을 읽어 Q에 넣음
    q = []
    for line in file.readlines():
        arr = line.split('\t')
        if len(arr) < 2 or not arr[0].isnumeric():
            continue
        id = int(arr[0])
        sent = arr[1]
        q.append((id, sent))

    # Q를 maxThread개로 분리하고 쓰레드 생성
    cur = 0
    step = math.ceil(len(q) / maxThread)
    threads = []
    res = []
    for i in range(0,maxThread):
        res.append([])
        qi = q[cur:min(len(q), cur+step)]
        threads.append(
            Thread(target=do_concurrent_query, args=(info, qi, res[i]))
        )
        cur = cur + step
    # 멀티쓰레드 처리
    print('멀티 쓰레드 쿼리 시작')
    for t in threads:
        t.start()
    for i in range(0,maxThread):
        threads[i].join()
        # 결과를 파일에 저장
        out.writelines(res[i])
        out.flush()
    file.close()
    out.close()

def result(fileName):
    r = {}
    file = open(fileName, 'r', encoding='utf-8')
    for line in file.readlines():
        arr = line.split('\t')
        if len(arr) < 3 or not arr[0].isnumeric():
            continue
        id = int(arr[0])
        sent = arr[1]
        positive = int(arr[2])
        r[id] = (sent,positive)
    file.close()
    return r

# 파일1과 파일2를 비교해서 정확도를 측정함
def match(file1,file2):
    r1 = result(file1)
    r2 = result(file2)
    correct = 0
    total = 0
    diff = []
    for id in r1.keys():
        if id in r2:
            total = total + 1
            if r2[id][1] == r1[id][1]:
                correct = correct + 1
            else:
                diff.append((id, r1[id][0], r1[id][1], r2[id][1]))
    percent = (correct/total)*100
    print('총 ' + str(total) + '개중 ' + str(correct) + '개 일치 (' + str(percent) + '%)')
    return diff

# 학습된 데이터 JSON으로 저장하기 위함
def saveJson(fileName, js):
    out = open(fileName, 'w', encoding='utf-8')
    json.dump(js,out)
    out.close()
# 학습된 데이터 JSON으로 읽기 위함
def openJson(fileName):
    try:
        inp = open(fileName, 'r', encoding='utf-8')
        return json.load(inp)
    except:
        return False
def saveDiff(diff, fileName):
    try:
        out = open(fileName, 'w', encoding='utf-8')
        for x in diff:
            l = str(x[0]) + '\t' + x[1] + '\t' + str(x[2]) + '\t' + str(x[3]) + '\n'
            out.writelines([l])
        out.close()
        return True
    except:
        return False

#@timeit
def main():
    info = openJson('./trained.json')
    if info == False:
        info = train('./ratings_train.txt', 4)
        saveJson('./trained.json', info)

    test(info, './ratings_valid.txt', './ratings_result.txt', 4)
    dif = match('./ratings_valid.txt', './ratings_result.txt')

main()