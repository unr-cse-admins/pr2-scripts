#!/usr/bin/env python3
import sys
import random
import subprocess
import xml.etree.ElementTree as ET

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

for vm in ["base","pi","c1","c2"]:
    error=subprocess.call(["virsh", "dumpxml", vm, ">", "/tmp/", vm+".xml"])
    if not error:
        #error dumping the xml
        print (error)
    else:
        #start parsing the .xml
        #current issue: how do i into previous command without repeating if i cant stdout the error var in order to call the ET parser
        vm_xml=ET.parse(vm+".xml").getroot()
        for child in vm_xml:
            #trying to find the <devices> section, which contains our interfaces that we care about
            if child.tag == "devices":
                #trying to find the specific interface that we care about
                for device in child:
                    if device.tag == "interface" && device.attrib == "{ 'type': 'bridge'}":
                        #replace mac address with randomly generated one
                        for device_info in device:
                            if device_info.tag == "mac" && device.attrib == "{'address': ''}": #not too sure about how to 'find' the mac info, since each mac in the file is unique
                                #loop through the field, replace the mac in there with new one
                                for i in vm_xml('mac'):
                                    i.text=rand_mac()
                                    #maybe an issue here? there might not be any quotes around this which we'll need in the end, maybe append the quotes around it? force the quotes in the function?


        #writing changes to our .xml file backup, not sure if we send this to a different .xml file
        # vm_xml.write("/tmp/"+vm+".xml")


        #in theory, mac addresses should be replaced at this point, so afterward we have to create a new virtual disk, anything else?
