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
parser.add_argument('-d', dest='datadir', type=str, action='store', default=".", help='Directory containing output files from Elastisim simulation. Output file must be called "job_statistics.csv". Default: current directory.')
args = parser.parse_args()

# Setup the file names
csvJobStatsName = f'{args.datadir}/job_statistics.csv'

usagePlotFile = f'{args.prefix}_measured_load.png'
usagePlotFilePeriod = f'{args.prefix}_measured_load_period.png'
statsJSON = f'{args.prefix}_measured_stats.json'

csvfile = open(csvJobStatsName, 'r')

csvreader = csv.DictReader(csvfile)
jobList = []
maxtime = 0
for row in csvreader:
    jobList.append(row)
    endtime = int(row['End Time'])
    if endtime > maxtime:
        maxtime = endtime

job_df = pd.DataFrame(jobList)
job_df['Start Time'] = job_df['Start Time'].astype(float)
job_df['Wait Time'] = job_df['Wait Time'].astype(float)
job_df['End Time'] = job_df['End Time'].astype(float)
job_df['Nodes'] = job_df['Nodes'].astype(int)
job_df['Makespan'] = job_df['Makespan'].astype(float)
job_df['Coreh'] = job_df['Makespan'] * job_df['Nodes'] / 3600.0
job_df['Turnaround Time'] = job_df['Turnaround Time'].astype(float)
job_df['Efficiency'] = job_df['Makespan'] / job_df['Turnaround Time']

load_a = np.zeros(maxtime+1, dtype=int)
for job in jobList:
    temp_a = np.zeros(maxtime+1, dtype=int)
    istart = math.floor(float(job['Start Time']))
    iend = math.ceil(float(job['End Time']))
    nodes = int(job['Nodes'])
    temp_a[istart:iend] = nodes
    load_a = load_a + temp_a

# With the moldable jobs, start and end times can be fractional
# This means that when they are floor'd and ceil'd you can end
# up with times where the load exceeds the number of cores available.
# Rather than doing something intelligent, we clip the array so it is
# in the correct range
load_a = np.clip(load_a, a_min=0, a_max=nCoreTot)

plt.figure(figsize=(15, 5))
plt.plot(load_a, label='Overall')
plt.xlabel("Time")
plt.ylabel("Cores in use")
sns.despine()
plt.savefig(usagePlotFile, dpi=300, bbox_inches='tight')

# Reduced analysis period
plt.figure(figsize=(15, 5))
plt.plot(load_a, label='Overall')
plt.xlabel("Time")
plt.ylabel("Cores in use")
plt.xlim([timeLower, timeUpper])
sns.despine()
plt.savefig(usagePlotFilePeriod, dpi=300, bbox_inches='tight')

maxUsage = (timeUpper - timeLower) * nCoreTot

# Descriptive statistics
stats = {}

stats['nJobStart'] = sum((job_df['Start Time'] >= timeLower) & (job_df['Start Time'] <= timeUpper))

print(f"\n\nSimulation statistics (analysis period):")
print(f"\nJob data:")
print(f"    nJobs = {stats['nJobStart']}")

stats['minLoad'] = min(load_a[timeLower:timeUpper+1])
stats['maxLoad'] = max(load_a[timeLower:timeUpper+1])
stats['medianLoad'] = statistics.median(load_a[timeLower:timeUpper+1])
stats['meanLoad'] = statistics.mean(load_a[timeLower:timeUpper+1])

usageVal = sum(load_a[timeLower:timeUpper+1])
stats['usageIncluded'] = usageVal / 3600.0
stats['usageExcluded'] = (sum(load_a[0:timeLower]) + sum(load_a[timeUpper:])) / 3600.0
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

print(f"\nTurnaround time statistics:")
print(f"    min = {stats['minTurnaroundTime']}")
print(f" median = {stats['medianTurnaroundTime']}")
print(f"    max = {stats['maxTurnaroundTime']}")
print(f"   mean = {stats['meanTurnaroundTime']}")

stats_d = {}
stats_d[args.prefix] = stats
jsonout = open(statsJSON, 'w')
json.dump(stats_d, jsonout, indent=4, default=str)
