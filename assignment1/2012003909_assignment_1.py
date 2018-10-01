from queue import Queue,PriorityQueue
import copy
import sys
import io
from dataclasses import dataclass, field
from typing import Callable , Any
class Direction:
    LEFT = (0, -1)
    RIGHT = (0,1 )
    DOWN = (1, 0)
    UP = (-1, 0)


def getDirectionOrder(start : tuple,goal : tuple):
    # start부터 goal까지 가기 위해서 우선순위대로 방향을 반환
    x = [Direction.RIGHT,Direction.LEFT]
    y = [Direction.DOWN, Direction.UP]
    if start[0] > goal[0]:
        y = [Direction.UP,Direction.DOWN]
    if start[1] > goal[1]:
        x = [Direction.LEFT,Direction.RIGHT]
    if start[0] == goal[0]:
        return [x[0], y[0], x[1], y[1]]
    return [y[0], x[0], y[1],x[1]]
class Maze:
    start : tuple
    key : tuple
    map :list
    height : int
    width : int
    @dataclass(order=True)
    class AStarNode:
        priority : int
        item : Any=field(compare=False)
        def __init__(self, priority : int, item):
            self.priority = priority
            self.item = item
    def copy (self):
        # 해당 인스턴스 복제
        mz = copy.deepcopy(self)
        mz.map = copy.deepcopy(self.map)
        return mz
    def __init__(self, fileName : str):
        # maze파일을 읽어서 인스턴스 생성
        f = open(fileName)
        self.map = []
        n, self.height, self.width = [int(x) for x in f.readline().strip().split(' ')]
        for l in f:
            line = [int(x) for x in l.strip().split(' ')]
            self.map.append(line)
            for x in range(0,len(line)):
                if line[x] == 3:
                    self.start = (len(self.map)-1 , x)
                elif line[x] == 4:
                    self.goal = (len(self.map)-1 , x)
                elif line[x] == 6:
                    self.key = (len(self.map)-1 , x)
    def checkPos (self,pos : tuple):    
        # 해당 포지션에 있는 곳이 지나 갈 수 있는 곳인가?
        if pos[0] < 0 or pos[0] >= self.height or pos[1] < 0 or pos[1] >= self.width:
            return False
        return self.map[pos[0]][pos[1]] != 1
    def move(self , pos : tuple, direction : tuple):
        # 현재 포지션에서 direction으로 이동해본다
        newPos = (pos[0] + direction[0] , pos[1] + direction[1])
        if self.checkPos(newPos):
            return newPos
        return None
    def createPathTrack(self):
        # 경로 역추적 하기 위한 배열을 만든다
        # 반환 배열을 t라고 할때 t[y][x] = (y,x) 가 초기상태
        # t[y][x] = (y,x)로 오기 전 이전 경로
        ret = []
        for i in range(0, self.height):
            ret.append([(i,x) for x in range(0,self.width)])
        return ret
    def applyPath(self, path : list, goal : tuple):
        # 역추적하여 현재 미로에 적용한다
        cur = goal
        while path[cur[0]][cur[1]] != cur:
            if self.map[cur[0]][cur[1]] == 2 or self.map[cur[0]][cur[1]] == 6:
                self.map[cur[0]][cur[1]] = 5
            cur = path[cur[0]][cur[1]]
    def dfs_sub(self, start : tuple, goal: tuple, step : int):
        # step 까지 DFS 탐색
        time = 1
        if start == goal:
            if self.map[start[0]][start[1]] == 2:
                self.map[start[0]][start[1]] = 5
            return (time, True, 1)
        if step == 0:
            return (time, False, 0)
        prev = self.map[start[0]][start[1]]
        self.map[start[0]][start[1]] = 1
        order = getDirectionOrder(start,goal)
        for dr in order:
            mv = self.move(start, dr)
            if mv is not None:
                ret = self.dfs_sub(mv, goal, step-1)
                time += ret[0]
                if ret[1]:
                    self.map[start[0]][start[1]] = 5 if prev == 2 else prev
                    return (time, True, ret[2]+1)
        self.map[start[0]][start[1]] = prev
        return (time, False, 0)
    def ids_sub( self, start : tuple, goal : tuple):
        # start 부터 goal까지 IDS로 경로를 탐색한다
        length = 1
        time = 0
        while True:
            ret = self.dfs_sub(start, goal, length )
            time += ret[0]
            if ret[1]:
                return (time, length)
            length += 1
    def ids(self):
        ret1 = self.ids_sub(self.start, self.key)
        ret2 = self.ids_sub(self.key, self.goal)
        return (ret1[0]+ret2[0], ret1[1]+ret2[1])
    def pr_bfs_sub(self, start: tuple, goal: tuple, fc : Callable[[tuple, tuple, int],int]) -> tuple:
        # start부터 goal까지 A*함수로 경로를 탐색한다
        # fc : priority 구하는 함수; Caller 정의
        mz = self.copy()
        q = PriorityQueue()
        
        time = 0
        path = self.createPathTrack()
        
        q.put(Maze.AStarNode( 0, (start, 0 , start )))
        while not q.empty():
            node = q.get()
            prior, item = node.priority, node.item
            pos, length, previous = item
            # PATH 추적을 위해 전 단계를 저장
            path[pos[0]][pos[1]] = previous

            mz.map[pos[0]][pos[1]] = 1
            if pos == goal:
                self.applyPath(path, goal)
                return (time, length)
            # getDirectionOrder 함수로 도착지점을 찾기 위한 방향을 우선순위별로 얻음
            order = getDirectionOrder(pos, goal)
            for dr in order:
                mv = mz.move(pos,dr)
                if mv is not None:
                    # 함수인자로 전달받은 fc함수를 이용해 Priority Queue의 우선순위를 결정합니다
                    q.put(Maze.AStarNode(fc(pos, goal, length+1), (mv, length+1, pos)))
            time = time + 1
        return (0,0)
    def gbs(self) -> tuple:
        # Greedy best first search
        
        h = lambda a,b,c : abs(a[0]-b[0])+abs(a[1]-b[1])
        r1 = self.pr_bfs_sub(self.start, self.key, h)
        r2 = self.pr_bfs_sub(self.key, self.goal, h)
        return (r1[0] + r2[0], r1[1]+r2[1])
    def astar(self) -> tuple:
        # heuristic function = 장애물이 하나도 없을 때의 최소거리
        h = lambda a,b,c : abs(a[0]-b[0])+abs(a[1]-b[1])+c

        r1 = self.pr_bfs_sub(self.start, self.key, h)
        r2 = self.pr_bfs_sub(self.key, self.goal, h)
        return (r1[0] + r2[0], r1[1]+r2[1])
    def dfs(self) -> tuple:
        r1 = self.dfs_sub(self.start,self.key, 100000)
        r2 = self.dfs_sub(self.key,self.goal , 100000)
        return (r1[0]+r2[0], r1[2]+r2[2])
    def bfs(self) -> tuple:
        # priority를 안주면; BFS처럼 동작
        h = lambda a,b,c : 0
        r1 = self.pr_bfs_sub(self.start, self.key, h)
        r2 = self.pr_bfs_sub(self.key, self.goal, h)
        return (r1[0] + r2[0], r1[1]+r2[1])
    def print(self, stream : io.TextIOWrapper):
        for l in self.map:
            for v in l:
                stream.write(str(v) + ' ')
            stream.write('\n')
    

