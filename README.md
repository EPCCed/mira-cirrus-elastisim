# MIRA - Cirrus scheduler modelling 

Repository for data and configuration for modelling scheduling on 
[Cirrus](https://www.cirrus.ac.uk) using [ElastiSim](https://elastisim.github.io/).

## Models

* CPU partition
  - Simple occupancy model
    + System description: each ElastiSim node represents a single core to allow for shared node use
    + Application model: defined as simple runtime (`busy_wait`); runtime scales perfectly with number of cores
    + Jobs: define two properties: `iterations` runtime in minutes at base node count, `base_nodes` number of
      cores for the base job definition (ratio of used nodes to base nodes is used to compute runtime)
    