import numpy as np

from scipy.sparse import csr_matrix
import scipy as scipy
from scipy.spatial import cKDTree

import networkx as nx
import pytim.observables

def _zero_rows(M, rows):
    diag = scipy.sparse.eye(M.shape[0]).tolil()
    for r in rows:
        diag[r, r] = 0
    return diag.dot(M)

def _zero_columns(M, columns):
    diag = scipy.sparse.eye(M.shape[1]).tolil()
    for c in columns:
        diag[c, c] = 0
    return M.dot(diag)

def _reduce_graph(A, branches):
    reduction_list=[]
    for branch in branches[2:]: #excluding the branching points and monomers
        reduction_list.append(branch)
    reduction_flat = [item for sublist in reduction_list for item in sublist]
    reduction_flat = [item for sublist in reduction_flat for item in sublist]
    reduction = (set(reduction_flat) | set(branches[1])) - set(branches[0])

    A = _zero_rows(A, list(reduction))
    A = _zero_columns(A, list(reduction))
    
    return A, reduction

def _has_next(A,is_end,chain,next_index):
    neighbor = (A.getrow(next_index).toarray() ) == 1
    neighbor_array = np.where(neighbor)[1]

    if (len(neighbor_array)>2):
        return False, chain, is_end
    if (is_end[0,next_index]==True):
        is_end[0,next_index]= False
        return False, chain, is_end
    new_neighbor = list(set(neighbor_array)-set(chain))
    
    if new_neighbor:
        next_index= new_neighbor[0]
        chain.append(next_index)
        return next_index, chain, is_end
    
    return False, chain, is_end

def _merge_structures(parent, interior, k, start_idx):
    while len(parent) < len(interior):
        for i in range(k):
            parent.append([])

    for idx in range(start_idx, len(interior)):  #now add to interior_branches
        for chain in interior[idx]:
            parent[idx].append(chain)
    return parent

def determine_branches(A, k, reduction):
    """ determine all chains starting at chain ends
        * passing reduction necessary to correctly treat monomers"""
    branches = []
    
    b_point = A.sum(-1) > 2  # branching point condition
    b_point = b_point.A1
    branches.append(np.where(b_point)[0].tolist())

    mono = ( A.max(-1).toarray() ) == 0  # monomers condition
    mono = mono.reshape(len(mono),)
    for i in range(0, len(mono)):
        if i in reduction:
             mono[i]=False
    branches.append(np.where(mono)[0].tolist())
    
    
    # determine loose ends -> potential dimer
    loose_end = A.sum(-1)==1
    loose_end = loose_end.reshape(len(loose_end),)

    for i in range(1, k):
        branches.append([])
    chain = []

    for end in np.where(loose_end.A1)[0]:
        if (loose_end[0,end]==True):
            chain.append(end)            
            neighbor = (A.getrow(end).toarray()) == 1
            next = np.where(neighbor)[1][0]
            chain.append(next)
       
            while next:
                next, chain, loose_end = _has_next(A,loose_end,chain,next)

            while True:
                #allocated list might be to small 
                try:
                    branches[len(chain)].append(chain)
                    break
                except IndexError:
                    for i in range(k):
                        branches.append([])
                        
            chain = []

    return branches, reduction


class Branching(pytim.observables.Observable):
    """Determine all chains, inner branches and cycles using Scipy Sparse Matrix CSR
        * pytim observable"""
    
    def __init__(self,k,cut):
        self.k = k
        self.cut = cut
        self.linear = None
        self.cluster_chains = None
        self.cycles  = None

    def compute(self, group1, group2):
        cut = self.cut
        k = self.k

        box = group1.universe.dimensions[:3]
        positions1 = group1.atoms.pack_into_box()
        positions2 = group2.atoms.pack_into_box()
        tree1 = cKDTree(positions1,boxsize=box)
        tree2 = cKDTree(positions2,boxsize=box)
        dok=tree1.sparse_distance_matrix(tree2,cut)
        dok.setdiag(0.0)
        M = dok.tocsr()
        A = M.copy()
        A.data[A.data>0.0] =1.0
        A = A.astype(int)
        A = A + A.transpose() # matrix upper triangular


        # detect exterior structure
        chain_end_id = A.sum(-1)==1
        chain_end_id = chain_end_id.A1
        chain_end_id = np.where(chain_end_id)[0]

        reduction = set()
        branches, reduction = determine_branches(A, k, reduction)
    
        # detect interior structure
        aux_branches = []
        interior_branches= []
        if len(branches[0])>0:
            A , reduction_plus = _reduce_graph(A, branches)
            reduction = reduction | reduction_plus
            aux_branches, reduction = determine_branches(A, k, reduction)
            interior_branches = aux_branches[:]
 
            unblocked_b_points = 0 #chains might be "blocked" by rings
            while (len(aux_branches[0])> 0 and unblocked_b_points != len(aux_branches[0])):
                unblocked_b_points = len(aux_branches[0])
                A , reduction_plus = _reduce_graph(A, aux_branches)
                reduction = reduction | reduction_plus
                aux_branches, reduction = determine_branches(A, k, reduction)
                interior_branches = _merge_structures(interior_branches, aux_branches, k, 0)

        # detect cycles
        if (A.max()>0.0): 
            G = nx.Graph(A)
            self.cycles = nx.cycle_basis(G)
            for cyc in self.cycles[:]:
                cyc.sort()
            self.cycles.sort(key=len)


            #reduce by cycles (cannot use _reduce_graph())
            reduction_cycles_list = [item for sublist in self.cycles for item in sublist]
            reduction_cycles = set(reduction_cycles_list) - set(branches[0])
            A = _zero_rows(A, list(reduction_cycles))
            A = _zero_columns(A, list(reduction_cycles))
            reduction = reduction | reduction_cycles
    

            # detect "blocked" interior structure
            bonded_b_points = 0 #cycles of branching points
            while (len(aux_branches[0])> 0 and bonded_b_points != len(aux_branches[0])):
                bonded_b_points = len(aux_branches[0])
                aux_branches, reduction = determine_branches(A, k, reduction)
                interior_branches = _merge_structures(interior_branches, aux_branches, k, 0)
                
                A , reduction_plus = _reduce_graph(A, aux_branches)
                reduction = reduction | reduction_plus
        
        branches = _merge_structures(branches, interior_branches,k, 2)

        self.linear = branches[:]
        self.cluster_chains = branches[:]
        linear_chain_end_id = []

        for idx, n_chains in enumerate(branches):
            self.linear[idx] = []
            self.cluster_chains[idx] = []
            if idx<2:
                continue
            for chain in n_chains:
                
                if (chain[0] in chain_end_id and chain[-1] in chain_end_id):
                    self.linear[idx].append(chain)
                    linear_chain_end_id.append(chain[0])
                    linear_chain_end_id.append(chain[-1])
                else:
                    self.cluster_chains[idx].append(chain)


        cluster_chain_end_id = list(set(chain_end_id) - set(linear_chain_end_id))

        self.linear[0] = sorted(linear_chain_end_id)
        self.linear[1] = sorted(branches[1]) # monomers
        self.cluster_chains[0] = sorted(cluster_chain_end_id)
        self.cluster_chains[1] = sorted(branches[0]) #branching points
        
        return self.linear, self.cluster_chains, self.cycles
