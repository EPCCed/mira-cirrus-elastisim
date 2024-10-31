import json
import csv
import sys
import argparse
import numpy as np
import pandas as pd
import random

# Parse command line arguments
parser = argparse.ArgumentParser(description='Compute software usage data from Slurm output.')
parser.add_argument('filename', type=str, nargs=1, help='Data file containing listing of Slurm jobs')
parser.add_argument('-t', dest='jobtype', type=str, action='store', default='rigid', help='The type of jobs to produce. Can be "rigid" or "moldable". Default: rigid')
parser.add_argument('-l', dest='timeLimit', type=float, action='store', default=None, help='Maximum number of seconds since period start to consider job start times from. Default: infinite, include all jobs')
parser.add_argument('-n', dest='totUse', type=float, action='store', default=1.0e10, help='Total usage to produce jobs for in coreh. Default: infinite, include all jobs')
parser.add_argument('-r', dest='minRuntime', type=float, action='store', default=0, help='Minimum runtime for jobs to consider for selection. Default: 1, include all jobs')
parser.add_argument('-c', dest='csvfile', type=str, action='store', default='raw_job_statistics.csv', help='CSV output file name. Default: raw_job_statistics.csv')
parser.add_argument('-o', dest='jsonfile', type=str, action='store', default='elastisim_joblist.json', help='JSON output file name. Default: elastisim_joblist.json')
parser.add_argument('-s', dest='scalefactor', type=int, action='store', default=1, help='The factor to divide the job time (in seconds) by. Default: 1')
args = parser.parse_args()

csvfile = open(args.filename[0], 'r')
csvwriter  = open(args.csvfile, 'w')
csvwriter.write('ID,Type,Submit Time,Start Time,End Time,Wait Time,Makespan,Turnaround Time,Status,Nodes\n')

csvreader = csv.reader(csvfile)
njob = 0
submitzero = 0
jobs_l = []
tmax = 0.0
runmax = 0
sizemax = 0
endmax = 0 
endmax_kept = 0 
# Skip the header line
next(csvreader, None)
for row in csvreader:
    if njob == 0:
        submitzero = int(row[3])
    jobid = row[0]
    cores = int(int(row[1])/2)
    if cores < 1: continue
    tsubmit = int(row[3]) - submitzero
    tsubmit = int(tsubmit/args.scalefactor)
    if tsubmit > tmax: tmax = tsubmit
    runtime = int(int(row[7])/args.scalefactor)
    tstart = int(row[5]) - submitzero
    tstart = int(tstart/args.scalefactor)
    tend = tstart + runtime
    if tend > endmax: endmax = tend

    if runtime < args.minRuntime: continue
    if tsubmit > args.timeLimit: continue

    if tend > endmax_kept: endmax_kept = tend
    twait = tstart - tsubmit
    turnaround = tend - tsubmit
    iterations = runtime
    if iterations < 1: iterations = 1
    if iterations > runmax: runmax = iterations 

    job_d = {}
    job_d['ID'] = f'{row[0]}_ar2'
    job_d['Type'] = args.jobtype
    job_d['Submit Time'] = tsubmit
    job_d['Start Time'] = tstart
    job_d['End Time'] = tend
    job_d['Wait Time'] = twait
    job_d['Makespan'] = iterations
    job_d['Turnaround Time'] = turnaround
    job_d['Nodes'] = 144 # Hardwired as these are all 128 core jobs (144 equivalent on Cirrus)

    jobs_l.append(job_d)

    njob = njob + 1


# Sampling the brute force way
tot_coreh = 0.0
selected_jobs_l = []
while (tot_coreh <= args.totUse) and (len(jobs_l) > 0):
    random_element = random.choice(jobs_l)
    jobs_l.remove(random_element)
    coreh = (random_element['Nodes'] * random_element['Makespan']) / 3600.0
    tot_coreh = tot_coreh + coreh
    selected_jobs_l.append(random_element)

print(f' total Coreh in selected jobs = {tot_coreh}')
print(f' Number of selected jobs = {len(selected_jobs_l)}')

jobs_json = []
for job in selected_jobs_l:
    job_d = {}
    job_d['type'] = job['Type']
    job_d['submit_time'] = job['Submit Time']
    if job['Type'] == 'rigid':
        job_d['num_nodes'] = job['Nodes']
    else:
        job_d['num_nodes_min'] = int(job['Nodes'] / 2)
        job_d['num_nodes_max'] = int(job['Nodes'] * 2)
    job_d['application_model'] = '/data/input/busywait_model.json'
    args_d = {}
    args_d['nstep'] = job['Makespan']
    args_d['base_nodes'] = job['Nodes']
    args_d['jobid'] = job['ID']
    job_d['arguments'] = args_d
    jobs_json.append(job_d)

jobs_d = {}
jobs_d['jobs'] = jobs_json
jsonout = open(args.jsonfile, 'w')
json.dump(jobs_d, jsonout, indent=3)



