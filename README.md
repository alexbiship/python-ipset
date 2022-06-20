[![Codacy Badge](https://app.codacy.com/project/badge/Grade/8ee3bada9ae645f5a23f888ea4bfd1ce)](https://www.codacy.com/gh/alexbiship/python-ipset/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=alexbiship/python-ipset&amp;utm_campaign=Badge_Grade)
# Auto IPSet Rule Deployer
Deploy local server's ipset rules to other remote servers automatically.
## Pre-Installation
-   Clone repository
```bash
git clone git@github.com:alexbiship/python-ipset.git
```
-   Copy RSA(SSH) key for `root` user for remote access, change name to `id_rsa.key` and copy to the root path of the project directory
```bash
chmod 400 id_rsa.key
```
-   All installation and running commands on remote servers are required `root` user permission. Allow `root` user login on remote servers if it's disabled. [See here for more info](https://www.knot35.com/how-to-permanently-enable-root-access-on-aws-ec2-instance/)  Login as `root` Python v3.6+ is required and tested on Ubuntu 18.04
```bash
add-apt-repository ppa:deadsnakes/ppa
apt update
apt -y install python3
apt -y install python3-pip
pip3 install virtualenv
```
-   Create virtual env and install dependencies
```bash
cd $YOUR_PROJECT_DIRECTORY
virtualenv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

[//]: # (-   Install iptables-persistent plugin&#40;this can't be installed automatically via bash since it requires client interaction&#40;yes/no prompt&#41;&#41;)

[//]: # (```bash)

[//]: # (apt -y install iptables-persistent)

[//]: # (```)
-   Check all available CLI commands
 ```bash
python3 main.py
 ```
 ### Examples
-   Firstly, run `add-server` command and register servers.(you have to add local server that monitors MySQL database change. Use localhost or 127.0.0.1)
 ```bash
python3 main.py add-server
 ```
-   Run `init` command and install and config, basic settings automatically for all servers.
 ```bash
python3 main.py init
 ```
-   Run `reset-ipset` command to clean up local server's ipset rules(Not for other servers)
-   Run `reset-servers` command to clean up all ipsets and iptable rules in all servers(factory mode :)

-   Add two cron jobs. One is for syncing mysql db and set proper ipset, other one is to deploy ipset rules to all servers
 ```bash
crontab -e
# setup cron job
* * * * * cd /path/to/the/project/folder && .venv/bin/python3 main.py sync
* * * * * cd /path/to/the/project/folder && .venv/bin/python3 main.py deploy
 ```
