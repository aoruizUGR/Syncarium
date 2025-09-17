#!/bin/bash

# Script to configure GPIO_4 as PPS input or output on an Intel 710 NIC
# Usage: sudo ./config_pps_Intel710.sh <namespace> <interface> <in|out>

NAMESPACE=$1
INTERFACE=$2
MODE=$3

# Get the PTP device number associated with the interface
PTP_DEVICE=$(sudo ip netns exec $NAMESPACE ethtool -T "$INTERFACE" 2>/dev/null | awk -F': ' '/PTP Hardware Clock:/ {print $2}')

# Verify a valid PTP_DEVICE number
if [[ -n "$PTP_DEVICE" && "$PTP_DEVICE" =~ ^[0-9]+$ ]]; then
    PTP_PATH="/sys/class/ptp/ptp$PTP_DEVICE"
else
    echo "Could not determine PTP system device from interface name $INTERFACE" >&2
fi

# Determine PHC based on the last digit of the interface name
if [[ "$INTERFACE" =~ [0-9]+$ ]]; then
    LAST_CHAR="${BASH_REMATCH[0]}"
    PHC=$((LAST_CHAR % 4))  # Only 0,1,2,3
else
    echo "ℹ️ Could not determine port number from interface name."
    exit 1
fi

# Configure PPS output mode
if [ "$MODE" == "OUT" ]; then
    #echo "ℹ️ Setting SMA1 as PPS output with PHC=$PHC..."
    echo "2 $PHC" | sudo tee "$PTP_PATH/pins/GPIO_4" > /dev/null
    echo "$PHC 1 1 1 1 1" | sudo tee "$PTP_PATH/period" > /dev/null

# Configure PPS input mode
elif [ "$MODE" == "IN" ]; then
    #echo "ℹ️ Setting SMA1 as PPS input with PHC=$PHC..."
    echo "1 $PHC" | sudo tee "$PTP_PATH/pins/GPIO_4" > /dev/null
    echo "$PHC 1" | sudo tee "$PTP_PATH/extts_enable" > /dev/null
fi
