# Take a number of "dark" runs.

n8led.py --off
for i in `seq 100`; do
    oneCmd.py idg n8pds meas name=LEDdark wave=0 power=0 nread=60 note=dark_after_pin_swap
done
