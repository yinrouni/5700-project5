# tmp port test
NS=cs5700cdnproject.ccs.neu.edu
NAME=cs5700cdn.example.com
while true; do
        for port in {50004..50004}; do
                echo "port $port"
                IP=`dig +short +time=2 +tries=1 -p $port @$NS $NAME | head -1`
                echo $IP
                if [[ $IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
                   wget http://$IP:$port/wiki/Main_Page
                fi
                sleep 1

                echo 'DONE'
        done
        break
done
