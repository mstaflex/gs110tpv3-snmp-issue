# README

The script 'netgear_gs110tpv3_7.0.4.8_vlan-untag-removal-issue.py' mimics a problem that
we came across in our Python steered SNMP-switch-control framework.

We tested against multiple different switches from Netgear and only one is behaving erratically.

The attached script adds a new VLAN ID, assigns this ID to port 1 and also removes the original
VLAN ID (1) from this port. On the switch in question GS110TPv3 (running 7.0.4.8 newest FW) the removal
doesn't work. However on a GS324T and a GS724TP this has the intended affect and works flawlessly.


# Versions

## Software

Python3 - 3.8.6
Snimpy  - 0.8.14
pysmi   - 0.3.4

## Hardware

GS110TPv3 - 7.0.4.8
GS324T    - 1.0.0.16


# Steps to reproduce

1. Install Snimpy for Python(3) - pysmi is a prerequisite.

2. Adapt 'netgear_gs110tpv3_7.0.4.8_vlan-untag-removal-issue.py' to the local setup,
mainly changing 'host' to the switch IP and configure SNMPv2 community password with 
write access in the switch and also add the community string in the script
(currently set to 'very-private'):

>  def main(vlan_id=1001, port=1, host="10.30.2.21", community="very-private", device="GS110TPv3"):


3. Make sure the switch is reset to factory reset values and specifically remove VLAN ID 1001 prior to
every execution of the script (also make sure that PVID and untagged ports are set back to e.g. 1 for port 1).

4. Then execute the script.

If the erroneous situation is detected any further execution is halted by two asserts in the script,
which check if the intended change in configuration was actually executed by the switch or not.
It might be meaningful to remove the asserts while debugging to have all steps of the script be executed
till the end, instead of ending it early.
