import json
import sys

infile = sys.argv[1]

f = open(infile)
jobs_d = json.load(f)

index_jobs_d = {}
for job in jobs_d['jobs']:
    st = job['submit_time']
    index_jobs_d[st] = job

index_jobs_d = dict(sorted(index_jobs_d.items()))

jobs_d = {}
jobs_a = []
for i, job in index_jobs_d.items():
    jobs_a.append(job)

jobs_d['jobs'] = jobs_a

with open(sys.argv[2], 'w') as fp:
    json.dump(jobs_d, fp, indent=4)


