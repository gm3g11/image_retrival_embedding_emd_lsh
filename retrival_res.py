import os
import numpy as np
import pickle
retrival_file=open("retrival.pkl", "rb")
output = pickle.load(retrival_file)
print(output)
retrival_file.close()