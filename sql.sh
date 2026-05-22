#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Usage: $0 <script.sql>"
  exit 1
fi

sudo docker exec -i postgres psql -U cats -d cats_knowledge < db/"$1"