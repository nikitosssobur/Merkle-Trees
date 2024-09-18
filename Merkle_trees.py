import hashlib
import random
import sys


class BinaryMerkleTree:
    '''
    Binary MerkleTree implementation
    '''
    def __init__(self, data_blocks):
        self.__hash_func = hashlib.sha256
        self.data_blocks = data_blocks
        self.blocks_hashes = [] 
        self.merkle_root = None
    

    def get_merkle_root(self):
        return self.merkle_root
    

    def hash(self, obj):
        '''
        obj variable can get as input int or str or byte-string or None
        '''
        if obj is None:
            bytes_obj = ''.encode('utf-8')
        else:
            bytes_obj = str(obj).encode('utf-8')
        return self.__hash_func(bytes_obj).hexdigest()


    def set_hash_func(self, hash_func):
        self.__hash_func = hash_func


    def pair_hash(self, pair):
        return self.hash(''.join(pair))


    def get_level_hashes(self, data_hashes):
        data_hashes = [data_hashes[i : i + 2] for i in range(0, len(data_hashes), 2)]
        return [self.pair_hash(pair) for pair in data_hashes]


    def find_hashes(self):
        data_hashes = [self.hash(data) for data in self.data_blocks]
        if len(data_hashes) % 2 == 1:
            data_hashes += [data_hashes[-1]]    
        self.blocks_hashes.append(data_hashes)
        while len(data_hashes) != 1:
            if len(data_hashes) % 2 == 1:
                data_hashes += [data_hashes[-1]]
            #data_hashes = [data_hashes[i : i + 2] for i in range(0, len(data_hashes), 2)]
            #data_hashes = [self.pair_hash(pair) for pair in data_hashes]  # data_hashes = len(data_hashes) / 2
            data_hashes = self.get_level_hashes(data_hashes)
            self.blocks_hashes.append(data_hashes)
        
        self.merkle_root = self.blocks_hashes[-1][0]
        

    def bin_tree_hashes_list(self):
        '''
        Function create hash values of the all nodes of the tree in the format of 1-d list.
        List contains hashes in the order from root node to the leaves, from left to right.  
        hashes_list[0] - hash of the root node
        hashes_list[1] - hash of the left child node
        hashes_list[2] - hash of the right child node 
                            ...
        hashes_list[i//2] - hash of the i-th parent node
        hashes_list[2i] - hash of the left child of the i-th parent node
        hashes_list[2i + 1] - hash of the right child of the i-th parent node
        '''
        hashes_list = []
        for block in self.blocks_hashes[::-1]:
            hashes_list += block
        
        self.hashes_list = hashes_list


    def add_block(self, block):
        self.data_blocks.append(block)


    def update_tree(self):
        self.blocks_hashes.clear()
        self.find_hashes()
        self.bin_tree_hashes_list()

    
    def update_tree_optim(self):
        new_blocks_num = len(self.data_blocks) - len(self.blocks_hashes[0])
        new_data_blocks = self.data_blocks[len(self.data_blocks) - new_blocks_num:]
        for i in range(len(self.blocks_hashes)):
            if i == 0:
                new_blocks_hashes = [self.hash(block) for block in new_data_blocks]
            else:
                new_blocks_hashes = self.get_level_hashes(new_blocks_hashes)
            self.blocks_hashes[i] += new_blocks_hashes
        
        self.blocks_hashes.append([self.pair_hash(self.blocks_hashes[-1])])
        self.merkle_root = self.blocks_hashes[-1][0]


    def get_blocks_hashes(self):
        return self.blocks_hashes


    def get_hashes_list(self):
        return self.hashes_list


    def tree_height(self):
        self.height = len(self.blocks_hashes)


    def generate_proof(self, arg):
        if isinstance(arg, (int, float)):
            arg_hash = self.hash(arg)
        elif isinstance(arg, str):
            arg_hash = arg
        
        proof = []
        if arg_hash not in self.blocks_hashes[0]:
            #exclusion proof 
            raise ValueError("Data block is not in the Merkle Tree")
        
        index = self.blocks_hashes[0].index(arg_hash)  
        for level in self.blocks_hashes:  
            if index % 2 == 1:
                sibling_hash_index = index - 1
                is_left = False
            else:
                sibling_hash_index = index + 1
                is_left = True
            
            if sibling_hash_index < len(level):
                sibling_hash = level[sibling_hash_index]
                proof.append((sibling_hash, is_left))
            
            index = index // 2

        return proof



