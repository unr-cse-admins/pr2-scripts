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
    return "10:%02x:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255)
    )

def create():
    print("Creating bridge...")
    vm_bridge = "pr2-" + args.prefix + "-br"
    subprocess.run(["ovs-vsctl", "add-br", vm_bridge])
    subprocess.run(["ovs-vsctl", "add-br", "external-br"])

    vms = ("base", "pi", "c1", "c2")
    for vm in vms:

        #generate new drive using `truncate`
        print("Creating a virtual drive for: " + vm_name)
        file = open(vm_drive, "w")
        file.truncate(16106127360)
        file.close()

        #generating new fields for renaming in the .xml
        vm_name = args.prefix + "-" + vm
        vm_drive = "/var/lib/libvirt/images/" + args.prefix + "-" + vm + ".qcow2" #before doing this, still need to do system call to make new drive
        vm_uuid = uuid.uuid4()
        mac_int = rand_mac()
        if vm is "base" or vm is "pi":
            mac_ex = rand_mac()

        #done with the uuid
        vm_xml = ET.parse("vms/" + vm + ".xml")

        print("Renaming VM for: " + vm_name)
        # print("VM Name before: " + vm_xml.find('name').text)
        vm_xml.find('name').text = str(vm_name)
        # print("VM Name after: " + vm_xml.find('name').text)

        print("Generating new UUID for: " + vm_name)
        # print("UUID Before: " + vm_xml.find('uuid').text)
        vm_xml.find('uuid').text = str(vm_uuid)
        # print("UUID After: " + vm_xml.find('uuid').text)

        #replacing drive name
        for device in vm_xml.findall("devices/disk"):
            if device.attrib["device"] == "disk":
                # print("Old drive filepath: " + device.find("source").attrib["file"])
                device.find("source").attrib["file"] = vm_drive
                # print("New drive filepath: " + device.find("source").attrib["file"])

        #replacing mac addresses for bridges + updating bridge names, $$$PREFIX$$$-br for internal, "external-br" for external bridges
        for interface in vm_xml.findall("devices/interface"):
            if interface.find("mac").attrib["address"] == "$$$" + (vm).upper() + "_MAC_INTERNAL$$$":
                # print("MAC Address before " + vm_bridge + ": $$$" + (vm).upper() + "_MAC_INTERNAL$$$")
                interface.find("mac").attrib["address"] = mac_int
                interface.find("source").attrib["bridge"] = vm_bridge
                print("Replacing mac address for " + vm_name + "'s bridge " + vm_bridge + " with: " + mac_int)
                # print("MAC Address of " + interface.find("source").attrib["bridge"] + " after: " + interface.find("mac").attrib["address"])
            elif interface.find("mac").attrib["address"] == "$$$" + (vm).upper() + "_MAC_EXTERNAL$$$":
                # print("MAC Address before " + vm_bridge + ": $$$" + (vm).upper() + "_MAC_INTERNAL$$$")
                interface.find("mac").attrib["address"] = mac_ex
                interface.find("source").attrib["bridge"] = "external-br"
                print("Replacing mac address for " + vm_name + "'s bridge external-br with: " + mac_ex)
                # print("MAC Address of " + interface.find("source").attrib["bridge"] + " after: " + interface.find("mac").attrib["address"])

        #creating a new vm instance using the newly-edited .xml file
        print("\nCreating new VM: " + vm_name + "...\n")
        vm_xml.write("/tmp/" + vm_name + ".xml")
        subprocess.run(["virsh", "create", "/tmp/" + vm_name + ".xml"])

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
