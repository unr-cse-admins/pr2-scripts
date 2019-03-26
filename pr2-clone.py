#!/usr/bin/env python3
import sys
import random
import subprocess
import xml.etree.ElementTree as ET
import uuid


prefix = sys.argv[1]

#credits to https://gist.github.com/pklaus/9638536#gistcomment-2013303, I guess python doesn't have a random MAC generator so here's our next best option
def rand_mac():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
        )

vms = ("base", "pi", "c1", "c2")
for vm in vms:
    #generating new fields for renaming in the .xml
    vm_name = prefix + "-" + vm
    vm_drive = "/var/lib/libvirt/images/" + prefix + "-" + vm + ".qcow2" #before doing this, still need to do system call to make new drive
    vm_uuid = uuid.uuid4()
    vm_bridge = prefix + "-br"
    mac_int = rand_mac()
    if vm is "base" or vm is "pi":
        mac_ex = rand_mac()
        print(vm_name, vm_drive, vm_uuid, mac_int, mac_ex, vm_bridge)
    else:
        print(vm_name, vm_drive, vm_uuid, mac_int, vm_bridge)

    vm_xml = ET.parse("vms/" + vm + ".xml").getroot()
    vm_xml.find('uuid').text = vm_uuid #uuidgen
