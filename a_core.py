import numpy as np
from a_env import Pay_env
from memory import Memory
from datetime import datetime
import DDPG
from DQN import DQN
import random,time
import utilities
from multiprocessing import Manager
#import tensorflow.compat.v1 as tf
#tf.disable_v2_behavior()
class TxState():
    def __init__(self):
        self.curr_rate = 0
        self.count_succ = 0

class Agentstate():
    def __init__(self):
        self.Tx_state = TxState()
        self.fee_state = []
        #actions of the last step
        self.pre_decision = []

#np.random.seed(1)
#tf.set_random_seed(1)
class Pay_agent():
    def __init__(self,Route,fee_limited,ts_perEpisode,BATCH_SIZE,fresh_time,payerID,num_cooporator):
        # Payment paramaters
        self.route = Route
        self.fee_limit = fee_limited
        self.episode_len = ts_perEpisode
        self.state = Agentstate()
        # ENV paramaters
        self.env= None
        self.payer = payerID
        self.n_actions = np.power(3,len(self.route)-1)
        self.weight_file = './save/DQN'+str(payerID)
        self.fresh_time = fresh_time
        #Memeory paramaters
        self.MEMORY_CAPACITY = 10000
        self.M = None
        # DDPG paramaters
        self.actor = None
        self.critic = None
        self.Batchsize = BATCH_SIZE

        #DQN paramaters
        self.dqn = None

        manage = Manager()
        self.observation = manage.list()
        self.action = manage.Value('i',0)
        self.ddpg_action = manage.list()
        #share msgs
        #Actions of other agents
        self.cooporator = num_cooporator
        self.action_set = manage.dict()

    #convert action idx to real action
    def idx2Act(self,idx,num_priority):
        real_action=[]
        while True:
            s=idx//num_priority  
            y=idx%num_priority  
            real_action=real_action+[y]
            if s==0:
                break
            idx=s
        while len(real_action)<self.env.num_relayer:
            real_action.append(0)
        real_action.reverse()
        return real_action

    def get_ob(self):
        peers = list(self.action_set.keys())
        peers.sort()
        decision = []
        for peer in peers:
            decision.append(self.action_set[peer])
        #self.action_set = {}
        if len(decision) == self.cooporator:
            self.state.pre_decision = np.array([x for x in decision])
        else:
            print('Lose msg from cooporators...')
        self.observation = np.append(self.state.fee_state,self.state.pre_decision)
        return self.observation

    def init_ddpg(self):
        self.env.seed(1)
        actor,critic,M = DDPG.init_env(self.env,self.MEMORY_CAPACITY)
        self.actor = actor
        self.critic = critic
        self.M = M
    
    def step_ddpg(self,var):
        a = self.actor.choose_action(self.observation)
        real_action = np.clip(np.round(np.random.normal(a, var)),0, self.env.num_priority-1)
        self.ddpg_action = real_action
        #convert the action to index
        idx= sum(j*pow(3,i)for i,j in enumerate(reversed(real_action)))
        assert self.env.action_space.contains(real_action), "%r (%s) invalid" % (real_action, type(real_action))
        #supply new scheme for incoming Tx
        self.env.set_priorities(real_action)
        #update state
        self.state.fee_state = np.array([self.env.fee_info[j][int(real_action[i])] for i,j in enumerate(self.env.intermediate_users)])
        total_fee = sum(self.state.fee_state)
        self.state.pre_decision = []
        return idx,total_fee

    def ddpg_learning(self,var,count_Txs,loop,fee):
        #current observation
        pre_ob = self.observation
        #observation of next step
        ob_ = self.get_ob()
        curr_rate,cum_succ_Txs,self.observation = self.env.record(
            ob = pre_ob,
            a = self.ddpg_action,
            f = fee,
            ob_ = ob_,
            cum_succ_Txs = self.state.Tx_state.count_succ,
            cum_sent_Txs = count_Txs)
        self.state.Tx_state.curr_rate = curr_rate
        self.state.Tx_state.count_succ = cum_succ_Txs
        r0,r1,r2 = 0,0,0
        if self.env.settle_times != None:
            TSidx_settle_times = list(self.env.settle_times.keys())
            for ts in TSidx_settle_times:
                if self.env.TS.value > self.env.settle_times[ts]:
                    r, achieve_rate,count_succ = self.env.cal_reward(ts)
                    r1 += achieve_rate
                    r2 += count_succ
                    m_s, m_a, m_r, m_s_ = self.env.get_record(ts)
                    if loop >= 10:
                        r0 += r
                        self.M.store_transition(m_s, m_a, m_r, m_s_)

                    if self.M.pointer > self.MEMORY_CAPACITY:
                        var *= .9995    # decay the action randomness
                        b_M = self.M.sample(self.Batchsize)
                        b_s = b_M[:, :self.env.state_dim]
                        b_a = b_M[:, self.env.state_dim: self.env.state_dim + self.env.action_dim]
                        b_r = b_M[:, -self.env.state_dim - 1: -self.env.state_dim]
                        b_s_ = b_M[:, -self.env.state_dim:]

                        self.critic.learn(b_s, b_a, b_r, b_s_)
                        self.actor.learn(b_s)

        return r0,r1,r2

    def init_env(self,num_priority,fee_info):
        self.env = Pay_env(
            episode_len=self.episode_len,
            route = self.route,
			num_priority = num_priority,
            fee_info = fee_info,
            num_cooporator=self.cooporator)
        self.env.reset(self.state,self.cooporator)
        tx_state = np.array([self.state.Tx_state.curr_rate,self.state.Tx_state.count_succ])
        self.observation = np.append(
            tx_state,
            np.append(self.state.fee_state,self.state.pre_decision))
        #self.observation =self.state.fee_state
        #return total_fee


    def init_dqn(self):
        #print('state_dim:',self.env.state_dim)
        self.M = Memory(self.MEMORY_CAPACITY)
        #print(self.observation)
        self.env.seed(1)
        self.dqn = DQN(self.payer,self.n_actions,self.env.state_dim)
        utilities.load_dqn_weights_if_exist(self.payer,self.dqn,self.weight_file)

    def step_dqn(self):
        #print(self.observation)
        self.action.value = self.dqn.choose_action(self.observation)
        real_action = self.idx2Act(self.action.value,self.env.num_priority)
        assert self.env.action_space.contains(real_action), "%r (%s) invalid" % (real_action, type(real_action))
        #supply new scheme for incoming Tx
        self.env.set_priorities(real_action)
        #update state
        self.state.fee_state = np.array([self.env.fee_info[j][real_action[i]] for i,j in enumerate(self.env.intermediate_users)])

        total_fee = sum(self.state.fee_state)
        self.state.pre_decision = []
        return self.action.value,total_fee

    def dqn_learning(self,count_Txs,loop,fee,loss):
        #current observation
        pre_ob = self.observation
        #observation of next step
        ob_ = self.get_ob()
        curr_rate,cum_succ_Txs,self.observation = self.env.record(
            ob = pre_ob,
            a = self.action.value,
            f = fee,
            ob_ = ob_,
            cum_succ_Txs = self.state.Tx_state.count_succ,
            cum_sent_Txs = count_Txs)
        self.state.Tx_state.curr_rate = curr_rate
        self.state.Tx_state.count_succ = cum_succ_Txs
        r0,r1,r2 = 0,0,0
        if self.env.settle_times != None:
            TSidx_settle_times = list(self.env.settle_times.keys())
            for ts in TSidx_settle_times:
                if self.env.TS.value > self.env.settle_times[ts]:
                    r, achieve_rate,count_succ = self.env.cal_reward(ts)
                    r1 += achieve_rate
                    r2 += count_succ
                    m_s, m_a, m_r, m_s_ = self.env.get_record(ts)
                    size = self.M.pointer
                    batch = random.sample(range(size), size) if size < self.Batchsize else random.sample(
                        range(size), self.Batchsize)
                    if loop >= 10:
                        r0 += r
                        self.M.remember(m_s, m_a, m_r, m_s_,False)
                    if self.M.pointer > self.MEMORY_CAPACITY/2:
                        #print('DQN learn')
                        history = self.dqn.learn(*self.M.sample(batch))
                        loss += history.history["loss"][0]
                    else:
                        loss = -1

        return r0,r1,r2
