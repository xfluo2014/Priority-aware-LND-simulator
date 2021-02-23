import queue,heapq
from heapq import heappush, heappop

<<<<<<< HEAD
class Prioritize:
    def __init__(self, priority, item):
        self.priority = priority
        self.item = item

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority < other.priority

=======
>>>>>>> origin/Version0224
class MyPriorityQueue(queue.Queue):
    def _init(self,maxsize):
        self.queue = []

    def _qsize(self):
        return len(self.queue)

<<<<<<< HEAD
    def _put(self,msg):
        Priority = msg['p_set'].pop(0)
        entry = Prioritize(Priority,msg)
=======
    def _put(self,entry):
>>>>>>> origin/Version0224
        heappush(self.queue,entry)

    def remove(self,t):
        idx_list = [i for i,value in enumerate(self.queue) if value.item['expiry'] <= t]
        data = []
        while len(idx_list) > 0:
            idx = idx_list.pop()
            msg = self.queue[idx]
            self.queue[idx] = self.queue[-1]
            self.queue.pop()
            heapq.heapify(self.queue)
            data.append([msg.item['payer'],msg.item['pay_hash']])
        return data
        

    def _get(self):
<<<<<<< HEAD
        return heappop(self.queue).item
=======
        return heappop(self.queue)
>>>>>>> origin/Version0224
