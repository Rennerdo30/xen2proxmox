# xen2proxmox

## Installation
1. copy xe from XenServer to proxmox
2. install stunnel via `apt install stunnel`

## Usage 
```bash
python3 migrate.py <XenServer address> <username> <password> <uuid of vm to migrate> <pve target storage>
```


## Limitations
* only one mac adress is used
* only works with bios boot
* only one socket is used
* vmbr0 is the default network
* bootdrive is not set

### Special Thanks to [DeepBlueV7.X](https://github.com/deepbluev7) for finding the nessescary xe commands
