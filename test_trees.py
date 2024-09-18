import Merkle_trees as mt
import random
import time


data_blocks = [random.randint(0, 1000) for _ in range(2**16)]


bmt = mt.BinaryMerkleTree(data_blocks)
smt = mt.SparseMerkleTree(key_len = 16)
imt = mt.IndexedMerkleTree(tree_height = 16)


start1 = time.time()
bmt.find_hashes()
end1 = time.time()

smt.initial_tree()
imt.initial_tree()


start2 = time.time()
for index, value in enumerate(data_blocks):
    smt.add_value(index, value)
end2 = time.time()    



start3 = time.time()
for index, value in enumerate(data_blocks[:len(data_blocks) - 1]):
    imt.add_value(value) 
    imt.update()
end3 = time.time()

print('Programm is finished!')

print(f'Add element to binary tree and update state: {end1 - start1}')

print(f'Add element to sparse tree and update state: {end2 - start2}')

print(f'Add element to indexed tree and update state: {end3 - start3}')