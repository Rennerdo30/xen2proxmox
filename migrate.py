#!/usr/bin/python3

import os
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("server")
parser.add_argument("username")
parser.add_argument("password")
parser.add_argument("uuid")
parser.add_argument("storage")
args = parser.parse_args()

# path to xe
XE_PATH = os.path.abspath("./xe")
XE_SERVER = args.server
XE_USERNAME = args.username
XE_PASSWORD = args.password
VM_UUID = args.uuid
PVE_STORAGE = args.storage

def get_vm_name():
    cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME, '-pw', XE_PASSWORD,
           'vm-param-get', 'uuid=' + VM_UUID, 'param-name=name-label']
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    return output


def get_vm_cpu_count():
    cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME, '-pw', XE_PASSWORD,
           'vm-param-get', 'uuid=' + VM_UUID, 'param-name=VCPUs-max']
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    return output


def get_vm_mem_count():
    cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME, '-pw', XE_PASSWORD,
           'vm-param-get', 'uuid=' + VM_UUID, 'param-name=memory-static-max']
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    return output


def get_vm_desc():
    cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME, '-pw', XE_PASSWORD,
           'vm-param-get', 'uuid=' + VM_UUID, 'param-name=name-description']
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    return output


def get_vm_mac():
    cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME, '-pw',
           XE_PASSWORD, 'vm-vif-list', 'uuid=' + VM_UUID, 'params=MAC']
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    output = output[output.find(':') + 1::].strip()
    return output


def collect_metadata():
    metadata = dict()
    metadata['vm_name'] = get_vm_name()
    metadata['vm_cpu_count'] = get_vm_cpu_count()
    metadata['vm_mem_count'] = get_vm_mem_count()
    metadata['vm_desc'] = get_vm_desc()
    metadata['vm_mac'] = get_vm_mac()
    return metadata


def get_disks():
    cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME,
           '-pw', XE_PASSWORD, 'vm-disk-list', 'uuid=' + VM_UUID]
    output = subprocess.check_output(cmd, universal_newlines=True).strip()
    disks = []
    next_line = False
    for line in output.splitlines():
        if 'VDI' in line:
            next_line = True
            continue

        if 'uuid' in line and next_line:
            next_line = False
            uuid = line[line.find(':') + 1::].strip()
            disks.append(uuid)
    return disks


def export_disks(disks):
    for disk in disks:
        cmd = [XE_PATH, '-s', XE_SERVER, '-u', XE_USERNAME, '-pw', XE_PASSWORD, 'vdi-export',
               'uuid=' + disk, 'filename=' + disk + '.raw', 'format=raw', '--progress']
        subprocess.check_output(cmd, stderr=None)
        if os.path.isfile(disk + '.raw'):
            print("Exported " + disk)
        else:
            print("Could not export " + disk)


def get_vmid():
    cmd = ['pvesh', 'get', '/cluster/nextid']
    vmid = subprocess.check_output(cmd, universal_newlines=True).strip()
    return vmid


def create_proxmox_vm(metadata):
    vmid = get_vmid()
    vm_mem = int(metadata['vm_mem_count']) / 1024 / 1024
    cmd = ['qm', 'create', str(vmid), "--sockets", "1", "--cores", metadata["vm_cpu_count"], "--memory", str(vm_mem),
           "--name", metadata["vm_name"], "--description", metadata["vm_desc"], "--agent", "enabled=1,fstrim_cloned_disks=1",
           "--net0", "model=e1000,bridge=vmbr0,macaddr=" + metadata["vm_mac"], "--scsihw", "virtio-scsi-pci"]
    subprocess.check_output(cmd, stderr=None)
    return vmid


def import_disks(vmid, disks, storage):
    idx = 0
    for disk in disks:
        if os.path.isfile(disk + '.raw'):
            cmd = ['qm', 'importdisk', str(vmid), disk + '.raw', storage]
            subprocess.check_output(cmd, stderr=None)
            cmd = ['qm', 'set', '--scsi' +
                   str(idx), storage + ':vm-' + str(vmid) + '-disk-' + str(idx) + '.raw']
            subprocess.check_output(cmd, stderr=None)
            print("Imported " + disk + " to " + storage + " for " + vmid)
        else:
            print("Could not import " + disk)
        idx = idx + 1

print("Collecting disks...")
disks = get_disks()
print("Exporting disks...")
export_disks(disks)
print("Collecting metadata...")
metadata = collect_metadata()
print("Create PVE VM")
vmid = create_proxmox_vm(metadata)
print("Import disks for " + str(vmid))
import_disks(vmid, disks, PVE_STORAGE)

print("Finished!")
