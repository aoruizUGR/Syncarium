#!/bin/bash

# First use: $ sudo chmod u+x config_hugepages.sh
# Usage:     $ sudo ./config_hugepages.sh 

# Assign 1024 hugepages
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages > /dev/null 2>&1

# Create and mount /mnt/huge if it doesn't exist
sudo mkdir -p /mnt/huge > /dev/null 2>&1
sudo mount -t hugetlbfs nodev /mnt/huge > /dev/null 2>&1
