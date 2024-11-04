import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
import csv
import json
import pandas as pd
import math
import statistics
import argparse

# Constants - currently for Cirrus CPU
nCoreTot = 13248 # Total cores available
timeLower = 5000 # Start time of analysis window
timeUpper= 23000 # End time of analysis window

# Parse command line arguments
parser = argparse.ArgumentParser(description='Analyse results of Elastisim scheduler simulation.')
parser.add_argument('-p', dest='prefix', type=str, action='store', default='elastisim', help='Prefix to use for output files. Default: "elastisim"')
parser.add_argument('-d', dest='datadir', type=str, action='store', default=".", help='Directory containing output files from Elastisim simulation. Output files must be called "node_utilization.csv" and "job_statistics.csv". Default: current directory.')
parser.add_argument('-i', dest='inputjson', type=str, action='store', default=None, required=True, help='Elastisim input JSON job list file. No default.')
parser.add_argument('-n', dest='name', type=str, action='store', default='elastisim', help='Name/label to use for statistics set. Default: "elastisim"')
args = parser.parse_args()

# Setup the file names
jsonInputName = args.inputjson
csvJobStatsName = f'{args.datadir}/job_statistics.csv'
csvNodeUtilizationName = f'{args.datadir}/node_utilization.csv'

usagePlotFile = f'{args.prefix}_simulated_load.png'
usagePlotFilePeriod = f'{args.prefix}_simulated_load_period.png'
statsJSON = f'{args.prefix}_simulation_stats.json'

csvfile = open(csvJobStatsName, 'r')

csvreader = csv.DictReader(csvfile)
jobList = []
for row in csvreader:
    jobList.append(row)

print(jobList[0])
print(jobList[-1])

jsonfile = open(jsonInputName, 'r')
jobDict = json.load(jsonfile)
i = 0
maxtime = 0
totuse = 0
jobidList = []
for job in jobDict['jobs']:
    jobidList.append(job['arguments']['jobid'])
    jobList[i]['JobID'] = job['arguments']['jobid']
    jobList[i]['BaseNodes'] = int(job['arguments']['base_nodes'])
    if job['type'] == 'moldable':
        jobList[i]['MinNodes'] = int(job['num_nodes_min'])
        jobList[i]['MaxNodes'] = int(job['num_nodes_max'])
    else:
        jobList[i]['MinNodes'] = int(job['num_nodes'])
        jobList[i]['MaxNodes'] = int(job['num_nodes'])
    i += 1

nodedata_df = pd.read_csv(csvNodeUtilizationName)
nodedata_df['Count'] = 1
nodedata_df.tail()

nodecount_grouped = nodedata_df.loc[nodedata_df['State'] == 'allocated'].groupby(by='Running jobs', sort=False)['Running jobs'].count()

for i, job in enumerate(jobList):
    cores = nodecount_grouped.iloc[i]
    jobList[i]['Nodes'] = cores
    totuse = totuse + float(jobList[i]['Makespan']) * jobList[i]['Nodes']
    if float(jobList[i]['End Time']) > maxtime:
        maxtime = math.ceil(float(jobList[i]['End Time']))

job_df = pd.DataFrame(jobList)
job_df['Start Time'] = job_df['Start Time'].astype(float)
job_df['Wait Time'] = job_df['Wait Time'].astype(float)
job_df['End Time'] = job_df['End Time'].astype(float)
job_df['Nodes'] = job_df['Nodes'].astype(int)
job_df['Makespan'] = job_df['Makespan'].astype(float)
job_df['Coreh'] = job_df['Makespan'] * job_df['Nodes'] / 3600.0
job_df['Turnaround Time'] = job_df['Turnaround Time'].astype(float)
job_df['Efficiency'] = job_df['Makespan'] / job_df['Turnaround Time']
print(job_df)

print(job_df['Coreh'].sum())

nrigid = len(job_df.loc[job_df['Nodes'] == job_df['BaseNodes']])
nmoldable = len(job_df.loc[job_df['Nodes'] != job_df['BaseNodes']])
nlarger = len(job_df.loc[job_df['Nodes'] > job_df['BaseNodes']])
nsmaller = len(job_df.loc[job_df['Nodes'] < job_df['BaseNodes']])
ntot = len(job_df)

print(f'Number of jobs at original size = {nrigid}/{ntot} ({100*nrigid/ntot:.2f}%)')
print(f'Number of jobs molded = {nmoldable}/{ntot} ({100*nmoldable/ntot:.2f}%)')
print(f'Number of jobs larger = {nlarger}/{ntot} ({100*nlarger/ntot:.2f}%)')
print(f'Number of jobs smaller = {nsmaller}/{ntot} ({100*nsmaller/ntot:.2f}%)')

