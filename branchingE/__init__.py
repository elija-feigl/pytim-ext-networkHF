import numpy as np

from network import Branching

def _reduce_to_group(sample,g):
    for idx, line in enumerate(sample[:2]):
        for id in line[:]:
            if id not in g:
                line.remove(id)
        sample[idx] = line
    for idx, line in enumerate(sample[2:]):
        for chain in line[:]:
            if not g.intersection(chain):
                line.remove(chain)
        sample[idx+2] = line
    return sample

class BranchingStatistics(object):
    """ histograms of linear chains, branches, cycles
        
        input:
        g1, g2 : two atom groups
        cut : distance that is criterion for connection between atoms of group g1 and g2
        k: guess for maximum chain length in the system"""
    
    def __init__(self,universe,g1,g2,cut,k=50):
        self.counts = 0  
        self.universe = universe
        self.g1 = g1
        self.g2 = g2
        self.k = k
        self.cut = cut
        self.Branching = Branching(k,cut)
    
        self.linear = np.zeros(self.k)
        self.cluster_chains = np.zeros(self.k)
        self.cycles  = np.zeros(self.k)

    def sample(self,group=None):
        
        linear_sample, cluster_chains_sample, cycles_sample =  self.Branching.compute(self.g1,self.g2)
        
        __max_struct = max(len(linear_sample),(len(cycles_sample[-1])+1))
        if __max_struct > len(self.linear):
            __linear = self.linear
            __cluster_chains = self.cluster_chains
            __cycles = self.cycles
            __indx = np.arange(len(self.linear),dtype = int)
            
            self.linear = np.zeros(__max_struct)
            self.cluster_chains = np.zeros(__max_struct)
            self.cycles  = np.zeros(__max_struct)
            
            self.linear[__indx] = __linear
            self.cluster_chains[__indx] = __cluster_chains
            self.cycles[__indx] = __cycles
        

        
        
        #keep only indices that belong to the group if provided
        if group:
            group_set= set(group.residues.resids-1)

            linear_sample = _reduce_to_group(linear_sample,group_set)
            cluster_chains_sample = _reduce_to_group(cluster_chains_sample,group_set)
            
            for cyc in cycles_sample[:]:
                if not group_set.intersection(cyc):
                    cycles_sample.remove(cyc)
    
    
        #real linear chain:
        linear_plus = np.zeros(len(self.linear))
        linear_plus[1]= len(linear_sample[1])

        for idx in range(2,len(linear_sample)):
            linear_plus[idx] = len(linear_sample[idx])
        self.linear += linear_plus
        
        #branch length:
        cluster_chains_plus = np.zeros(len(self.cluster_chains))
        for idx in range(2,len(cluster_chains_sample)):
            cluster_chains_plus[idx] = len(cluster_chains_sample[idx])
        self.cluster_chains += cluster_chains_plus

        #cycle length:
        for cycle in cycles_sample:
            self.cycles[len(cycle)] += 1
            
        self.counts +=1

        return linear_sample, cluster_chains_sample, cycles_sample
            
        
    def get_values(self):
        
    #normalization
        self.linear /= float(self.counts) 
        self.cluster_chains /= float(self.counts)
        self.cycles  /= float(self.counts)
    
        return self.linear, self.cluster_chains, self.cycles

