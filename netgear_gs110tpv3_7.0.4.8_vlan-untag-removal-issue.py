from snimpy.manager import Manager as M
from snimpy.manager import load
from pathlib import Path
from collections import defaultdict


#------------------------------------------------------------------------------------


def vlan_get_config(m: M) -> dict:
    "Compiles a dict with all the vlans and connected ports"
    result = dict()
    size = 0
    for vlanid in [int(vlanid) for vlanid in m.dot1qVlanStaticRowStatus] + [1]:
        name = m.dot1qVlanStaticName[vlanid]
        raw = {
            "dot1qVlanStaticEgressPorts": m.dot1qVlanStaticEgressPorts[vlanid],
            "dot1qVlanStaticUntaggedPorts": m.dot1qVlanStaticUntaggedPorts[vlanid],
        }
        expanded = defaultdict(list)
        size = len(raw["dot1qVlanStaticEgressPorts"])
        for i in range(size):
            for bit in range(1, 9):
                mask = 1 << (8 - bit)
                for key in raw:
                    if mask & raw[key][i]:
                        expanded[key].append(i * 8 + bit)
        expanded["name"] = name
        result[vlanid] = expanded
    return result, size


def create_snmp_hex_bitmask(ports, size=40):
    "Creates a hex bit mask in the format that SNMP expects."
    mask = bytearray(size)
    for port in ports:
        bport = port - 1
        byte_pos = bport // 8
        bit_pos = bport % 8
        bit_mask = 1 << (8 - bit_pos - 1)
        mask[byte_pos] = mask[byte_pos] | bit_mask
    return bytes(mask)


#------------------------------------------------------------------------------------

def main(vlan_id=None, port=None, host=None, community=None, device=None):
    new_untagged_ports = {1} # only port 1 is suspect to this test

    load("SNMPv2-MIB")
    m = M(host=host, community=community, version=2)
    description = m.sysDescr
    mib_path = Path(__file__).parent / "mibs"
    
    load(str(mib_path / device / "IF-MIB.txt"))
    load(str(mib_path / device / "Q-BRIDGE-MIB.txt"))
    current_config, current_size = vlan_get_config(m)

    if vlan_id in current_config:
        print(f"This test script expects a clean state. Remove vlan {vlan_id} completely first. VLAN PVID on port 1 should be 1 for this test")
        exit(-1)

    # Creating VLAN Id from scratch
    print(f"Creating VLAN: {vlan_id}")
    m.dot1qVlanStaticRowStatus[vlan_id] = "createAndWait"
    m.dot1qVlanStaticName[vlan_id] = f"vlan {vlan_id}"
    current_config, current_size = vlan_get_config(m)

    for current_vlan, current_port_tables in current_config.items():
        if vlan_id == current_vlan:
            continue
        # Check from where it needs to be removed:
        current_egress = current_port_tables["dot1qVlanStaticEgressPorts"].copy()
        current_untagged = current_port_tables["dot1qVlanStaticUntaggedPorts"].copy()

        for port in new_untagged_ports:
            if port in current_untagged:
                print(f"Removing egress port (and untagged flag) {port} from VLAN {current_vlan}")
                current_egress.remove(port)
                current_untagged.remove(port)

        if (
            current_port_tables["dot1qVlanStaticUntaggedPorts"] != current_untagged
            or current_port_tables["dot1qVlanStaticEgressPorts"] != current_egress
        ):
            # this step is the problematic one, vlan 1 is not removed from port 1
            prev_egress_ports = m.dot1qVlanStaticEgressPorts[current_vlan]
            m.dot1qVlanStaticEgressPorts[current_vlan] = create_snmp_hex_bitmask(
                current_egress, current_size
            )
            prev_untagged_ports = m.dot1qVlanStaticUntaggedPorts[current_vlan]
            m.dot1qVlanStaticUntaggedPorts[current_vlan] = create_snmp_hex_bitmask(
                current_untagged, current_size
            )

            #assert prev_egress_ports != m.dot1qVlanStaticEgressPorts[current_vlan]
            #assert prev_untagged_ports != m.dot1qVlanStaticUntaggedPorts[current_vlan]


    # adding new vlan id (this works fine)
    m.dot1qVlanStaticEgressPorts[vlan_id] = create_snmp_hex_bitmask({1}, current_size)
    m.dot1qVlanStaticUntaggedPorts[vlan_id] = create_snmp_hex_bitmask({1}, current_size)
    m.dot1qPvid[port] = vlan_id

    print("Done - check on the config website if VLAN ID 1 is still assigned to port 1.")

# ----------------------------------------------------------------------------
    
main(vlan_id=1001, port=1, host="10.30.2.21", community="very-private", device="GS110TPv3")
