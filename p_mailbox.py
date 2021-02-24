import random
import time
from pq import MyPriorityQueue
from multiprocessing import Process,Manager
from multiprocessing.managers import SyncManager
from channels import channel
import datetime


class MyManager(SyncManager):
    pass
MyManager.register("PriorityQueue", MyPriorityQueue)  # Register a shared PriorityQueue

def Manager():
    m = MyManager()
    m.start()
    return m

class Mailbox:
    def __init__(self,p_id,chan,peerObjs,process_rate,num_priorities,queue_size,accelerate,fee_policy):
        self.accelerate_mb = accelerate
        self.peer_id = p_id
        self.num_of_priorities = num_priorities
        #htlc id and time stemp in each queue
        self.queue_size = queue_size
        self.m = Manager()
        self.p_queue = self.m.PriorityQueue(queue_size)
        #forwarding fee of each queue
        self.p_fee = [x for x in fee_policy]
        #processing rate 100 payments/s
        self.processing_rate = process_rate
        self.forward = Process(target=self.htlc_out,args=(chan,peerObjs))

    def htlc_out(self,chan,peerObjs):
        while True:
            current_time = datetime.datetime.now()
            data_re = self.p_queue.remove(current_time)
            while len(data_re)>0:
                payer_id,p_hash = data_re.pop()
                del peerObjs[payer_id].created_htlc[p_hash]
            msg = self.p_queue.get(block=True)
            #simulate the processing time
            time.sleep(self.accelerate_mb/self.processing_rate)
            current_time = datetime.datetime.now()
            msg['trace'][str(chan.hop)] = current_time
            chan.htlc_queue.put(msg)
            

            
                





'''            
            if current_hop[0]>current_hop[1]:
                current_hop = tuple(reversed(list(current_hop)))
            chan_str = 'channel'+str(current_hop[0])+str(current_hop[1])
            target_chanID = hash(chan_str)

            #send msg
            for chan in ChanObjs:
                if chan.channelID == target_chanID:
                    #insert the forwarding htlc msg into channel queue
                    msg['trace'][str(chan.hop)] = datetime.datetime.now()
                    chan.htlc_queue.put(msg)
                    break


chan = channel(1,(1,2))
mailbox = Mailbox(1,chan)
mailbox.p_queue.join()
msgs = [{'p_set':[1,1],'time':1,'r_hop':[(1,2),(2,3)]},{'p_set':[1,1],'time':2,'r_hop':[(1,2),(2,3)]}]
for msg in msgs:
    mailbox.htlc_in(msg)
while mailbox.p_queue.empty() == False:
    msg0 = mailbox.p_queue.get()
    print(msg0.item)
'''