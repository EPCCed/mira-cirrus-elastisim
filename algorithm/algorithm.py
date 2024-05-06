# This file is part of the ElastiSim software.
#
# Copyright (c) 2022, Technical University of Darmstadt, Germany
#
# This software may be modified and distributed under the terms of the 3-Clause
# BSD License. See the LICENSE file in the base directory for details.
from typing import Any
from elastisim_python import JobState, JobType, NodeState, pass_algorithm, Job, Node, InvocationType


def schedule(jobs: list[Job], nodes: list[Node], system: dict[str, Any]) -> None:
    time = system['time']

    pending_jobs = [job for job in jobs if job.state == JobState.PENDING]
    running_jobs = [job for job in jobs if job.state == JobState.RUNNING]
    reconfiguring_jobs = [job for job in jobs if job.state == JobState.PENDING_RECONFIGURATION or
                          job.state == JobState.IN_RECONFIGURATION]
    completed_jobs = [job for job in jobs if job.state == JobState.COMPLETED]
    killed_jobs = [job for job in jobs if job.state == JobState.KILLED]

    free_nodes = [node for node in nodes if node.state == NodeState.FREE]
    allocated_nodes = [node for node in nodes if node.state == NodeState.ALLOCATED]
    reserved_nodes = [node for node in nodes if node.state == NodeState.RESERVED]

    if system['invocation_type'] == InvocationType.INVOKE_SCHEDULING_POINT:
        job = system['job']
        num_nodes_to_expand = min(len(free_nodes), job.num_nodes_max - len(job.assigned_nodes))
        if num_nodes_to_expand > 0:
            job.assign(free_nodes[:num_nodes_to_expand])
            del free_nodes[:num_nodes_to_expand]
    elif system['invocation_type'] == InvocationType.INVOKE_EVOLVING_REQUEST:
        job = system['job']
        evolving_request = system['evolving_request']
        num_nodes = len(job.assigned_nodes)
        diff = evolving_request - num_nodes
        if diff < 0:
            job.remove(job.assigned_nodes[diff:])
        elif len(free_nodes) >= diff:
            job.assign(free_nodes[:diff])
    else:
        for job in pending_jobs:
            if job.type == JobType.RIGID:
                if job.num_nodes <= len(free_nodes):
                    job.assign(free_nodes[:job.num_nodes])
                    del free_nodes[:job.num_nodes]
                else:
                    break
            else:
                num_nodes_to_assign = min(len(free_nodes), job.num_nodes_max)
                if num_nodes_to_assign >= job.num_nodes_min:
                    job.assign(free_nodes[:num_nodes_to_assign])
                    del free_nodes[:num_nodes_to_assign]
                else:
                    break


if __name__ == '__main__':
    url = 'ipc:///tmp/elastisim.ipc'
    pass_algorithm(schedule, url)
