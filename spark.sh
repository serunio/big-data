if [ $# -ne 1 ]; then
  echo "Usage: $0 <job.py>"
  exit 1
fi

sudo docker exec -it spark spark-submit /jobs/"$1"