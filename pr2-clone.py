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
import re

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

        #generating new fields for renaming in the .xml
        vm_name = args.prefix + "-" + vm
        vm_drive = "/var/lib/libvirt/images/" + args.prefix + "-" + vm + ".qcow2" #before doing this, still need to do system call to make new drive
        vm_uuid = uuid.uuid4()
        vm_br = args.prefix + "-br"
        mac_int = rand_mac()
        if vm is "base" or vm is "pi":
            mac_ex = rand_mac()

        #done with the uuid
        print("Generating new UUID for: " + vm_name)
        vm_xml = ET.parse("vms/" + vm + ".xml").getroot()
        vm_xml.find('uuid').text = vm_uuid

        #generate new drive using `truncate`
        print("Creating a virtual drive for: " + vm_name)
        file = open(vm_drive, "w")
        file.truncate(16106127360)
        file.close()

        #replacing drive name
        for device in vm_xml.findall("devices/disk"):
            if device.attrib["device"] == "disk":
                device.find("source").attrib["file"] = vm_drive

        #replacing mac addresses for bridges + updating bridge names, $$$PREFIX$$$-br for internal, "external-br" for external bridges
        for interface in vm_xml.findall("devices/interface"):
            if interface.find("mac").attrib["address"] == "$$$" + (vm).upper() + "_MAC_INTERNAL$$$":
                # print("MAC Address before " + vm_br + ": $$$" + (vm).upper() + "_MAC_INTERNAL$$$")
                interface.find("mac").attrib["address"] = mac_int
                interface.find("source").attrib["bridge"] = vm_br
                # print("MAC Address of " + interface.find("source").attrib["bridge"] + " after: " + interface.find("mac").attrib["address"])
            elif interface.find("mac").attrib["address"] == "$$$" + (vm).upper() + "_MAC_EXTERNAL$$$":
                # print("MAC Address before " + vm_br + ": $$$" + (vm).upper() + "_MAC_INTERNAL$$$")
                interface.find("mac").attrib["address"] = mac_ex
                interface.find("source").attrib["bridge"] = "external-br"
                # print("MAC Address of " + interface.find("source").attrib["bridge"] + " after: " + interface.find("mac").attrib["address"])

        #writing changes to new .xml file (having issues actually writing the string using tostring)
        # final_xml = ET.tostring(vm_xml)
        # input_file = open("/tmp/" + args.prefix + "-" + vm + ".xml" , "w")
        # input_file.write(final_xml)
        # input_file.close()

        #we can also do system calls with our current tree to make the vms for us and then we can simply delete the xmls
        #subprocess.run(["virsh", "create", vm_name + ".xml"])

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
