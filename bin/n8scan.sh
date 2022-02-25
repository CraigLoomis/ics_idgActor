usage() {
    error=$1

    if test -n "$error"; then
        echo "error: $error"
        echo
    fi 1>&2

    echo "usage: $0 [-w 0|940|1050|1200|1300] [-p 0..1023] [-c count] [-N note] [-g ngroups] [-s sleep] [-d ndarks] testName" 1>&2
    exit 1;
}

declare -A leds
leds+=([0]=0 [940]=1 [1050]=2 [1200]=3 [1300]=4)
wave=0
power=0
count=15
ngroups=1
ndarks=1
sleep=60
offSleep=5
note="note"

while getopts "nlw:p:c:N:g:s:S:d:" opt; do
    case "$opt" in
        w)
            wave=${OPTARG}
            (( wave == 0 || wave == 940 || wave == 1050 || wave == 1200 || wave == 1300 )) || usage "invalid wavelength: $wave"
            ;;
        p)
            power=${OPTARG}
            (( power >= 0 && power <= 1023 )) || usage "invalid power: $power"
            ;;
        d)
            ndarks=${OPTARG}
            ;;
        c)
            count=${OPTARG}
            ;;
        g)
            ngroups=${OPTARG}
            ;;
        N)
            note=${OPTARG}
            ;;
        s)
            sleep=${OPTARG}
            ;;
        S)
            offSleep=${OPTARG}
            ;;
        n)
            norun=true
            ;;
        l)
            controlLeds=true
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))
name=$1
name=${name}_${wave}_${power}

(( $power > 0 && $wave == 0 )) && usage "if wavelength is not set, then power must be 0"

led=${leds[$wave]}
echo args: name=$name wave=$wave led=$led power=$power nread=$count note="${note}"

test -n "$name" || usage "name required"

if test -n "$note"; then
    noteArg="note='$note'"
else
    noteArg=""
fi

if test -n "$controlLeds"; then
    if test $power -eq 0; then
        n8led.py --off
        sleep 10
    else
        oneCmd.py idg n8pds meas name=${name}_predark wave=$wave power=0 nread=$count $noteArg
        n8led.py --on $led $power
        sleep $sleep
    fi
fi

for i in `seq $ngroups`; do
    oneCmd.py idg n8pds meas name=$name wave=$wave power=$power nread=$count $noteArg
done

if test -n "$controlLeds"; then
    n8led.py --off
    sleep $offSleep
fi

for i in `seq $ndarks`; do
    oneCmd.py idg n8pds meas name=${name}_dark wave=$wave power=0 nread=$count $noteArg
done
