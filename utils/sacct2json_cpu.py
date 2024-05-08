import json
import csv
import sys

njob_limit = False
MAX_JOB = 100

if len(sys.argv) > 3:
    njob_limit = True
    MAX_JOB = int(sys.argv[3])

csvfile = open(sys.argv[1], 'r')

csvreader = csv.reader(csvfile)
njob = 0
submitzero = 0
jobs_l = []
# Skip the header line
next(csvreader, None)
for row in csvreader:
    if njob == 0:
        submitzero = int(row[3])
    cores = int(row[1])
    if cores < 1:
        continue
    tsubmit = int(row[3]) - submitzero
    tsubmit = int(tsubmit/60)
    runtime = int(row[6])
    iterations = int(runtime/60)
    if iterations < 1:
        continue
    job_d = {}
    job_d['type'] = 'rigid'
    job_d['submit_time'] = tsubmit
    job_d['num_nodes'] = cores
    job_d['application_model'] = 'cirrus-cpu-simple/data/input/busywait_model.json'
    args_d = {}
    args_d['iterations'] = iterations
    args_d['base_nodes'] = cores
    job_d['arguments'] = args_d
    jobs_l.append(job_d)
    njob += 1
    if njob_limit and njob >= MAX_JOB:
        break

jobs_d = {}
jobs_d['jobs'] = jobs_l
jsonfile = open(sys.argv[2], 'w')
json.dump(jobs_d, jsonfile, indent=3)


