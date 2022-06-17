import subprocess
import os
import click
import paramiko
from dotenv import load_dotenv
from models import Server

load_dotenv()


def ssh_remote_command(hostname, username='root', cmd=''):
    key = paramiko.RSAKey.from_private_key_file('id_rsa.key')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, username=username, pkey=key)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

    while True:
        line = ssh_stdout.readline()
        if not line:
            break
        print("%s@%s: %s" % (hostname, username, line), end="")


def get_servers(is_all=False):
    if is_all:
        return Server.select().execute()
    else:
        return Server.select().where(Server.is_post_installed == 0).execute()


def print_stdout(process):
    while process.poll() is None:
        line = process.stdout.readline()
        if line != "":
            print(line, end="")


def run_command(cmd):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        encoding="utf-8",
        errors='replace'
    )
    print_stdout(p)


def create_ipset_rule_cmd(rule_name):
    return "sudo ipset create %s hash:ip" % rule_name


def export_ipset_rule_cmd(rule_name):
    return "sudo ipset save %s -f /etc/ipsets.conf" % rule_name


def restore_ipset_rule_cmd(rule_name):
    return "sudo ipset save %s -f /etc/ipsets.conf" % rule_name


def export_iptables_rule_cmd():
    return "sudo iptables-save | sudo tee /etc/iptables/rules.v4"


def get_ipset_rule():
    pass


def enable_ipset_service_cmd():
    return """
        sudo systemctl daemon-reload && 
        sudo systemctl start ipset-persistent && 
        sudo systemctl enable ipset-persistent
    """


def create_iptables_accept_rule_cmd(ipset_rule_name):
    return """
        sudo iptables -A INPUT -p tcp --dport 80 -m set --match-set {ipset_rule_name} src -j ACCEPT && 
            sudo iptables -A INPUT -p tcp --dport 443 -m set --match-set {ipset_rule_name} src -j ACCEPT 
        """.format(ipset_rule_name=ipset_rule_name)


def create_iptables_drop_rule_cmd():
    return """
        sudo iptables -A INPUT -p tcp -s 0/0 -d 0/0 --dport 80 -j DROP &&
        sudo iptables -A INPUT -p tcp -s 0/0 -d 0/0 --dport 443 -j DROP
    """


def create_ipset_persistent_service_cmd(rule_name):
    service = """ 
        [Unit]
        Description=Ipset persistence service
        DefaultDependencies=no
        Requires=netfilter-persistent.service
        Requires=ufw.service
        Before=network.target
        Before=netfilter-persistent.service
        Before=ufw.service
        ConditionFileNotEmpty=/etc/ipsets.conf
         
        [Service]
        Type=oneshot
        RemainAfterExit=yes
        ExecStart=/sbin/ipset restore -f -! /etc/ipsets.conf
         
        # save on service stop, system shutdown etc.
        ExecStop=/sbin/ipset save %s -f /etc/ipsets.conf
         
        [Install]
        WantedBy=multi-user.target
        RequiredBy=netfilter-persistent.service
        RequiredBy=ufw.service
    """ % rule_name
    service_conf_file_path = "/etc/systemd/system/ipset-persistent.service"
    return "echo '%s' | sudo tee -a %s > /dev/null" % (service, service_conf_file_path)


def basic_install_cmd():
    # first reset all ipset and iptables rules
    return """
         sudo apt update && 
         sudo apt -y install netfilter-persistent &&
         sudo apt -y install ipset &&
         sudo apt -y install iptables-persistent &&
         sudo ipset destroy && sudo iptables -F
    """


def post_install_remote():
    servers = get_servers()
    basic_cmds = basic_install_cmd()
    rule_name = os.getenv("IPSET_RULE_NAME")
    for server in servers:
        ssh_remote_command(server.host, 'root', basic_cmds)
        ssh_remote_command(server.host, 'root', create_ipset_rule_cmd(rule_name))
        ssh_remote_command(server.host, 'root', export_ipset_rule_cmd(rule_name))
        ssh_remote_command(server.host, 'root', export_iptables_rule_cmd())
        ssh_remote_command(server.host, 'root', create_iptables_accept_rule_cmd(rule_name))
        ssh_remote_command(server.host, 'root', create_iptables_drop_rule_cmd())
        ssh_remote_command(server.host, 'root', create_ipset_persistent_service_cmd(rule_name))
        ssh_remote_command(server.host, 'root', enable_ipset_service_cmd())
        Server.update({Server.is_post_installed: True}).where(Server.host == server.host).execute()


def post_install_local():
    rule_name = os.getenv("IPSET_RULE_NAME")
    run_command(basic_install_cmd())
    run_command(create_ipset_rule_cmd(rule_name))
    run_command(export_ipset_rule_cmd(rule_name))
    run_command(create_iptables_accept_rule_cmd(rule_name))
    run_command(create_iptables_drop_rule_cmd())
    run_command(export_iptables_rule_cmd())
    run_command(create_ipset_persistent_service_cmd(rule_name))
    run_command(enable_ipset_service_cmd())
