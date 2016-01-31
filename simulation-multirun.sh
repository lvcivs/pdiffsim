#!/bin/bash
# runs the simulation repeatedly and stores results in subfolders
# first argument: name of config file
# second argument: number or runs
for i in $(seq -f "%05g" 0 $2) # 10
	do
		python3 pdiffsim.py $1.cfg $i
		if test -e "$1.log/$i/frequencies.dat"
		then Rscript frequencies.R $1.log/$i
		fi
		grep . $1.log/$i/frequencies.dat | tail -1 >> $1.log/final_frequencies.txt
		#echo 123
	done

