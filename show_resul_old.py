import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pylab import *

data_ttl_tx = {}
data_suc_tx = {}
data_fee = {}
Pairs = []
read_payInfo = open("./lnd/PBLND-simu-main/payment_info.txt","r")
for lines in read_payInfo.readlines():
    linesContent = lines.strip().split('\t')
    if linesContent != '':
        temp_pair = eval(linesContent[0])
        Pairs.append(temp_pair)
read_payInfo.close()

for i in Pairs:
    #File_path = './records/new_data20210120/R20/Records_avgR84_round1000/peer'+str(i[0])+'_Rate.txt'
    File_path = './records/new_data20210120/DiffNum_priorities/ProcessR20_pty6/peer'+str(i[0])+'_Rate.txt'
    temp_ttl_tx = []
    temp_suc_tx = []
    temp_fee = []
    with open(File_path,'r') as f:
        for lines in f.readlines():
            linesContent = lines.strip().split('\t')
            if linesContent != '':
                temp_ttl_tx.append(float(linesContent[3]))
                temp_suc_tx.append(float(linesContent[5]))
                temp_fee.append(float(linesContent[9]))

    data_ttl_tx[i[0]] = temp_ttl_tx
    data_suc_tx[i[0]] = temp_suc_tx
    data_fee[i[0]] = temp_fee

x=0
sucR_data = []
tps_data = []
fees = []

Start_point = 5
End_point = 30

while x <=End_point:
    temp_sucR = 0
    temp_tps = 0
    temp_fee = 0
    for i in Pairs:
        if len(data_ttl_tx[i[0]])>=End_point:
            temp_sucR += data_suc_tx[i[0]][x]/data_ttl_tx[i[0]][x]
            temp_tps += data_suc_tx[i[0]][x]
            temp_fee += data_fee[i[0]][x]
    sucR_data.append(temp_sucR/len(Pairs))
    tps_data.append(temp_tps)
    fees.append(temp_fee/len(Pairs))
    x += 1

err_rate = (max(sucR_data[(Start_point+1):])-min(sucR_data[(Start_point+1):]))/2
avg_rate = sum(sucR_data[(Start_point+1):])/(End_point-Start_point)
err_fee = (max(fees[(Start_point+1):])-min(fees[(Start_point+1):]))/2
avg_fee = sum(fees[(Start_point+1):])/(End_point-Start_point)
print('R_ERR: %s\tAVG_R: %s'%(err_rate,avg_rate))
print('F_ERR: %s\tAVG_F: %s'%(err_fee,avg_fee))
avg_tps = sum(tps_data[(Start_point+1):])/(End_point-Start_point)
print('TPS: %s'%(avg_tps/100))
rc('font',size = 18)
xlabel('Check points')
ylabel('Rewards')
df = pd.DataFrame(tps_data)
plt.plot(df[0],'lightblue',df[0].rolling(5).mean(),'b') 
#plt.plot(reward)
plt.show()

'''
x=0
sum_reward = []
sum_fee = []
while x <=830:
    temp_reward = 0
    temp_fee = 0
    for i in Pairs:
        if len(rewards[i[0]])>=830:
            temp_reward += rewards[i[0]][x]
            temp_fee += Fees[i[0]][x]
    #temp_reward = temp_reward/temp_fee
    sum_fee.append(temp_fee)
    sum_reward.append(temp_reward)
    x += 1

avg_rate = sum(sum_reward[201:])/63000
print(avg_rate)

plt.plot(sum_reward) 
plt.show()


for i in Pairs:
    plt.plot(rewards[i[0]])
    plt.show() 
'''

def norm_metric(v,num_pty):
    low = 2
    high = 2**(num_pty)
    v_range = [low,high] 
    norm_v = round((v-v_range[0])/(v_range[1]-v_range[0]),2)
    return norm_v
