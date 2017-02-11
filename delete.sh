#!/bin/bash

COUNT=0

while true; do

	SIZE=$(du ./cache | cut -f 1)

	if (( SIZE > 36700160 )); then
		COUNT=$((COUNT+1))
		echo "$COUNT Exceeded limit, deleting"
		rm -rf cache/*
	fi
	
	sleep 300
done
