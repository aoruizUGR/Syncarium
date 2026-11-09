#!/bin/bash
# Usage:
#   sudo ./config_pps_Intel810.sh <interface> <SMA1|SMA2> <IN|OUT>

INTERFACE=$1
SMA=$2          # SMA1 or SMA2
MODE=$3         # IN or OUT

# Parameter validation
if [[ -z "$INTERFACE" || -z "$SMA" || -z "$MODE" ]]; then
    echo "Usage: sudo $0 <interface> <SMA1|SMA2> <IN|OUT>"
    exit 1
fi

ETH="$INTERFACE"
SMA_PATH="/sys/class/net/$ETH/device/$SMA"

# Verify that the SMA control file exists
if [[ ! -e "$SMA_PATH" ]]; then
    echo "❌ Error: $SMA is not available on interface $ETH"
    exit 1
fi

#echo "ℹ️ Configuring $SMA as $MODE on interface $ETH"

#############################################
# Configure SMA direction
#############################################

if [[ "$MODE" == "IN" ]]; then
    echo "1" | sudo tee "$SMA_PATH" > /dev/null
    # echo "✔ $SMA set to input (1PPS IN)"

elif [[ "$MODE" == "OUT" ]]; then
    echo "2" | sudo tee "$SMA_PATH" > /dev/null
    # echo "✔ $SMA set to output (1PPS OUT)"

else
    # echo "❌ Invalid MODE. Use IN or OUT"
    exit 1
fi