name=${1:-LEDscan}
power=1023
nread=15
seq=15
led=1

wave=(0 940 1050 1200 1300)

oneCmd.py idg n8pds meas name=${name}_dark wave=${wave[$led]} power=$power nread=$nread note=led_on

n8led.py --on $led $power
for s in `seq $seq`; do
    oneCmd.py idg n8pds meas name=${name}_on wave=${wave[$led]} power=$power nread=$nread note=led_on
done

n8led.py --off
for s in `seq $seq`; do
    oneCmd.py idg n8pds meas name=${name}_off wave=${wave[$led]} power=$power nread=$nread note=led_off
done

