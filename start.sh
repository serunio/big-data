#!/bin/bash
sudo systemctl start docker.service

mkdir -p hdfs/nn
mkdir -p hdfs/dn1
mkdir -p hdfs/dn2
mkdir -p hdfs/dn3
mkdir -p jobs

sudo docker compose up -d --build

echo "czekanie na podniesienie się kontenerów"
until sudo docker exec nn bash -c "echo ready" 2>/dev/null; do
  sleep 1
done

sudo docker exec --user hadoop nn bash -c   "/opt/hadoop/sbin/start-dfs.sh && /opt/hadoop/sbin/start-yarn.sh"