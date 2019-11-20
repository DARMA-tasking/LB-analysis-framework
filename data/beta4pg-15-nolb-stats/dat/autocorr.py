import numpy as np
import math

file_name = "o-17179869184.dat"

times = []
with open(file_name, 'r') as f:
    for r in f:
        times.append(float(r.split(' ')[2].strip()))

w_sz = 100

prev_slice = None
for i in range(len(times) - w_sz + 1):
    curr_slice = times[i:i+w_sz]
    if prev_slice:
        C = np.cov(prev_slice, curr_slice, bias=True)
        pr = C[0][1] / math.sqrt(C[0][0] * C[1][1])
        print i, pr
    prev_slice = curr_slice
