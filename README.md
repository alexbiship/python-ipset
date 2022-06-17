
# Auto IPSet Rule Deployer

Deploy local server's ipset rules to other remote servers automatically.


## Pre-Installation

- Clone repository
```bash
$   git clone git@github.com:alexbiship/python-ipset.git
```
- Copy RSA(SSH) key for `root` user for remote access, change name to `id_rsa.key` and copy to the root path of the project directory
```bash
$ chmod 400 id_rsa.key
```
- All installation and running commands on remote servers are required `root` user permission. Allow `root` user login on remote servers if it's disabled. [See here for more info](https://www.knot35.com/how-to-permanently-enable-root-access-on-aws-ec2-instance/)  Login as `root` 
- Python v3.6+ is required and tested on Ubuntu 18.04

```bash
$   add-apt-repository ppa:deadsnakes/ppa
$   apt update
$   apt -y install python3
$   apt -y install python3-pip
$   pip3 install virtualenv
```
- Create virtual env and install dependencies
```bash
$   cd $YOUR_PROJECT_DIRECTORY
$   virtualenv .venv
$   source .venv/bin/activate
$   pip3 install -r requirements.txt
```
- Install iptables-persistent plugin(this can't be installed automatically via bash since it requires client interaction(yes/no prompt))
```bash
$   apt -y install iptables-persistent
```
 - Check all available CLI commands
 ```bash
$   python3 main.py
 ```


 ### Examples

 - Firstly, run `init` command and install and config basic settings automatically for local(or main) server that this script runs on.
 ```bash
    python3 main.py init
 ```
 - Register remote servers. host name can be public IP or domain name
 ```
 $  python3 main.py add-server
 ```
  - initialize remote servers(this will install all stuff like `ipsets`, ipset-persistence, etc on remote server side). You must run this command after registering new server otherwise it won't work as expected.
 ```
 $  python3 main.py init-remote
 ```
 - Add two cron jobs. One is for synching data between local and mysql db, other one is to deploy ipset rules to all remote servers
 ```bash
$ crontab -e

# setup cron job
* * * * * cd /path/to/the/project/folder && .venv/bin/python3 main.py sync
* * * * * cd /path/to/the/project/folder && .venv/bin/python3 main.py deploy
 ```