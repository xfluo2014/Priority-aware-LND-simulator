import math
import gym
from datetime import datetime,timedelta
from multiprocessing import Manager
from gym import spaces, logger
from gym.utils import seeding
import numpy as np
import copy,gc


class Pay_env():
    def __init__(self,episode_len,route,num_priority,fee_info,num_cooporator):
        #Because payment rate is varying, the episode depends on 
        #the number of cumulative payments.
        self.TS_inEpisode = episode_len
        self.intermediate_users = [route[x][0] for x in range(1,len(route))]
        self.num_relayer = len(self.intermediate_users)
        #self.state_len =  self.num_relayer if num_cooporator< self.num_relayer else num_cooporator
        self.num_priority = num_priority

        self.fee_info = copy.deepcopy(fee_info)

        #payment sets ordering by time stamp
        self.manage = Manager()
        #the time stamp to update the priorities 
        self.TS = self.manage.Value(datetime,datetime.now())
        self.single_Tx = self.manage.Namespace()
        self.payment_sets = self.manage.dict()
        self.current_succ = self.manage.dict()
        #self.payment_set = manage.list()
        self.priorities = self.manage.list()
        self.records = {}
        self.action_space = spaces.Box(low= 0,high= self.num_priority-1,shape=(self.num_relayer,),dtype=np.int64)
        self.observation_space = []
        #
        fee_space = spaces.Box(low= self.get_low_fees(),high=self.get_high_fees(),dtype=np.int64)
        self.observation_space.append(fee_space)


        desion_space = spaces.Box(low=0,high=+np.inf,shape = (num_cooporator,),dtype=np.int64)
        self.observation_space.append(desion_space)

        #the settle time is the last demand expiry time{ (key)timestamp: (value)settle time}
        self.settle_times = self.manage.dict()
        self.seed()
        self.state_dim = 0
        self.action_dim = self.action_space.shape[0]
        self.action_bound = self.action_space.high

    def get_low_fees(self):
        low_fees = []
        for i in self.intermediate_users:
            low_fees.append(min(self.fee_info[i]))
        #if len(low_fees) < self.state_len:
            #extension = np.zeros(self.state_len-len(low_fees))
            #low_fees.extend(extension)
        return np.array(low_fees,dtype=np.int64)

    def get_high_fees(self):
        high_fees =[]
        for i in self.intermediate_users:
            high_fees.append(max(self.fee_info[i]))
        #if len(high_fees) < self.state_len:
            #extension = np.zeros(self.state_len-len(high_fees))
            #high_fees.extend(extension)
        return np.array(high_fees,dtype=np.int64)

    #update payments set
    def collect_pays(self,ns,lock):
        payObj = ns.df
        self.single_Tx.p_rate = payObj.rate
        self.single_Tx.payHash = payObj.pay_hash
        self.single_Tx.success = False
        self.single_Tx.pay_time = timedelta(seconds=100)
        #If the transaction rate is treated as the demand, we must ensure the transaction completed in d seconds.
        expect_settle_time = payObj.expiry
        lock.acquire()
        temp_ts = self.TS.value
        #print('time slot env',temp_ts)
        if temp_ts not in self.payment_sets.keys():
            self.payment_sets[temp_ts] = self.manage.list()
        self.payment_sets[temp_ts].append(copy.deepcopy(self.single_Tx))
        #self.single_Tx.clear()
        if temp_ts in list(self.settle_times.keys()):
            if self.settle_times[temp_ts]<expect_settle_time:
                self.settle_times[temp_ts]=expect_settle_time
        else:
            self.settle_times[temp_ts]=expect_settle_time
        lock.release()
        return temp_ts


    def check_pays(self,pay_hash,ts,pay_time):
        #print(ts,self.payment_sets)
        if ts in self.payment_sets.keys():
            if self.payment_sets[ts]!= []:
                idx_pay, = [i for i,x in enumerate(self.payment_sets[ts]) if x.payHash == pay_hash]
                #print('target pay',pay)
                temp_ns = self.payment_sets[ts][idx_pay]
                temp_ns.success = True
                temp_ns.pay_time = pay_time
                self.payment_sets[ts][idx_pay] = temp_ns
                self.current_succ[self.TS.value] += 1

    #update payment priorities
    def set_priorities(self,priorities):
        self.priorities[:] = [x for x in priorities]
        #print('Priorities:',self.priorities)


    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    #success ratio or  achieved transaction rate
    def get_metric(self,k):
        #due to the varying demand, we use success 
        # ratio to calculate the reward
        count_succ = 0
        pay_times = []
        for pay in self.payment_sets[k]:
            if pay.success == True:
                pay_times.append(pay.pay_time)
                count_succ +=1
        #calculate avg rate
        Achieve_rate = 0
        #True pay rate must less than the sending rate
        rate_limited = self.payment_sets[k][0].p_rate
        avg_pay_time = 0
        if len(pay_times)>0:
            avg_pay_time = sum(pay_times)/len(pay_times)
            cal_rate = round(count_succ/avg_pay_time,2) 
            Achieve_rate = cal_rate if cal_rate < rate_limited else rate_limited
        #suss_ratio = count_succ/len(self.payment_sets[k])
        return Achieve_rate,count_succ,avg_pay_time


    #calculate the reward of k-th set payments with 
    #the success ratio and averaged forwarding fee
    def cal_reward(self,k):
        #The weight of each factors
        #weight_suss = 100
        weight_rate = 0.8
        weight_fee = 1 - weight_rate
        #suss_ratio = self.get_success_ratio(k,pay_list)
        #rate_reward = 0
        Achieve_rate,count_succ,avg_pay_time = self.get_metric(k)
        fee = self.records[k][2]

        norm_rate = round(Achieve_rate/self.payment_sets[k][0].p_rate,2)

        fee_range = [sum(self.get_low_fees()),sum(self.get_high_fees())] 
        norm_fee = round((fee-fee_range[0])/(fee_range[1]-fee_range[0]),2)
        reward = weight_rate * norm_rate - weight_fee * norm_fee
        #the record will clear every episode, so if the key of k was clear
        #we cannot use index k to record the reward, we need to drop it.
        #and use a bool value to indicate the result.
        self.records[k][2] = reward
        del self.payment_sets[k]
        del self.settle_times[k]
        return reward,avg_pay_time,count_succ
        

    def get_record(self,k):
        s = np.array([x for x in self.records[k][0]])
        a = self.records[k][1]
        r = self.records[k][2]
        s_ = np.array([x for x in self.records[k][3]]) if len(self.records[k][3])  else []
        assert len(s) == len(s_), "S:%s has different length with S':%s"%(s,s_)
        #print('MDP:',self.records[k])
        del self.records[k]
        return s,a,r,s_

    def record(self,ob,a,f,ob_):
        s = np.array([x for x in ob])
        #assert len(s) == self.state_dim, "Dimension error for state s:%s(req: %s)"%(s,self.state_dim)
        a = copy.deepcopy(a)
        r = f
        t = self.TS.value
        #update current Tx state
        curr_rate = self.current_succ[t]
        self.TS.value = datetime.now()
        self.current_succ[self.TS.value] = 0
        del self.current_succ[t]
        #cum_succ_Txs = cum_succ_Txs + curr_rate
        #cum_succ_ratio = 0
        #if cum_sent_Txs != 0:
        #    cum_succ_ratio = cum_succ_Txs / cum_sent_Txs
        Tx_s = np.array([curr_rate])
        ob_ = np.append(Tx_s,ob_)
        s_ = np.array([x for x in ob_])
        #assert len(s_) == self.state_dim, "Dimension error for state s_:%s(req: %s)"%(s_,self.state_dim)
        self.records[t] = [s,a,r,s_]
        return curr_rate,ob_
        #self.update_pays(k)
        #return self.state,self.rewards[timestamp],done,{}


    def reset(self,state,num_cooporator):
        #self.state = np.array(self.np_random.randint(low = 0,high = self.num_priority,\
        #             size=(self.num_relayer,)))
        p_set = (self.num_priority-1)*np.ones(self.num_relayer,dtype=int)
        #state.Tx_state.count_succ = 0
        state.Tx_state.curr_rate = 0
        tx_state = np.array([state.Tx_state.curr_rate])
        state.fee_state = np.array([self.fee_info[j][p_set[i]] for i,j in enumerate(self.intermediate_users)])
        state.pre_decision = np.zeros(num_cooporator,dtype=np.int64)
        self.state_dim = len(np.append(
            tx_state,
            np.append(state.fee_state,state.pre_decision)))
        self.set_priorities(p_set)
        self.TS.value = datetime.now()
        self.current_succ[self.TS.value] = 0
        self.payment_sets.clear()
        #self.payment_set[:] = []
        self.settle_times.clear()
        gc.collect()
