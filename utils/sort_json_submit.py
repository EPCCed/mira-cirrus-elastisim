import json
import sys

infile = sys.argv[1]

f = open(infile)
jobs_d = json.load(f)
print(len(jobs_d['jobs']))

jobs_a = jobs_d['jobs']

jobs_sorted_a = sorted(jobs_a, key=lambda d: d['submit_time'])

print(len(jobs_sorted_a))

jobs_d = {}
jobs_d['jobs'] = jobs_sorted_a

with open(sys.argv[2], 'w') as fp:
    json.dump(jobs_d, fp, indent=4)


