import random

class payment:
	def __init__(self,pair,crt_time,priorities,route,expiry,pay_rate):
		self.pay_from_to = pair
		self.payID = hash('pay'+ str(self.pay_from_to[0]) + '-' + str(self.pay_from_to[1])+str(random.random()))
		self.amt = 1
		self.rate = pay_rate
		self.pay_create_time = crt_time
		self.preimage = str(self.pay_from_to[0])+'pay'+str(self.amt)+'to'+str(self.pay_from_to[1])+'at time'+str(self.pay_create_time)
		self.pay_hash = hash(self.preimage)
		self.route = [x for x in route]
		self.total_fee = 0
		self.priorities = [int(x) for x in priorities]
		self.trace = {}
		self.pay_time = None
		self.success = None
		#self.failMsg = None
		#expiry time
		self.expiry = expiry
		#To avoid a long queue, we clear the used pays from 
		# the created htlc queue when it's ready for clear.
		#[Get the reward for learning, Receive the pay result]
		#self.ready = [False,False]
		#time slot that collected by agent
		self.env_TS = None
		
	
	def get_total_fee(self,fee_list,priorities):
		intermediate_users =  [int(self.route[x][0]) for x in range(1,len(self.route))]
		fee = sum([fee_list[j][priorities[i]] for i,j in enumerate(intermediate_users)])
		return fee

