#!/usr/bin/env bash

sudo systemctl start docker.service

set -e 

mkdir -p hdfs/nn
mkdir -p hdfs/dn1
mkdir -p hdfs/dn2
mkdir -p hdfs/dn3
mkdir -p jobs

sudo docker compose up -d --build