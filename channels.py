import random
import time
from multiprocessing import Process,Queue
import datetime

class channel:
	def __init__(self,delay,hop,queue_size):
		self.hop = None
		self.init_hop(hop)
		self.channelID = hash('channel'+str(self.hop[0])+str(self.hop[1]))
		#init link delay 20ms
		self.delay = delay
		self.htlc_queue = Queue(30)
		#htlc manager on channel
		self.manager = None

	#Define upStream_peer id < downStream_peer id on bidirectional channels 
	#to avoid repeating initialization channels
	def init_hop(self,hop):
		if hop[0] > hop[1]:
			hop = tuple(reversed(hop))
		self.hop = hop

	def init_manager(self,peerObjs):
		self.manager = Process(target= self.send_msg,args=(peerObjs,))
		#self.manager.setDaemon(True)
		#self.manager.start()
		#self.manager.join()

	def send_msg(self,peerObjs):
		while True:
			msg = self.htlc_queue.get(block=True)
			#forward to target peer
			target_peer = msg['r_hop'][0][1]
			#print('target peer:',target_peer)
			#remove the hop from the rest hops (r_hop)
			msg['r_hop'].pop(0)
			#check msg error
			#print(msg['p_set'],msg['r_hop'])
			if len(msg['r_hop']) == len(msg['p_set']):
				#send the msg to the target peer
				current_time = datetime.datetime.now()
				time_delta = int((current_time - msg['trace'][str(self.hop)]).total_seconds()*1000)#delta time in milliseconds
				#print('time_delta: ', time_delta)
				if time_delta < 20:
					time.sleep((self.delay-time_delta)/1000)
				payer_id = msg['payer']
				pay_hash = msg['pay_hash']
				trace = msg['trace']
				if current_time >=msg['expiry']:
					#peerObjs[target_peer].send_msg(peerObjs[payer_id],pay_hash)
					del peerObjs[payer_id].created_htlc[pay_hash]
				else:
					msg['trace'][target_peer] = datetime.datetime.now()
					peerObjs[target_peer].forward_htlc.put(msg)
			else:
				print('Error msg in channel %s'%self.channelID)