class SparseMerkleTree:
    #Sparse Merkle Tree implementation
    
    def __init__(self, key_len = None, default_leaf_value = ''):
        self.key_len = key_len if isinstance(key_len, int) and key_len > 1 else 3
        self.__hash_func = hashlib.sha256
        self.default_leaf_value = default_leaf_value
        #self.data_blocks = ['' for _ in range(2 ** self.key_len)]  
        self.blocks_hashes = []
        self.default_hash_values = self.get_default_hash_values()
        self.merkle_root = self.default_hash_values[-1]
        self.values = [None] * (2 ** self.key_len)
    

    def hash(self, obj):
        if obj is None:
            bytes_obj = ''.encode('utf-8')
        else:
            bytes_obj = str(obj).encode('utf-8')
        return self.__hash_func(bytes_obj).hexdigest()


    def get_default_hash_values(self):
        default_hash_values = []
        for i in range(self.key_len + 1):
            if i == 0:
                def_value = self.hash(self.default_leaf_value)
            else:
                def_value = self.hash(default_hash_values[i - 1] * 2) 
            default_hash_values.append(def_value)
        return default_hash_values
        
            
    def initial_tree(self):
        level_nodes_num = 2 ** self.key_len
        for i in range(self.key_len + 1):
            self.blocks_hashes.append([self.default_hash_values[i]] * level_nodes_num)
            level_nodes_num //= 2
    
    
    def add_value(self, index, value):
        if isinstance(index, int) and 0 <= index <= (2 ** self.key_len) - 1:
            self.values[index] = value
            self.update(index, value)
            

    def update(self, index, value):
        for i in range(self.key_len + 1):
            if i == 0:
                hash_value = self.hash(value)
                self.blocks_hashes[i][index] = hash_value 
                parent_node_index = index // 2
                sibling_node_index = index + 1 if index % 2 == 0 else index - 1
            else:
                if sibling_node_index % 2 == 0:
                    arg = self.blocks_hashes[i - 1][sibling_node_index] + hash_value
                else:
                    arg = hash_value + self.blocks_hashes[i - 1][sibling_node_index]
                hash_value = self.hash(arg)
                self.blocks_hashes[i][parent_node_index] = hash_value
                if i <= self.key_len - 1:
                    sibling_node_index = parent_node_index + 1 if parent_node_index % 2 == 0 else parent_node_index - 1
                    parent_node_index = parent_node_index // 2
        self.merkle_root = self.blocks_hashes[-1][0]

    
    def generate_proof(self, arg):
        if isinstance(arg, (int, float)):
            arg_hash = self.hash(arg)
        elif isinstance(arg, str):
            arg_hash = arg
        
        proof = []
        if arg_hash not in self.blocks_hashes[0]:
            raise ValueError("Data block is not in the Merkle Tree")
        
        index = self.blocks_hashes[0].index(arg_hash)  
        for level in self.blocks_hashes:  
            if index % 2 == 1:
                sibling_hash_index = index - 1
                is_left = False
            else:
                sibling_hash_index = index + 1
                is_left = True
            
            if sibling_hash_index < len(level):
                sibling_hash = level[sibling_hash_index]
                proof.append((sibling_hash, is_left))
            
            index = index // 2

        return proof



class Leaf:
    def __init__(self, value, nextidx, nextval):
        self.value = value
        self.nextidx = nextidx
        self.nextval = nextval

    def get_concat_data(self):
        return f"{self.value}{self.nextidx}{self.nextval}" #str(self.value) + str(self.nextidx) + str(self.nextval)
    


