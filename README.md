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
* vmbr0 is the default network
* bootdrive is not set
