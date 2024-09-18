#!/bin/bash

model=$1

# Cleanup
# rm -f $PWD/$model/data/output/*.csv

docker run -v $PWD/$model/data:/data -v $PWD/algorithm:/algorithm --name $model --detach elastisim /data/input/configuration.json --log=root.thresh:warning 
sleep 20
docker container ls
echo "[$(date)] Starting running $model"

docker exec $model python3 /algorithm/algorithm.py

echo "[$(date)] Finished running $model"

docker logs $model


