#!/bin/bash

script_path="$(realpath "$0")"
script_dir="$(dirname "$script_path")"
relative_path="../../submodules/TimeStick/DRV"
absolute_path="$(realpath "$script_dir/$relative_path")"

mv "$absolute_path/Makefile.txt" "$absolute_path/Makefile" > /dev/null 2>&1

# Compile and install the driver
sudo make clean -C "$absolute_path" > /dev/null 2>&1
sudo make -C "$absolute_path" > /dev/null 2>&1
sudo make install -C "$absolute_path" > /dev/null 2>&1

# Unload conflicting modules
sudo rmmod cdc_mbim > /dev/null 2>&1
sudo rmmod cdc_ncm > /dev/null 2>&1

# Detect and reset the ASIX USB device (0b95:1790)
USB_DEV_PATH=$(for d in /sys/bus/usb/devices/*; do
    if [[ -f "$d/idVendor" && -f "$d/idProduct" ]]; then
        vendor=$(cat "$d/idVendor")
        product=$(cat "$d/idProduct")
        if [[ "$vendor" == "0b95" && "$product" == "1790" ]]; then
            echo "$d"
        fi
    fi
done)

if [[ -z "$USB_DEV_PATH" ]]; then
    echo "ℹ️ ASIX USB device not found. Please insert the TimeStick and run the script again."
    exit 1
fi

# echo "ℹ️ ASIX device found at: $USB_DEV_PATH"

USB_DEV=$(basename "$USB_DEV_PATH")

# echo "ℹ️ Resetting USB device $USB_DEV..."
echo 0 | sudo tee /sys/bus/usb/devices/$USB_DEV/authorized > /dev/null
sleep 2
echo 1 | sudo tee /sys/bus/usb/devices/$USB_DEV/authorized > /dev/null
# echo "ℹ️ Reset completed."

# Load the driver module
sudo modprobe ax_usb_nic > /dev/null 2>&1