class IndexedMerkleTree:
    def __init__(self, tree_height: int):
        if tree_height > 0 and isinstance(tree_height, int):
            self.tree_height = tree_height
        else:
            self.tree_height = 3
        
        self.leafs_num = 2 ** self.tree_height
        self.leafs = self.initial_leafs()
        self.__hash_func = hashlib.sha256 
        self.blocks_hashes = []
        self.values = [self.leafs[0].value]
        self.add_value_index = 1
        self.max_val_indx = 0


    def hash(self, obj):
        if obj is None:
            bytes_obj = ''.encode('utf-8')
        else:
            obj = obj if isinstance(obj, str) else str(obj)
            bytes_obj = obj.encode('utf-8')
        return self.__hash_func(bytes_obj).hexdigest()
    

    def initial_leafs(self):
        return [Leaf(0, 0, 0) for _ in range(self.leafs_num)]


    def initial_tree(self):
        for i in range(self.tree_height + 1):
            if i == 0:
                hashes = [self.hash(leaf.get_concat_data()) for leaf in self.leafs]
            else:
                prev_hashes = [self.blocks_hashes[i - 1][j : j + 2] for j in range(0, len(self.blocks_hashes[i - 1]), 2)]
                hashes = [self.hash(pair[0] + pair[1]) for pair in prev_hashes] 
            self.blocks_hashes.append(hashes)


    def max_smaller_val(self, value):
        smaller_vals = []
        for val in self.values:
            if val <= value:
                smaller_vals.append(val)
        return max(smaller_vals)


    def add_value(self, value):
        if len(self.values) < self.leafs_num:
            #smaller_vals = []
            #for val in self.values:
                #if val <= value:
                    #smaller_vals.append(val)
           #max_smaller_val = max(smaller_vals)
            max_smaller_val = self.max_smaller_val(value)
            max_smaller_leaf_idx = self.values.index(max_smaller_val)
            max_smaller_leaf = self.leafs[max_smaller_leaf_idx]

            if value > self.values[self.max_val_indx]:
                nextidx, nextval = 0, 0
                self.max_val_indx = len(self.values)
            else:
                nextidx, nextval = max_smaller_leaf.nextidx, max_smaller_leaf.nextval
                #max_smaller_leaf.nextidx = len(self.values) + 1 
                #max_smaller_leaf.nextval = value 
                #self.leafs[max_smaller_leaf_idx] = max_smaller_leaf
            self.leafs[max_smaller_leaf_idx].nextidx = len(self.values)           
            self.leafs[max_smaller_leaf_idx].nextval = value 

            leaf = Leaf(value, nextidx, nextval)
            self.values.append(value)
            self.leafs[self.add_value_index] = leaf
            self.add_value_index += 1

        
        else:
            raise IndexError('All the leaves on the tree are filled!') 


    def update(self):
        for i in range(self.tree_height + 1):
            if i == 0:
                hashes = [self.hash(leaf.get_concat_data()) for leaf in self.leafs]
            else:
                prev_hashes = [self.blocks_hashes[i - 1][j : j + 2] for j in range(0, len(self.blocks_hashes[i - 1]), 2)]
                hashes = [self.hash(pair[0] + pair[1]) for pair in prev_hashes]
            self.blocks_hashes[i] = hashes  


    def generate_proof(self, arg):
        if isinstance(arg, (int, float)):
            arg_hash = self.hash(arg)
        elif isinstance(arg, str):
            arg_hash = arg
        
        proof = []
        if arg_hash not in self.blocks_hashes[0]:
            raise ValueError("Data block is not in the Merkle Tree")
        
        index = self.blocks_hashes[0].index(arg_hash)  
        for level in self.blocks_hashes:  
            if index % 2 == 1:
                sibling_hash_index = index - 1
                is_left = False
            else:
                sibling_hash_index = index + 1
                is_left = True
            
            if sibling_hash_index < len(level):
                sibling_hash = level[sibling_hash_index]
                proof.append((sibling_hash, is_left))
            
            index = index // 2

        return proof
    
    '''     
    def update(self):
        max_sm_val_idx = self.values.index(self.max_smaller_val(self.leafs[index].value))
        max_sm_leaf = self.leafs[max_sm_val_idx]
        index, hash_value = len(self.values) - 1, self.hash(self.leafs[index].get_concat_data()) 
        hash_value2 = self.hash(max_sm_leaf.get_concat_data())
        for i in range(self.tree_height + 1):
            if i == 0:
                self.blocks_hashes[i][index] = hash_value 
                self.blocks_hashes[i][max_sm_val_idx] = hash_value2
                parent_node_index = index // 2
                max_sm_parent_idx = max_sm_val_idx // 2
                sibling_node_index = index + 1 if index % 2 == 0 else index - 1
                max_sm_sibling_idx = max_sm_val_idx + 1 if max_sm_val_idx % 2 == 0 else max_sm_val_idx - 1
                calc_subtree = max_sm_val_idx != sibling_node_index 

            else:
                if sibling_node_index % 2 == 0:
                    arg = self.blocks_hashes[i - 1][sibling_node_index] + hash_value
                else:
                    arg = hash_value + self.blocks_hashes[i - 1][sibling_node_index]
                hash_value = self.hash(arg)
                self.blocks_hashes[i][parent_node_index] = hash_value
                
                if i != self.tree_height:
                    sibling_node_index = parent_node_index + 1 if parent_node_index % 2 == 0 else parent_node_index - 1
                    parent_node_index = parent_node_index // 2
                    
                hash_value2 = self.hash(hash_value2 + self.blocks_hashes[i - 1][max_sm_sibling_idx])
                self.blocks_hashes[i][max_sm_parent_idx] = hash_value2

        
        self.merkle_root = self.blocks_hashes[-1][0]
    '''

    
