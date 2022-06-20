import subprocess
import os
import paramiko
from dotenv import load_dotenv
from models import Server

load_dotenv()
ipsets_config_path = '/etc/ipsets.conf'
iptables_config_path = '/etc/iptables/rules.v4'
rule_name = os.getenv("IPSET_RULE_NAME")
print("dddddddddddd", rule_name)
is_local = True


def ssh_remote_connect(hostname, username="root"):
    key = paramiko.RSAKey.from_private_key_file('id_rsa.key')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, username=username, pkey=key)
    global is_local
    is_local = False
    return ssh


def ssh_remote_command(con, cmd=''):
    ssh_stdin, ssh_stdout, ssh_stderr = con.exec_command(cmd)

    while True:
        line = ssh_stdout.readline()
        if not line:
            break
        print(line, end="")


def get_servers(is_all=False, is_active=False):
    if is_all:
        return Server.select().execute()
    elif is_active:
        return Server.select().where(Server.is_post_installed == 1).execute()
    else:
        return Server.select().where(Server.is_post_installed == 0).execute()


def print_stdout(process):
    stdout = ""
    while process.poll() is None:
        line = process.stdout.readline()
        if line != "":
            print(line, end="")
            stdout = stdout + line
    return stdout


def run_command(cmd):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        encoding="utf-8",
        errors='replace'
    )
    stdout = print_stdout(p)
    return stdout


def deploy_config():
    run_command(export_ipset_rule_cmd())
    run_command(export_iptables_rule_cmd())
    servers = get_servers(is_all=False, is_active=True)
    for server in servers:
        ssh = ssh_remote_connect(server.host, 'root')
        sftp = ssh.open_sftp()
        sftp.put(ipsets_config_path, ipsets_config_path)
        sftp.put(iptables_config_path, iptables_config_path)
        # restore from the file
        ssh_remote_command(ssh, restore_ipset_rule_cmd())
        ssh_remote_command(ssh, restore_iptables_rule_cmd())


def create_ipset_rule_cmd():
    return "sudo ipset create %s hash:ip" % rule_name


def export_ipset_rule_cmd():
    return "sudo ipset save %s -f /etc/ipsets.conf" % rule_name


def restore_ipset_rule_cmd():
    return "sudo ipset restore -! < /etc/ipsets.conf"


def restore_iptables_rule_cmd():
    return "sudo iptables-restore < /etc/iptables/rules.v4"


def export_iptables_rule_cmd():
    return "sudo iptables-save | sudo tee /etc/iptables/rules.v4"


def get_ipset_rule():
    pass


def enable_services_cmd():
    return """
        sudo systemctl daemon-reload && 
        sudo systemctl start ipset-persistent && 
        sudo systemctl start iptables-persistent && 
        sudo systemctl enable ipset-persistent &&
        sudo systemctl enable iptables-persistent
    """


def check_iptables_rule_exist_cmd(cmd):
    if is_local is False:
        return False
    stdout = run_command(cmd)
    if "Bad rule" in stdout:
        return False
    return True


def check_iptables_accept_rule_exist(port, protocol):
    return check_iptables_rule_exist_cmd("""
        sudo iptables -C INPUT -p {protocol} --dport {port} -m set --match-set {ipset_rule_name} src -j ACCEPT
        """.format(ipset_rule_name=rule_name, protocol=protocol, port=port))


def check_iptables_drop_rule_exist(port, protocol):
    return check_iptables_rule_exist_cmd("""
        sudo iptables -C INPUT -p {protocol} -s 0/0 -d 0/0 --dport {port} -j DROP
    """.format(port=port, protocol=protocol))


def create_iptables_accept_rule_cmd(port, protocol):
    if check_iptables_accept_rule_exist(port, protocol):
        return ""
    return """
        sudo iptables -A INPUT -p {protocol} --dport {port} -m set --match-set {ipset_rule_name} src -j ACCEPT 
        """.format(ipset_rule_name=rule_name, protocol=protocol, port=port)


