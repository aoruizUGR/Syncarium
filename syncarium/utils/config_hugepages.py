#!/usr/bin/env python3
import os
import subprocess
import sys

def run_command(command):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def configure_hugepages():
    hugepages_content = "1024"
    hugepages_path = "/proc/sys/vm/nr_hugepages"
    
    try:
        with open(hugepages_path, 'w') as f:
            f.write(hugepages_content)
    except IOError:
        return False
    
    mount_point = "/mnt/huge"
    
    if not os.path.exists(mount_point):
        try:
            os.makedirs(mount_point, exist_ok=True)
        except OSError:
            return False
    
    try:
        result = subprocess.run(["mount", "-l"], capture_output=True, text=True, check=True)
        if "hugetlbfs" not in result.stdout:
            if not run_command(f"sudo mount -t hugetlbfs nodev {mount_point}"):
                return False
    except subprocess.CalledProcessError:
        return False
    
    return True

def main():
    if os.geteuid() != 0:
        return 1
    
    if configure_hugepages():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())