import numpy as np
import pandas as pd
from pylab import *

Pairs = []
read_payInfo = open("payment_info.txt","r")
for lines in read_payInfo.readlines():
    linesContent = lines.strip().split('\t')
    if linesContent != '':
        temp_pair = eval(linesContent[0])
        Pairs.append(temp_pair)
read_payInfo.close()
'''
len_path = {}
read_pathInfo = open("path.txt","r")
for lines in read_pathInfo.readlines():
    linesContent = lines.strip().split('\t')
    temp_list = []
    if linesContent != '':
        for h in linesContent:
            temp_list.append(eval(h))
    len_path[temp_list[0][0]] = len(temp_list)
read_payInfo.close()
'''
def get_fee(f_path):
    data_ttl_tx = {}
    data_suc_tx = {}
    data_fee = {}
    for i in Pairs:
        File_path = f_path+'peer'+str(i[0])+'_Rate.txt'
        temp_ttl_tx = []
        temp_suc_tx = []
        temp_fee = []
        with open(File_path,'r') as f:
            for lines in f.readlines():
                linesContent = lines.strip().split('\t')
                if linesContent != '':
                    temp_ttl_tx.append(float(linesContent[3]))
                    temp_suc_tx.append(float(linesContent[5]))
                    #temp_fee.append(float(linesContent[9]))

        data_ttl_tx[i[0]] = temp_ttl_tx
        data_suc_tx[i[0]] = temp_suc_tx
        data_fee[i[0]] = temp_fee

    x=0
    sucR_data = []
    tps_data = []
    fees = []

    Start_point = 0
    End_point = 400

    while x <=End_point:
        temp_sucR = 0
        temp_tps = 0
        temp_fee = 0
        for i in Pairs:
            if len(data_ttl_tx[i[0]])>=End_point:
                temp_sucR += data_suc_tx[i[0]][x]/data_ttl_tx[i[0]][x]
                temp_tps += data_suc_tx[i[0]][x]
                #temp_fee += data_fee[i[0]][x]
        sucR_data.append(temp_sucR/len(Pairs))
        tps_data.append(temp_tps)
        fees.append(temp_fee/len(Pairs))
        x += 1
    return tps_data
file_paths = [
    './records/new_data20210120/R20/Records_avgR84_round839/',
    './records/new_data20210120/R20/Records_avgR84_round1000/',
    './OtherSch_lnd/records/EDF/R20/e_'
]
fees1 = get_fee(file_paths[0])
fees2 = get_fee(file_paths[1])
fees3 = get_fee(file_paths[2])
df1 = pd.DataFrame(x/100 for x in fees1)
df2 = pd.DataFrame(x2/100 for x2 in fees2)
df3 = pd.DataFrame(fees3)
'''
err_rate = (max(sucR_data[(Start_point+1):])-min(sucR_data[(Start_point+1):]))/2
avg_rate = sum(sucR_data[(Start_point+1):])/(End_point-Start_point)
err_fee = (max(fees[(Start_point+1):])-min(fees[(Start_point+1):]))/2
avg_fee = sum(fees[(Start_point+1):])/(End_point-Start_point)
print('R_ERR: %s\tAVG_R: %s'%(err_rate,avg_rate))
print('F_ERR: %s\tAVG_F: %s'%(err_fee,avg_fee))
avg_tps = sum(tps_data[(Start_point+1):])/(End_point-Start_point)
print('TPS: %s'%(avg_tps/100))
'''
rc('font',size = 18)
fig = plt.figure()
xlabel('Check points')
ylabel('Transaction throughput (TPS)')
y1,y10, = plot(df1[0],'lightgreen',df1[0].rolling(4).mean(),'g',linewidth = 2) 
y2,y20, = plot(df2[0],'lightblue',df2[0].rolling(4).mean(),'b',linewidth = 2)
y3,y30, = plot(df3[0],'pink',df3[0].rolling(4).mean(),'r',linewidth = 2)
legend([y20,y10,y30],['LPS','UPS','EDF'],loc = 'best',fontsize = 15)
#plt.plot(reward)
show()

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