'''
class IndexedMerkleTree(BinaryMerkleTree):
    def __init__(self, data_blocks):
        super().__init__(data_blocks)
        self.hashes_list = None


    def __getitem__(self, indx):
        if self.hashes_list is None:
            raise ValueError("You need to find hash values for getting node of the tree!")
        else:
            if isinstance(indx, int) and 0 <= indx <= len(self.hashes_list) - 1:
                return self.hashes_list[indx]
            else:
                raise IndexError("Index must be a non-negative integer less then number of nodes in the tree!")
            
    
    def insert_block(self, block, indx):
        self.data_blocks[indx] = block
'''

'''
data = [random.randint(0, 255) for _ in range(64)]
print(data)
bin_merkle_tree = BinaryMerkleTree(data)
bin_merkle_tree.find_hashes()
blocks_hashes = bin_merkle_tree.get_blocks_hashes()
print(sum([len(blocks) for blocks in blocks_hashes]))
print(blocks_hashes)
print(blocks_hashes[-1], len(blocks_hashes[-1]), len(blocks_hashes))
print(bin_merkle_tree.hash(blocks_hashes[-2][0] + blocks_hashes[-2][1]))
print(int(blocks_hashes[-1][0], 10))
print(sys.getsizeof(bin_merkle_tree))
'''

def verify_inc_proof(proof, root_hash, target_data, hash_func = hashlib.sha256):
    '''
    Verifies the Merkle proof.
    proof: list of tuples from generate_proof method
    root_hash: known root hash of the Merkle tree
    target_data: the original data that needs to be verified
    hash_func: hash function to use (default: sha256)
    '''
    target_hash = hash_func(str(target_data).encode('utf-8')).hexdigest()
    for sibling_hash, is_left in proof:
        if is_left:
            target_hash = hash_func((target_hash + sibling_hash).encode('utf-8')).hexdigest()
        else:
            target_hash = hash_func((sibling_hash + target_hash).encode('utf-8')).hexdigest()

    return target_hash == root_hash



'''
smt = SparseMerkleTree(key_len = 3)
def_hash_values = smt.get_default_hash_values()
smt.initial_tree()
print(smt.blocks_hashes)
print(def_hash_values)  
print([len(hashes) for hashes in smt.blocks_hashes])
print(smt.merkle_root)
smt.add_value(2, 20)
print(smt.blocks_hashes)
print(smt.merkle_root)
'''

'''
imt = IndexedMerkleTree(3)
imt.initial_tree()
imt.add_value(10)
imt.add_value(20)
imt.add_value(50)
imt.add_value(5)
imt.add_value(35)
imt.add_value(60)
imt.add_value(90)
'''
print('Programm is finished!')


