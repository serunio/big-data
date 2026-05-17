#!/usr/bin/env bash

set -e

if [ $# -ne 2 ]; then
  echo "Usage: $0 <interface> <host_id>"
  echo "example: $0 eno1 200"
  exit 1
fi

INTERFACE=$1
HOST_ID=$2

# np. 192.168.8.0/24
SUBNET=$(ip route | awk -v iface="$INTERFACE" '$0 ~ iface && $1 ~ "/" {print $1; exit}')

# np. 192.168.8.1
GATEWAY=$(ip route | awk -v iface="$INTERFACE" '$0 ~ iface && $1 == "default" {print $3}')

# np. 192.168.8
NETWORK_PREFIX=$(echo "$SUBNET" | cut -d/ -f1 | awk -F. '{print $1"."$2"."$3}')

# np. 192.168.8.200
HOST_IP="${NETWORK_PREFIX}.${HOST_ID}"

echo "INTERFACE=$INTERFACE"
echo "SUBNET=$SUBNET"
echo "GATEWAY=$GATEWAY"
echo "HOST_IP=$HOST_IP"

sudo docker network create -d macvlan \
  --subnet="$SUBNET" \
  --gateway="$GATEWAY" \
  -o parent="$INTERFACE" \
  hadoop_net || true

sudo ip link add macvlan0 link "$INTERFACE" type macvlan mode bridge || true
sudo ip addr add "${HOST_IP}/24" dev macvlan0 || true
sudo ip link set macvlan0 up

mkdir -p hdfs/nn
mkdir -p hdfs/dn1
mkdir -p hdfs/dn2
mkdir -p hdfs/dn3
mkdir -p jobs

sudo docker compose up -d --build