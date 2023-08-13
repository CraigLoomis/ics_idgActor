#!/bin/bash

p940="970 980 990 1000 1005 1010"
p1050="600 650 700 750 800 850 900"
p1200="500 550 600 650 700 750 800"
p1300="875 900 925 950 975 1000 "

#p940=990
#p1050=700
#p1200=600
#p1300=925

#p940=1005
#p1050=850
#p1200=750
#p1300=975

#p940="970 980 1000 1010"
#p1050="600 650 750 800 900"
#p1200="500 550 650 700 800"
#p1300="875 900 950 1000 "

p940=990
p1050=700
p1200=500
p1300=950

defsleep=1
nread=100
ngroup=30
name=h4run_1300_1

# oneCmd.py hx_n8 ramp nread=50 exptype=dark objname=${name}
for w in 1300; do
    plist=$(eval "echo \$p$w")

    # Fire 3 15-read ramps -- ~500s of acquisition
    # Wait ~30s (>2 reads)
    ( oneCmd.py hx_n8 ramp nread=20 exptype=flat objname=${name}_led${w}
      oneCmd.py hx_n8 ramp nread=20 exptype=flat objname=${name}_led${w} ) &
    sleep 30

    sleep=$defsleep
    
    for p in $plist; do
        ./n8scan.sh  -w $w -p $p -g $ngroup -c $nread -d $ngroup -s $sleep -S $sleep -l -N ${name} ${name}
    done
    oneCmd.py hx_n8 ramp nread=20 exptype=dark objname=${name}
done
