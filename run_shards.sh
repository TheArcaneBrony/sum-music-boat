#!/usr/bin/env bash

PROCESSES=()
count=0

_exit() {
    echo "existing the script, and killing processes ${PROCESSES[*]} $rpc"
    kill ${PROCESSES[*]} 2>/dev/null
    kill ${rpc}
    exit 0
}

run() {
    if [[ -z $2 ]]; then
        count=$1
    else
        count=$2
    fi
    for (( i=0; i<$count; i++ )); do
        pair=":python3.5 main.py $i $1"
        python3.5 main.py $i $1 &>/dev/null &
        PROCESSES[$i]="$!$pair"
        echo "running shard $i with PID of $!"
        echo "${PROCESSES[@]}"
    done
}

check() {
    output=$(top -b -n 1 -p $1 | tail -n 1 | awk '{print $9;}')
    output=${output%%.*}
    if (( output < 1 )); then
        echo "true"
    fi
}

trap _exit SIGINT

if [[ -z $1 ]]; then
    while true; do
        read -p "What do you wish to do?
1. kill all processes
2. restart all processes
3. start processes
> " option

        case $option in
        1)
            kill ${PROCESSES[*]}
            unset PROCESSES
           ;;
        2)
            kill ${PROCESSES[*]}
            unset PROCESSES
            run $count
            ;;
        3)
            read -p "how many shards to start the process with: " count
            run $count
            ;;
        *)
            echo "please select an option"
            ;;
        esac
        sleep 2
    done
else
    count=0
    if [[ -z $2 ]]; then
        count=$1
        run $count
    else
        count=$2
        run $1 $count
    fi
    python3.5 rpc_server.py &>/dev/null &
    rpc=$!
    while :; do
        for (( i=0; i<$count; i++ )); do
            current=${PROCESSES[$i]}
            KEY="${current%%:*}"
            VALUE="${current##*:}"
            if ! ps -p $KEY >/dev/null; then
                echo "an error occured, restarting, $VALUE"
                kill $KEY
                $VALUE &
                PROCESSES[$i]="$!:$VALUE"
            elif [ "$(check $KEY)" == "true" ]; then
                output=$(top -b -n 1 -p $i | tail -n 1 | awk '{print $9;}')
                output=${output%%.*}
                echo "Output $output"
                echo "a shard went down, restarting, $VALUE"
                kill ${PROCESSES[*]}
                $VALUE &
                PROCESSES[$i]="$!:$VALUE"
            fi
        done
    sleep 100
    done
fi