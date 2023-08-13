#!/bin/bash

p940="970 980 990 1000 1005 1010"
p1050="600 650 700 750 800 850 900"
p1200="500 550 600 650 700 750 800"
p1300="875 900 925 950 975 1000 "

defsleep=120
nread=120
ngroup=30

for w in 940 1050 1200 1300; do
    plist=$(eval "echo \$p$w")
    if (( $w == 1050 )); then
        sleep=360
    else
        sleep=$defsleep
    fi
    
    for p in $plist; do
        ./n8scan.sh  -w $w -p $p -g $ngroup -c $nread -d $ngroup -s $sleep -l -N repeat_at_higher_bias calib4_${w}_${p}_30V
    done
done
