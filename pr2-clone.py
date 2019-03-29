#!/usr/bin/env python3
import sys
import random
import subprocess
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import argparse
import os
import libvirt
import inspect

parser = argparse.ArgumentParser()
parser.add_argument("action", type = str, choices = ["create", "remove"])
parser.add_argument("prefix", help = "prefix of the VMs (one word description)")
args = parser.parse_args()

def main():
    if args.action == "create":
        return create()
    elif args.action == "remove":
        return remove()
    else:
        return 1


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

def create():
    print("Creating...")
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

def remove():
    internal_bridge = "pr2-" + args.prefix + "-br"
    vms = []
    for file in os.listdir("vms"):
        vms.append(args.prefix + "-" + os.path.splitext(file)[0])
    conn = libvirt.open("qemu:///system")
    for vm in vms:
        try:
            domain = conn.lookupByName(vm)
        except:
            continue
        try:
            domain.destroy() # shutdown VM if it is running
        except:
            pass
        xml = ET.fromstring(domain.XMLDesc(0))
        disks = xml.findall("devices/disk")
        for disk in disks:
            if disk.attrib["device"] == "disk":
                disk_image = disk.find("source").attrib["file"]
                try:
                    os.remove(disk_image)
                except OSError as e:
                    print("Removing", disk_image+":", e.strerror, file=sys.stderr)
                    pass
        domain.undefine()
    conn.close()
    subprocess.run(['ovs-vsctl', 'del-br', internal_bridge])
    return 0

main()