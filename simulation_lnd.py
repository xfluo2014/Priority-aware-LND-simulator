from channels import channel
from p_peers import peer
from payments import payment
import time,datetime
import random
import numpy as np
import networkx as nx
from a_core import Pay_agent

Num_nodes = 50
Num_pairs = 15
Num_priority = 3
queue_size = 120
queue_rate = 20
learning_method = 'DQN'

'''
read graph, pair, channel info from files
'''

#read graph info
G=nx.read_edgelist("graph.txt",nodetype=int)
#G.edge is the channel set, a channel contains 2-direction hops.
Hop = list(G.edges)
for i in list(G.edges):
    Hop.append(tuple(reversed(i)))

b_uv = {}
w_uv = {}
d_uv = {}
#read hop info
read_hopInfo = open("hopInfo.txt","r")
for lines in read_hopInfo.readlines():
    linesContent = lines.strip().split('\t')
    if linesContent != '':
        temp_pair = eval(linesContent[0])
        b_uv[temp_pair] = eval(linesContent[1])
        w_uv[temp_pair] = eval(linesContent[2])
        d_uv[temp_pair] = float(linesContent[3])
read_hopInfo.close()
#read payment info
Pairs = []
Pay_rate = {}
Fee_limited = {}
D_ij = {}
read_payInfo = open("payment_info.txt","r")
for lines in read_payInfo.readlines():
    linesContent = lines.strip().split('\t')
    if linesContent != '':
        temp_pair = eval(linesContent[0])
        Pairs.append(temp_pair)
        Pay_rate[temp_pair] = eval(linesContent[1])
        Fee_limited[temp_pair] = eval(linesContent[2])
        D_ij[temp_pair] = eval(linesContent[3])
read_payInfo.close()

#routes of each pair
Routes = {}
read_path = open("path.txt","r")
index_p = 0
for lines in read_path.readlines():
    linesContent = lines.strip().split('\t')
    temp_list = []
    if linesContent != '':
        for h in linesContent:
            temp_list.append(eval(h))
    Routes[Pairs[index_p]] = [temp_list]
    index_p = index_p + 1
read_path.close()
#print(Routes)

'''
functions used in main process
'''

payments_info = []
#To prepare payment info for each payer
for i in range(Num_nodes):
	#check any payments sent by this node
	payments = [x for x in Pairs if x[0] == i]
	pay_info = {}
	if payments != []:
		pay = payments[0]
		pay_info['pair'] = pay
		#pay_info['num_pays'] = 1000
		pay_info['rate'] = Pay_rate[pay]
		pay_info['route'] = Routes[pay][0]
		pay_info['p_set'] =  (Num_priority-1)*np.ones(len(pay_info['route'])-1,dtype=int)
		pay_info['demand'] = D_ij[pay]
		pay_info['fee_limited'] = Fee_limited[pay]
	payments_info.append(pay_info)

#print(payments_info)

<<<<<<< HEAD

=======
#define discrete normal distribution
def disc_normal(lb,ub,var_size):
	x = np.arange(lb, ub+1)
	xU, xL = x + 0.5, x - 0.5
	prob = ss.norm.cdf(xU, scale = 3) - ss.norm.cdf(xL, scale = 3)
	prob = prob / prob.sum() #normalize the probabilities so their sum is 1
	nums = np.random.choice(x, size = var_size, p = prob)
	return nums
>>>>>>> origin/Version0224

#To dynamiclly adjust the payment info
'''
def adjust_pay_info(peerObj):
	var_rate = np.random.poisson(5,1)
	var_rate =np.clip(var_rate,2,10)
	#var_pays = random.randrange(500,801,100)
	var_p_set = np.random.randint(low = 1,high = Num_priority-1,\
                     size=(len(peerObj.pay_info['route'])),dtype=np.int64)
	var_demand = random.randrange(5,21,5)
	#update payment info in peer object 
	#peerObj.pay_info['rate'] = var_rate
	peerObj.pay_info['p_set'] = var_p_set
	#peerObj.pay_info['demand'] = var_demand
'''	

def cal_avg_payTime(pays_list,num_complete):
	sum_pay_time = 0
	for i in range(num_complete):
		sum_pay_time += pays_list[i]['pay_time']
	return sum_pay_time/num_complete


print('Init peers object')
Peers = {}
for i in range(Num_nodes):
	Peers[i] = peer(i,payments_info[i],queue_rate,queue_size)
	Peers[i].init_fee_policy(Num_priority)
	#print(Peers[i].pay_info)

print('Init channels object')
Channels = {}
for h in list(G.edges):
	Channels[h] = channel(d_uv[h],h,queue_size*2)

print('Init channels manager')
#launch channel manager process
for h in list(G.edges):
	Channels[h].init_manager(Peers)


print('Init peers forward process')
#launch peer mailbox and switch process
for i in range(Num_nodes):
	hops = [h for h in list(G.edges) if i in h]
	built_channels = []
	for h in hops:
		built_channels.append(Channels[h])
	Peers[i].init_chan(built_channels,Peers,Num_priority)


print('Init peers fees list')
#get all peers' forwarding fees and put into a list
list_fees = []
for i in Peers:
	p_fees = []
	for j in range(Num_priority):
		p_fees.append(Peers[i].fee_policy[j])
	list_fees.append(p_fees)

Processes = []
#queue_set = []

#Only the main pair has the learning process
#Peers[main_peer].init_payAgent(Num_priority)
#Processes.append(Peers[main_peer].learn)

for i in Peers:
	Processes.append(Peers[i].switch)
	for j in Peers[i].mailbox.keys():
		Processes.append(Peers[i].mailbox[j].forward)
	#queue_set.append(Peers[i].forward_htlc)
	#queue_set.append(Peers[i].mailbox.p_queue)
	Peers[i].init_fee_info(list_fees)


print('Init channels')
for j in Channels:
	Processes.append(Channels[j].manager)
	#queue_set.append(Channels[j].htlc_queue)

print('Init multi agent')
#main_payer = [(48, 23)]
for i in Pairs:
	#print('peer to pay',i[0])
	while Peers[i[0]].pay_agent == None:
		Peers[i[0]].init_payAgent(Num_priority,Peers,len(Pairs),learning_method)
	Processes.append(Peers[i[0]].learn)

#print(Peers[main_peer].pay_info)
if __name__ == "__main__":
	#get the time stemp of start time
	start_time = time.time()
	print('PCN simulation start at:',datetime.datetime.now())
	#launch payment process for each payer
	for i in Peers:
		Processes.append(Peers[i].pays)

	print('Launch all process')
	for t in Processes:
		#t.setDaemon(True)
		t.start()
	#main_.start(
	for t in Processes:
		t.join()
	#main_.join()
