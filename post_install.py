import subprocess
import os

import click
from dotenv import load_dotenv

load_dotenv()


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
         sudo ipset destroy && sudo iptables -F"
    """


def install_all():
    run_command(basic_install_cmd())
    rule_name = os.getenv("IPSET_RULE_NAME")
    if rule_name is None:
        rule_name = click.prompt(
            text="Enter IPSet rule name. Required.",
            type=click.types.STRING,
            default="whitelist"
        )
    run_command(create_ipset_rule_cmd(rule_name))
    run_command(export_ipset_rule_cmd(rule_name))
    run_command(export_iptables_rule_cmd())
    run_command(create_ipset_persistent_service_cmd(rule_name))
    run_command(enable_ipset_service_cmd())
