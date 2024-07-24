import csv
import sys

csvfile = open(sys.argv[1], 'r')

csvreader = csv.reader(csvfile)
# Skip the header line
next(csvreader, None)
nodestate_l = []
for row in csvreader:
    nodestate_l.append(row)



maxtime = int(nodestate_l[-1][0]) + 1
print(maxtime)

nodeuse_l = [0 for i in range(maxtime)]

for row in nodestate_l:
    timestep = int(row[0])
    if row[2] == 'allocated':
        nodeuse_l[timestep] += 1

for i, x in enumerate(nodeuse_l):
    if i > 0:
        if x == 0:
            nodeuse_l[i] = nodeuse_l[i-1]

for row in nodestate_l:
    timestep = int(row[0])
    if timestep > 0 and row[2] == 'free':
        nodeuse_l[timestep] -= 1
    if nodeuse_l[timestep] < 0:
        nodeuse_l[timestep] = 0

print(nodeuse_l)



    