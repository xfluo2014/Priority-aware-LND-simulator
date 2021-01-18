import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


#read graph info
G=nx.read_edgelist("graph.txt",nodetype=int)
print(len(G.edges))


#red_edges = [(0,1),(1,12),(12,5),(5,10),(10,17),(17,16),(16,7)]
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size = 500)
nx.draw_networkx_labels(G, pos)
red_nodes = [22,41]
#nx.draw_networkx_nodes(G, pos, nodelist=red_nodes,node_color='r',cmap=plt.get_cmap('jet'), node_size = 500)
#nx.draw_networkx_edges(G, pos, edgelist=red_edges, edge_color='r', arrows=True)
nx.draw_networkx_edges(G, pos)
plt.show()