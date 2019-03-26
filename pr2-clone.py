#!/usr/bin/env python3
import sys
import random
import subprocess
import xml.etree.ElementTree as ET
import uuid
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("prefix")
args = parser.parse_args()
print(args.prefix)

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

vm_bridge = "pr2-" + args.prefix + "-br"
subprocess.run(["ovs-vsctl", "add-br", vm_bridge])
#create new ovs bridge `ovs-vsctl`

vms = ("base", "pi", "c1", "c2")
for vm in vms:
    #generate new drive `truncate`
    #generating new fields for renaming in the .xml

    vm_name = args.prefix + "-" + vm
    vm_drive = "/var/lib/libvirt/images/" + args.prefix + "-" + vm + ".qcow2" #before doing this, still need to do system call to make new drive
    vm_uuid = uuid.uuid4()
    mac_int = rand_mac()
    if vm is "base" or vm is "pi":
        mac_ex = rand_mac()
        print(vm_name, vm_drive, vm_uuid, mac_int, mac_ex, vm_bridge)
    else:
        print(vm_name, vm_drive, vm_uuid, mac_int, vm_bridge)

    #done with the uuid
    vm_xml = ET.parse("vms/" + vm + ".xml").getroot()
    vm_xml.find('uuid').text = vm_uuid #uuidgen



#start parsing and replacing stuff, write it to /tmp/<name>.xml, remove when done
