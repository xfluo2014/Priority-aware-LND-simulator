import networkx as nx
Num_nodes = 50
Num_pairs = 15
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

for x in Pairs:
    max_flow = 0
    for hop in Routes[x][0]:
        temp_flow = 0
        for y in Pairs:
            if hop in Routes[y][0]:
                temp_flow += Pay_rate[y]
        if temp_flow > max_flow:
            max_flow = temp_flow
    print('Tx:%s\tMax flow:%s'%(x,max_flow))

                