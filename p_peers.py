import numpy as np
import datetime,time,threading
from multiprocessing import Process,Lock,Manager,Queue
#from multiprocessing.managers import BaseManager,NamespaceProxy
from datetime import timedelta
from p_mailbox import Mailbox
from payments import payment
from a_core import Pay_agent
import scipy.stats as ss
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
		self.pay_rate = self.manage.Value('i',0)
		self.count_Txs = self.manage.Value('i',0)
		#self.record_rate = self.manage.list()
		#record pays as a receiver
		#self.lastHop_htlc = []
		#queue in which all htlc needs to be forwarded
		self.forward_htlc = Queue(30)
		
		#self payments process
		self.pays = Process(target=self.send_payment,args=(lock,))
		self.Num_TS = self.manage.Value('i',1)

		self.pay_agent = None
		#learning process
		self.learn = None
		#self.time_sync = self.manage.Value(datetime.datetime,None)

		#priority queue
		self.mailbox = {}
		self.mailbox_process_rate = queue_rate
		self.mailbox_queue_size = queue_size
		#forwarding process
		self.switch = None

		#file path
		self.save_reward = './records/peer'+str(self.peerID)+'_Rewards.txt'
		self.save_rate = './records/peer'+str(self.peerID)+'_Rate.txt'

		#shared msg
		#self.msg = Value('i',0)
		
	def init_payAgent(self,num_priorities,peerObjs,Num_pairs,learning_method):
		self.fee_limited = self.pay_info['fee_limited']
		self.pay_agent = Pay_agent(
			Route=self.pay_info['route'],
			fee_limited = self.fee_limited,
			ts_perEpisode = 100,
			BATCH_SIZE=128,
			fresh_time=1,
			payerID=self.peerID,
			num_cooporator=Num_pairs)
		#init agent env
		self.pay_agent.init_env(num_priorities,self.fees_info)
		#learning thread
		#self.learn = threading.Thread(target=self.learning,args=(peerObjs,))
		self.learn = Process(target=self.learning,args=(peerObjs,learning_method))


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
	def learning(self,peerObjs,learning_method):
		print('Launch learning process...')
		if learning_method == 'DQN':
			self.pay_agent.init_dqn()
		elif learning_method == 'DDPG':
			self.pay_agent.init_ddpg()
		else:
			print('No learning method')
		time.sleep(5)
		var = 3  # control exploration
		r_set = []
		count_success = 0
		ep_reward = 0
		avg_fee = 0
		avg_time = 0
		ep_loss = 0
		self.count_Txs.value = 0
		Txs_inPrePeriod = 0
		print('Learning started...')
		#self.pays.start()
		while True:	
			if self.Num_TS.value >=self.pay_agent.env.TS_inEpisode:

				r_set.append(ep_reward)
				print('Episode:\t', len(r_set), '\tReward:\t' ,ep_reward)
				#with open('./records/peer'+str(self.peerID)+'_rate.txt','a') as f:
				#	for i in self.record_rate:
				#		f.write(str(i)+' ')
				#	f.write('\n')
				#self.record_rate[:] = []
				#		f.write('Time:\t'+ str(key)+'\tRate:\t'+str(self.achieved_rate[key])+'\n')
				avg_fee = avg_fee/self.pay_agent.env.TS_inEpisode
				avg_time = avg_time/self.pay_agent.env.TS_inEpisode
				Txs_inPeriod = self.count_Txs.value - Txs_inPrePeriod
				with open(self.save_reward,'a') as f:
					f.write('Episode:\t'+ str(len(r_set))+
						'\tCount Txs:\t'+str(Txs_inPeriod)+
						'\tSuccess:\t'+str(count_success)+
						'\tAvg time:\t'+str(avg_time)+
						'\tAvg fees:\t'+str(avg_fee)+
						'\tReward:\t'+str(ep_reward)+
						'\n')
				#self.pay_agent.dqn.save(str(self.peerID))
				ep_reward = 0
				count_success = 0
				ep_loss = 0
				avg_fee = 0
				Txs_inPrePeriod = self.count_Txs.value
				#self.pay_agent.action_set = {}
				lock.acquire()
				self.Num_TS.value = 0
				self.count_Txs.value = 0
				lock.release()
				print('created htlc:',len(self.created_htlc))
				print('env settle times:',len(self.pay_agent.env.settle_times))
				print('env payment sets:',len(self.pay_agent.env.payment_sets))
			else:
				#lock.acquire()
				#get the action of this timeslot a_t
				a_t = 0
				fee = 0
				if learning_method =='DQN':
					a_t,fee = self.pay_agent.step_dqn()
					#fee_delta = fee - self.fee_recorded
					#self.fee_recorded = fee
				elif learning_method =='DDPG':
					a_t,fee = self.pay_agent.step_ddpg(var)
				else:
					print('No learning method')
				#total_fee = sum([self.fees_info[j][a_t[i]] for i,j in enumerate(self.pay_info['route'][1:])])
				self.share_msg(self.peerID,a_t,peerObjs)
				#lock.release()

				time.sleep(self.pay_agent.fresh_time*self.accelerate)

				lock.acquire()
				if learning_method =='DQN':
					r,Avg_Time,num_pays= self.pay_agent.dqn_learning(self.count_Txs.value,self.Num_TS.value,fee,ep_loss)
				elif learning_method =='DDPG':
					r,achieve_rate,num_pays= self.pay_agent.ddpg_learning(var,self.count_Txs.value,self.Num_TS.value,fee)
				else:
					print('No learning method')
				lock.release()

				count_success += num_pays
				#print('Peer:',self.peerID,' Round: ',self.Num_TS.value,' Count success Txs:',count_success, 'Current reward:',r)
				ep_reward += r
				avg_fee += fee
				avg_time += Avg_Time


	#send record info and first hop for self payments
	def send_payment(self,lock):
		if self.pay_info == {}:
			pass
		else:
			var_pair = self.pay_info['pair']
			var_route = [x for x in self.pay_info['route']]
			var_count = 0
			self.pay_rate.value = self.pay_info['rate']
			#self.record_rate.append(self.pay_rate.value)
			#current_time = datetime.datetime.now()
			while True:
				if var_count < self.pay_rate.value:
					var_demand=datetime.timedelta(seconds=self.pay_info['demand'])
					#priority set
					p_sets = []
					if self.pay_agent == None:
						p_sets = [x for x in self.pay_info['p_set']]
					else:
						p_sets = [x for x in self.pay_agent.env.priorities]
					#Own pays have the top priority: 0
					p_sets.insert(0,0)
					crt_time = datetime.datetime.now()
					expiry = crt_time + var_demand
					new_pay = payment(
						pair = var_pair,
						crt_time = crt_time,
						priorities = p_sets,
						route = var_route,
						expiry = expiry,
						pay_rate = self.pay_rate.value)
					new_pay.total_fee = new_pay.get_total_fee(self.fees_info,p_sets)
					self.ns.df = new_pay
					if self.pay_agent != None:
						new_pay.env_TS = self.pay_agent.env.collect_pays(self.ns,lock)
					lock.acquire()
					self.created_htlc[new_pay.pay_hash] = new_pay.env_TS
					lock.release()

					#insert it into mailbox queue to send
					forward_pay_info = {}
					forward_pay_info['payer'] = self.peerID
					forward_pay_info['crt_time'] = new_pay.pay_create_time
					forward_pay_info['pay_hash'] = new_pay.pay_hash
					forward_pay_info['r_hop'] = new_pay.route
					forward_pay_info['p_set'] = new_pay.priorities
					forward_pay_info['expiry'] = new_pay.expiry
					forward_pay_info['trace'] = {}
					#print(forward_pay_info)
					#communication  between two process
					circuit = forward_pay_info['r_hop'][0]
					self.mailbox[circuit].htlc_in(forward_pay_info)
					t_delta = (datetime.datetime.now()-crt_time).total_seconds()
					var_count += 1
					self.count_Txs.value += 1
					if t_delta < self.accelerate/self.pay_rate.value:
						time.sleep(self.accelerate/self.pay_rate.value-t_delta)
				else:
					lock.acquire()
					self.Num_TS.value += 1
					lock.release()
					var_count = 0
					self.pay_rate.value = self.pay_info['rate'] + self.disc_normal()
					#print('Peer:%s\tRaye:%s'%(self.peerID,self.pay_rate.value))
					#self.record_rate.append(self.pay_rate.value)
					#time_delta = (current_time-time_delta).total_seconds()
					#time.sleep(self.accelerate)

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
					pay_time = float((current_time - msg['crt_time']).total_seconds())
					self.send_msg(peerObjs[payer_id],pay_hash,pay_time)
				else:
					circuit = msg['r_hop'][0]
					self.mailbox[circuit].htlc_in(msg)
			else:
				del peerObjs[payer_id].created_htlc[pay_hash]




	#send msg to payer, is the process to unlock the htlc
	# step by step in LND.
	#def send_msg(self,peerObj,t,p_hash,trace,lock):
	def send_msg(self,peerObj,p_hash,pay_time):
		#send msg to env for reward
		pay_ts = peerObj.created_htlc[p_hash]
		if peerObj.pay_agent!= None:
			lock.acquire()
			peerObj.pay_agent.env.check_pays(p_hash,pay_ts,pay_time)
			lock.release()
		del peerObj.created_htlc[p_hash]

	#broadcast necessary mesege for cooporation
	def share_msg(self,peerID,msg,peerObjs):
		for peer in peerObjs:
			if peerObjs[peer].pay_agent != None:
				#check time
				#record msg by peerid
				#lock.acquire()
				peerObjs[peer].pay_agent.action_set[peerID] = msg
				#lock.release()

	#define discrete normal distribution
	def disc_normal(self,var_size = 1,floating = 4):
		x = np.arange(-floating, floating)
		xU, xL = x + 0.5, x - 0.5
		prob = ss.norm.cdf(xU, scale = 3) - ss.norm.cdf(xL, scale = 3)
		prob = prob / prob.sum() #normalize the probabilities so their sum is 1
		nums, = np.random.choice(x, size = var_size, p = prob)
		return nums
