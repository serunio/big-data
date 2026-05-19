#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Usage: $0 <script.py>"
  exit 1
fi

sudo docker exec -it spark python3 /scripts/"$1"