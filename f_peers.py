import numpy as np
import datetime,time,threading
from multiprocessing import Process,Lock,Manager,Queue
#from multiprocessing.managers import BaseManager,NamespaceProxy
from datetime import timedelta
from f_mailbox import Mailbox
from payments import payment
import copy,gc

lock = Lock()

class peer:
	def __init__(self,var_id,pay_info,queue_rate,queue_size):
		self.accelerate = 0.8
		self.peerID = var_id
		#payment info [pair, num_pays, route, p_set, demand]
		self.pay_info = copy.deepcopy(pay_info)

		#self.pay_rate = self.pay_info['rate']
		self.channels = []
		#record all peers' forwarding fees
		self.fees_info = []
		#the own fee policy
		self.fee_policy = []
		#fee limitation of own Txs
		self.fee_limited = 0
		#record pays as a sender
		self.manage = Manager()
		#fee_recorded records the total forwarding fee of the last decision
		#self.fee_recorded = self.manage.Value('i',0)
		self.ns = self.manage.Namespace()
		self.created_htlc = self.manage.dict()
		#record pays as a receiver
		#self.lastHop_htlc = []
		#queue in which all htlc needs to be forwarded
		self.forward_htlc = Queue(30)
		
		#self payments process
		self.pays = Process(target=self.send_payment,args=(lock,))
		self.achieved_rate = self.manage.dict()
		self.Num_TS = self.manage.Value('i',1)
		#self.time_sync = self.manage.Value(datetime.datetime,None)

		self.env_TS = 0
		self.record = None

		#FIFO queue
		self.mailbox = {}
		self.mailbox_process_rate = queue_rate
		self.mailbox_queue_size = queue_size
		#forwarding process
		self.switch = None

		#file path
		self.save_rate = './records/f_peer'+str(self.peerID)+'_Rate.txt'

		#shared msg
		#self.msg = Value('i',0)

	def init_chan(self,built_chans,peerObjs,num_priorities):
		self.channels = [x for x in built_chans]
		#priority queue
		for chan in self.channels:
			conn_peer, = [x for x in list(chan.hop) if x!= self.peerID]
			circuit = tuple([self.peerID,conn_peer])
			self.mailbox[circuit] = Mailbox(self.peerID,chan,peerObjs,
				self.mailbox_process_rate,
				num_priorities,
				self.mailbox_queue_size,
				self.accelerate,
				self.fee_policy)
		#forwarding process
		self.switch = Process(target = self.process_msg, args=(peerObjs,))
		self.record = Process(target=self.recording,args=(peerObjs))

	#case we simplify the payment amount to a determined fund
	#we change the pricing scheme which required the base fee and fee rate
	def init_fee_policy(self,priorities):
		base_fee = 0 #satoshi
		fee_rate = 2
		fees = []
		for i in range(priorities):
			fee_i = base_fee + 1000*(fee_rate**(i+1))
			weighted_fee_i = fee_i/1000
			fees.append(int(weighted_fee_i))
		self.fee_policy = [x for x in reversed(fees)]

	def init_fee_info(self,fee_list):
		self.fees_info = [x for x in fee_list]

	#agent learns and generates prorities set
	def recording(self,peerObjs):
		print('Launch recording process...')
		loop = 0
		count_success = 0
		#self.pays.start()
		while True:	
			if self.Num_TS.value >=100:
				print('Episode:\t', loop, '\tReward:\t' ,count_success)
				#with open(self.save_rate,'a') as f:
				#	for key in self.achieved_rate.keys():
				#		f.write('Time:\t'+ str(key)+'\tRate:\t'+str(self.achieved_rate[key])+'\n')
				with open(self.save_rate,'a') as f:
					f.write('Episode:\t'+ str(loop)+
						'\tSuccess:\t'+str(count_success)+
						'\n')
				#self.pay_agent.dqn.save(str(self.peerID))
				loop += 1
				count_success = 0
				#self.pay_agent.action_set = {}
				lock.acquire()
				#self.pay_agent.env.records = {}
				#self.pay_agent.env.reset(self.pay_agent.state,self.pay_agent.cooporator)
				#self.pay_agent.observation = np.append(self.pay_agent.state.fee_state,self.pay_agent.state.desion_state)
				self.Num_TS.value = 0
				lock.release()

			else:
				time.sleep(self.accelerate)
				count_success += num_pays


	#send record info and first hop for self payments
	def send_payment(self,lock):
		if self.pay_info == {}:
			pass
		else:
			var_pair = self.pay_info['pair']
			var_route = [x for x in self.pay_info['route']]
			var_count = 0
			pay_list = []
			#current_time = datetime.datetime.now()
			while True:
				if var_count < self.pay_info['rate']:
					var_demand=datetime.timedelta(seconds=self.pay_info['demand'])
					#priority set
					p_sets = [x for x in self.pay_info['p_set']]
					#Own pays have the top priority: 0
					p_sets.insert(0,0)
					crt_time = datetime.datetime.now()
					expiry = crt_time + var_demand
					new_pay = payment(var_pair,crt_time,p_sets,var_route,expiry,self.fee_limited)
					new_pay.total_fee = new_pay.get_total_fee(self.fees_info,p_sets)
					temp_pay = {}
					temp_pay[p_hash] = new_pay.pay_hash
					temp_pay[success] = False
					pay_list.append(temp_pay)

					#insert it into mailbox queue to send
					forward_pay_info = {}
					forward_pay_info['payer'] = self.peerID
					forward_pay_info['pay_hash'] = new_pay.pay_hash
					forward_pay_info['r_hop'] = new_pay.route
					forward_pay_info['expiry'] = new_pay.expiry
					forward_pay_info['trace'] = {}
					#print(forward_pay_info)
					circuit = forward_pay_info['r_hop'][0]
					self.mailbox[circuit].htlc_in(forward_pay_info)
					
					var_count += 1
					time.sleep(self.accelerate/self.pay_info['rate'])
				else:
					lock.acquire()
					self.Num_TS.value += 1
					lock.release()
					lock.acquire()
					self.created_htlc[self.env_TS] = pay_list
					lock.release()
					pay_list = []
					var_count = 0


	#receive link msg
	def process_msg(self,peerObjs):
		while True:
			msg = self.forward_htlc.get(block=True)
			current_time = datetime.datetime.now()
			payer_id = msg['payer']
			pay_hash = msg['pay_hash']
			trace = msg['trace']
			if current_time <=msg['expiry']:
				if msg['p_set'] == []:
					#self.lastHop_htlc.append(msg)
					#send payment info back to payer
					self.send_msg(peerObjs[payer_id],pay_hash)
				else:
					circuit = msg['r_hop'][0]
					self.mailbox[circuit].htlc_in(msg)
			else:
				del peerObjs[payer_id].created_htlc[pay_hash]




	#send msg to payer, is the process to unlock the htlc
	# step by step in LND.
	#def send_msg(self,peerObj,t,p_hash,trace,lock):
	def send_msg(self,peerObj,p_hash):
		#send msg to env for reward
		pay_ts = peerObj.created_htlc[p_hash]
		if peerObj.pay_agent!= None:
			lock.acquire()
			peerObj.pay_agent.env.check_pays(p_hash,pay_ts)
			lock.release()
		#else:
		#	pay.success = False
		del peerObj.created_htlc[p_hash]