def create_iptables_drop_rule_cmd(port, protocol):
    if check_iptables_drop_rule_exist(port, protocol):
        return ""
    return """
        sudo iptables -A INPUT -p {protocol} -s 0/0 -d 0/0 --dport {port} -j DROP
    """.format(protocol=protocol, port=port)


def create_ipset_persistent_service_cmd():
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
        ExecStop=/sbin/ipset save {rule_name} -f /etc/ipsets.conf
         
        [Install]
        WantedBy=multi-user.target
        RequiredBy=netfilter-persistent.service
        RequiredBy=ufw.service
    """.format(rule_name=rule_name)
    service_conf_file_path = "/etc/systemd/system/ipset-persistent.service"
    return "echo '%s' | sudo tee %s > /dev/null" % (service, service_conf_file_path)


def create_iptable_persistent_service_cmd():
    service = """
        [Unit]
        Description=Iptable persistence service
        DefaultDependencies=no
        Requires=netfilter-persistent.service
        Requires=ufw.service
        Before=network.target
        Before=netfilter-persistent.service
        Before=ufw.service
        ConditionFileNotEmpty=/etc/iptables/rules.v4

        [Service]
        Type=oneshot
        RemainAfterExit=yes
        ExecStart=/sbin/iptables-restore -f -! /etc/iptables/rules.v4
        ExecStop=/sbin/iptables-save -f /etc/iptables/rules.v4

        [Install]
        WantedBy=multi-user.target
        RequiredBy=netfilter-persistent.service
        RequiredBy=ufw.service
    """
    service_conf_file_path = "/etc/systemd/system/iptables-persistent.service"
    return "echo '%s' | sudo tee %s > /dev/null" % (service, service_conf_file_path)


def basic_install_cmd():
    # first reset all ipset and iptables rules
    return """
         sudo apt update && 
         sudo apt -y install netfilter-persistent &&
         sudo apt -y install ipset &&
         sudo ipset destroy && 
         sudo systemctl stop iptables-persistent &&
         sudo systemctl disable iptables-persistent &&  
         sudo rm "/etc/iptables/rules.v4" &&  
         sudo rm "/etc/systemd/system/iptables-persistent.service" && 
         sudo rm "/etc/ipsets.conf" &&  
         sudo rm "/etc/systemd/system/ipset-persistent.service" && 
         sudo systemctl stop ipset-persistent &&
         sudo systemctl disable ipset-persistent &&
         sudo systemctl daemon-reload && 
         sudo systemctl reset-failed && 
         sudo ipset -F && 
         sudo iptables -F
    """


def post_install_remote():
    servers = get_servers()
    basic_cmds = basic_install_cmd()
    for server in servers:
        ssh = ssh_remote_connect(server.host)
        ssh_remote_command(ssh, basic_cmds)
        ssh_remote_command(ssh, create_ipset_rule_cmd())
        ssh_remote_command(ssh, export_ipset_rule_cmd())
        ssh_remote_command(ssh, export_iptables_rule_cmd())
        ssh_remote_command(ssh, create_iptables_accept_rule_cmd(server.port, server.protocol))
        ssh_remote_command(ssh, create_iptables_drop_rule_cmd(server.port, server.protocol))
        ssh_remote_command(ssh, create_ipset_persistent_service_cmd())
        ssh_remote_command(ssh, create_iptable_persistent_service_cmd())
        ssh_remote_command(ssh, enable_services_cmd())
        Server.update({Server.is_post_installed: True}).where(Server.host == server.host).execute()


def post_install_local():
    run_command(basic_install_cmd())
    run_command(create_ipset_rule_cmd())
    run_command(export_ipset_rule_cmd())
    run_command(create_iptables_accept_rule_cmd())
    run_command(create_iptables_drop_rule_cmd())
    run_command(export_iptables_rule_cmd())
    run_command(create_ipset_persistent_service_cmd())
    run_command(enable_services_cmd())
