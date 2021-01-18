import queue,heapq
from heapq import heappush, heappop

class MyPriorityQueue(queue.Queue):
    def _init(self,maxsize):
        self.queue = []

    def _qsize(self):
        return len(self.queue)

    def _put(self,entry):
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
        return heappop(self.queue)