def execute(floor : str, algorithm : Callable[[Maze], tuple]):
    mz = Maze(floor+"_floor_input.txt")
    time, length = algorithm(mz)
    fi = io.open(floor+'_floor_output.txt','w')
    mz.print(fi)
    fi.write('---\n')
    fi.write('length=' + str(length) + '\n')
    fi.write('time=' + str(time) + '\n')
    fi.close()

def test(floor:str):
    mz = Maze(floor + "_floor_input.txt")
    print('==='+floor + ' floor===')
    time, length = mz.astar()
    print ( 'A*; time='+str(time)+' length=' + str(length) )
    time, length = mz.bfs()
    print ( 'BFS; time='+str(time)+' length=' + str(length) )
    time, length = mz.gbs()
    print ('Greedy; time='+str(time)+' length=' + str(length))
    try:
        time,length = mz.dfs()
        print ( 'DFS; time=' + str(time) + ' length=' + str(length))
    except RecursionError:
        print('DFS; Recursion Overflow')
        pass
    try:
        time, length = mz.ids()
        print ( 'IDS; time='+str(time)+' length=' + str(length) )
    except RecursionError:
        print ( 'IDS; Recursion Overflow')
        pass
    print('-------------')

def first_floor():
    # first_floor_input.txt를 읽어 Maze 인스턴스를 생성합니다
    # 두번째 인자인 lambda 함수로 알고리즘을 실행합니다
    # 결과를 first_floor_output.txt에 저장합니다
    execute('first', lambda mz : mz.gbs())
    # 여기서 first는 층 ( 이를 이용해 input과 output파일을 가져옵니다 )
    # 뒤의 lambda 함수는 사용할 알고리즘을 정의합니다. mz는 Maze 인스턴스 입니다.

def second_floor(): 
    # second_floor_input.txt를 읽어 Maze 인스턴스를 생성합니다
    # 두번째 인자인 lambda 함수로 알고리즘을 실행합니다
    # 결과를 second_floor_output.txt에 저장합니다
    execute('second', lambda mz : mz.gbs())

def third_floor():
    # third_floor_input.txt를 읽어 Maze 인스턴스를 생성합니다
    # 두번째 인자인 lambda 함수로 알고리즘을 실행합니다
    # 결과를 third_floor_output.txt에 저장합니다
    execute('third', lambda mz : mz.gbs())

def fourth_floor():
    # fourth_floor_input.txt를 읽어 Maze 인스턴스를 생성합니다
    # 두번째 인자인 lambda 함수로 알고리즘을 실행합니다
    # 결과를 fourth_floor_output.txt에 저장합니다
    execute('fourth', lambda mz : mz.gbs())

def fifth_floor():
    # fifth_floor_input.txt를 읽어 Maze 인스턴스를 생성합니다
    # 두번째 인자인 lambda 함수로 알고리즘을 실행합니다
    # 결과를 fifth_floor_output.txt에 저장합니다
    execute('fifth', lambda mz : mz.gbs())

mode = 'real'    
if mode == 'real':
    first_floor()
    second_floor()
    third_floor()
    fourth_floor()
    fifth_floor()
else:
    test('fifth')
    test('fourth')
    test('third')
    test('second')
    test('first')