load_a = np.zeros(maxtime+1, dtype=int)
load_cirrus_a = np.zeros(maxtime+1, dtype=int)
load_archer2_a = np.zeros(maxtime+1, dtype=int)
for job in jobList:
    temp_a = np.zeros(maxtime+1, dtype=int)
    istart = math.floor(float(job['Start Time']))
    iend = math.ceil(float(job['End Time']))
    nodes = int(job['Nodes'])
    temp_a[istart:iend] = nodes
    load_a = load_a + temp_a
    if "ar2" in job['JobID']:
        load_archer2_a = load_archer2_a + temp_a
    else:
        load_cirrus_a = load_cirrus_a + temp_a

# With the moldable jobs, start and end times can be fractional
# This means that when they are floor'd and ceil'd you can end
# up with times where the load exceeds the number of cores available.
# Rather than doing something intelligent, we clip the array so it is
# in the correct range
load_a = np.clip(load_a, a_min=0, a_max=nCoreTot)
load_archer2_a = np.clip(load_archer2_a, a_min=0, a_max=nCoreTot)
load_cirrus_a = np.clip(load_cirrus_a, a_min=0, a_max=nCoreTot)

plt.figure(figsize=(15, 5))
plt.plot(load_a, label='Overall')
plt.plot(load_cirrus_a, label='Cirrus')
plt.plot(load_archer2_a, label='ARCHER2')
plt.xlabel("Time")
plt.ylabel("Cores in use")
plt.legend()
sns.despine()
plt.savefig(usagePlotFile, dpi=300, bbox_inches='tight')

# Reduced analysis period
plt.figure(figsize=(15, 5))
plt.plot(load_a, label='Overall')
plt.plot(load_cirrus_a, label='Cirrus')
plt.plot(load_archer2_a, label='ARCHER2')
plt.xlabel("Time")
plt.ylabel("Cores in use")
plt.xlim([timeLower, timeUpper])
plt.legend()
sns.despine()
plt.savefig(usagePlotFilePeriod, dpi=300, bbox_inches='tight')

maxUsage = (timeUpper - timeLower) * nCoreTot

# Descriptive statistics
stats = {}

stats['nJobStart'] = sum((job_df['Start Time'] >= timeLower) & (job_df['Start Time'] <= timeUpper))

print(f"\n\nJob data:")
print(f"    nJobs = {stats['nJobStart']}")

stats['minLoad'] = min(load_a[timeLower:timeUpper+1])
stats['maxLoad'] = max(load_a[timeLower:timeUpper+1])
stats['medianLoad'] = statistics.median(load_a[timeLower:timeUpper+1])
stats['meanLoad'] = statistics.mean(load_a[timeLower:timeUpper+1])

usageVal = sum(load_a[timeLower:timeUpper+1])
stats['usageIncluded'] = usageVal / 3600.0
stats['usageExcluded'] = sum(load_a[0:timeLower]) + sum(load_a[timeUpper:]) / 3600.0
stats['usageFraction'] = usageVal/maxUsage
stats['residualWork'] = sum(load_a[timeUpper+1:]) / 3600

print(f"\nLoad statistics:")
print(f"           min = {stats['minLoad']}")
print(f"        median = {stats['medianLoad']}")
print(f"           max = {stats['maxLoad']}")
print(f"          mean = {stats['meanLoad']}")
print(f"        %usage = {100 * stats['usageFraction']}")
print(f" residual work = {stats['residualWork']}")

slice_df = job_df.loc[(job_df['Start Time'] >= timeLower) & (job_df['Start Time'] <= timeUpper)]
stats['minWait'] = slice_df['Wait Time'].min()
stats['medianWait'] = slice_df['Wait Time'].median()
stats['maxWait'] = slice_df['Wait Time'].max()
stats['meanWait'] = slice_df['Wait Time'].mean()

print(f"\nWait time statistics:")
print(f"    min = {stats['minWait']}")
print(f" median = {stats['medianWait']}")
print(f"    max = {stats['maxWait']}")
print(f"   mean = {stats['meanWait']}")

stats['minTurnaroundTime'] = slice_df['Turnaround Time'].min()
stats['medianTurnaroundTime'] = slice_df['Turnaround Time'].median()
stats['maxTurnaroundTime'] = slice_df['Turnaround Time'].max()
stats['meanTurnaroundTime'] = slice_df['Turnaround Time'].mean()

print(f"\nTotal job time statistics:")
print(f"    min = {stats['minTurnaroundTime']}")
print(f" median = {stats['medianTurnaroundTime']}")
print(f"    max = {stats['maxTurnaroundTime']}")
print(f"   mean = {stats['meanTurnaroundTime']}")

stats_d = {}
stats_d[args.name] = stats
jsonout = open(statsJSON, 'w')
json.dump(stats_d, jsonout, indent=4, default=str)
