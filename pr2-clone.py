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

#try to think about arg parsing

vm_bridge = "pr2-" + prefix + "-br"
subprocess.run(["ovs-vsctl", "add-br", vm_bridge])
#create new ovs bridge `ovs-vsctl`

vms = ("base", "pi", "c1", "c2")
for vm in vms:

    #generating new fields for renaming in the .xml
    vm_name = prefix + "-" + vm
    vm_drive = "/var/lib/libvirt/images/" + vm_name + ".qcow2" #before messing with this, still need to do system call to make new drive
    vm_uuid = uuid.uuid4()
    mac_int = rand_mac()
    if vm is "base" or vm is "pi":
        mac_ex = rand_mac()

    #creating new virtual drive
    subprocess.run(["truncate", "-s", "15G", "/tmp/" + vm_name + ".img"])

    #done with replacing uuid
    vm_xml = ET.parse("vms/" + vm + ".xml").getroot()
    vm_xml.find('uuid').text = vm_uuid #uuidgen

    #starting to replace mac address
    print(vm_xml.find('devices').text) #do i have to do wonky stuff to get the specific device? i.e. vm_xml.find('devices').find(`interface`).find('mac')?

    #after parsing, write changes to /tmp/<vm_name>.xml

    #after .xml is updated, create new vm:
    # subprocess.run(["virsh", "create", "/tmp/" + vm_name + ".xml"])
