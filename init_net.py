import networkx as nx
import random

Num_nodes = 50
Num_pairs = 20
Num_priority = 3

#generate graph of PCN
G= nx.watts_strogatz_graph(Num_nodes,3,1)
#print(list(G.edges))
#write_graph = open("graph.txt","w")
nx.write_edgelist(G,"graph.txt")
#write_graph.close()
#for hop in list(G.edges):
#    print(hop)

#initilized the occupied channel balance
b_uv = {}
w_uv = {}
d_uv = {}
for i in list(G.edges):
    b_uv[i] = 1000+100*random.randint(1,5)
    b_uv[tuple(reversed(i))] = 1000+100*random.randint(1,5)
    #mu = 0.008+0.001*random.randint(1,3)
    w_uv[i] = 0.01
    w_uv[tuple(reversed(i))] = 0.01
    #temp_delay = random.randrange(100,201,100)
    temp_delay = 30
    d_uv[i] = temp_delay
    d_uv[tuple(reversed(i))] = temp_delay

#write hop info
write_hopInfo = open("hopInfo.txt","w")
for i in list(G.edges):
    write_hopInfo.write("%s\t%s\t%s\t%s\n"%(i,b_uv[i],w_uv[i],d_uv[i]))
    j = tuple(reversed(i))
    write_hopInfo.write("%s\t%s\t%s\t%s\n"%(j,b_uv[j],w_uv[j],d_uv[j]))
write_hopInfo.close()

#pair of sender and receiver
Pairs = []
Pay_rate = {}
Pay_amount = {}
for i in range(Num_pairs):
    temp_sender = 0
    temp_receiver = 0
    exist_senders = [x[0] for x in Pairs]
    while temp_sender == temp_receiver or temp_sender in exist_senders:
        temp_sender = random.randint(1,Num_nodes)-1
        temp_receiver = random.randint(1,Num_nodes)-1
        temp_pair = [temp_sender,temp_receiver]
        if tuple(temp_pair) in G.edges or tuple(reversed(temp_pair)) in G.edges:
            temp_sender = temp_receiver
    Pairs.append((temp_sender,temp_receiver))
    #temp_rate = random.randint(10,20)
    Pay_rate[(temp_sender,temp_receiver)] = random.randint(3,9)
    Pay_amount[(temp_sender,temp_receiver)] = 1

print("Pairs: ",Pairs)

#generate payment path
write_path = open("path.txt","w")
maxNum_path = 3
for p in Pairs:
    count_path = 0
    temp_path_list = {}
    for path in map(nx.utils.pairwise, nx.all_shortest_paths(G,p[0],p[1])):
        temp_path_list[count_path] = [x for x in path]
        count_path += 1
        if count_path >= maxNum_path:
            break
    recard_path = []
    for tp in temp_path_list.values():
        if len(list(tp))>2:
            recard_path = [x for x in tp]
            print(recard_path)
            break
    if recard_path ==[]:
        recard_path  = [x for x in temp_path_list[0]]
    for h in recard_path:
        write_path.write('(%s,%s)\t'%(h[0],h[1]))
    write_path.write('\n')
write_path.close()

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

#user demand of payment time
D_ij = {}
for i in Pairs:
    D_ij[i] = len(Routes[i][0])-1 if len(Routes[i][0])>1 else 1

#write payment info in file
write_payInfo = open("payment_info.txt","w")
for i in Pairs:
    write_payInfo.write("%s\t%s\t%s\t%s\n"%(i,Pay_rate[i],Pay_amount[i],D_ij[i]))
write_payInfo.close()

Hop = list(G.edges)
for i in list(G.edges):
    Hop.append(tuple(reversed(i)))

hop_occp = {}
for i in Hop:
    count = 0
    for j in Pairs:
        if i in Routes[j][0]:
            count +=1
    hop_occp[i] = count

hop_  = list(filter(lambda a: a != 0, hop_occp.values()))
freq = sum(y >= 2 for y in hop_)
print(len(hop_))
print('share chan:', freq)