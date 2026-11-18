#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
stl_Ly3_E1.py - Example STL script for TRex load generator.

This is a sample STL (Simple Traffic Generator) program that can be used
to generate traffic with the TRex traffic generator.
"""

from trex.stl.api import *

def create_stl_program():
    """
    Creates and returns an STL program for TRex.
    
    Returns:
        STLProgram: The TRex STL program object.
    """
    # Create a simple stream
    s1 = STLStream(
        packet=STLPktBuilder(
            pkt=Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / UDP(dport=12345, sport=12345) / "TRex traffic generator test",
            vm=STLVmRaw(l2_len=64)
        ),
        mode=STLTXCont()
    )
    
    # Create and return the STL program
    return STLProgram(streams=[s1])

# If this script is run directly, create a simple test
if __name__ == "__main__":
    print("This is a sample STL script for TRex.")
    print("It can be used with different configurations.")