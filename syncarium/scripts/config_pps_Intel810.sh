#!/bin/bash

# Script to configure SMA1 as PPS input or output on an Intel 810 NIC
# Usage: sudo ./config_pps_Intel710.sh <namespace> <interface> <in|out>

NAMESPACE=$1
INTERFACE=$2
MODE=$3

# Get the PTP device number associated with the interface
PTP_DEVICE=$(sudo ip netns exec $NAMESPACE ethtool -T "$INTERFACE" 2>/dev/null | awk -F': ' '/PTP Hardware Clock:/ {print $2}')

if [[ -n "$PTP_DEVICE" && "$PTP_DEVICE" =~ ^[0-9]+$ ]]; then
    PTP_PATH="/sys/class/ptp/ptp$PTP_DEVICE"
else
    echo "Could not determine PTP system device from interface name $INTERFACE" >&2
fi

# Configure PPS output mode
if [ "$MODE" == "OUT" ]; then
    #echo "ℹ️ Setting SMA1 as PPS output..."
    echo "2 1" | sudo tee "$PTP_PATH/pins/SMA1" > /dev/null
    echo "1 0 0 0 100" | sudo tee "$PTP_PATH/period" > /dev/null
    echo "2 0 0 1 0" | sudo tee "$PTP_PATH/period" > /dev/null

# Configure PPS input mode
elif [ "$MODE" == "IN" ]; then
    echo "ℹ️ Configuration not avalaible yet."
fi
