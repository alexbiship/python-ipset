import subprocess


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


def commands():
    # first reset all ipset and iptables rules
    return [
        "sudo apt update",
        "sudo apt -y install ipset",
        "sudo apt -y install iptables-persistent",
        "sudo ipset destroy",
        "sudo iptables -F"
    ]


def install_all():
    cmds = commands()
    for cmd in cmds:
        # index 0 = command, 1 = arg
        run_command(cmd)
