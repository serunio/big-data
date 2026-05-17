# big-data
### Build
```
./start.sh <interface> <host_id>
```
W przestrzeni podanego interfejsu zostanie utworzona sieć Dockera hadoop_net, hostowi zostnie przypisane ip w tej sieci. Przed uruchomieniem trzeba w [docker-compose.yaml](docker-compose.yaml) wpisać odpowiednie ipv4_address w dla każdego kontenera.
### Wejście do namenode
Przez Docker:
```
sudo docker exec -it nn bash
su hadoop
```
Przez ssh (przykładowe ip), hasło "hadoop":
```
ssh hadoop@192.168.8.50
```
Jeżeli przed buildem do [authorized_keys](.ssh/authorized_keys) dodamy swój klucz poubliczny (zamiast host) możemy logować się bez hasła.  
Najlepiej do swojego ~/.ssh/config dodać wpis
```
Host nn
	HostName 192.168.8.50
	User hadoop
```
wtedy:
```
ssh nn
```
### spark jobs
Przed uruchomieniem joba trzeba na namenode uruchomić hdfs `start-dfs.sh`  
Potem z hosta:
```
sudo docker exec -it spark spark-submit /jobs/job.py
```
Wyniki na namenode:
```
hdfs dfs -ls /output
```
