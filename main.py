import click

from post_install import post_install_local, post_install_remote, deploy_config
from utils import init_db, sync_remote_and_local_db, insert_server_detail
from models import db


@click.group()
def cli():
    # Create SQLite DB
    init_db(db)


@click.command()
def init():
    # Post-Install
    post_install_local()


@click.command(help="Initialize remote servers. Use this right after new server is added.")
def init_remote():
    post_install_remote()


@click.command(help="Sync remote database and local db(sqlite) and update ipset rule(local server only)")
def sync():
    sync_remote_and_local_db()


@click.command(help="Deploy local server's up-to-dated ipset rule to other servers.")
def deploy():
    deploy_config()


@click.command(help="Add other servers to manage remotely")
@click.pass_context
def add_server(ctx):
    host = click.prompt(text="Publicly accessible host or IP address", type=click.types.STRING)
    name = click.prompt(text="Server name", type=click.types.STRING)
    insert_server_detail(host, name)
    if click.confirm("Do you want to continue?"):
        ctx.invoke(add_server)


@click.command()
@click.argument("key")
def set_security_key(key):
    print(key)
    click.echo("Generating a security key")


cli.add_command(init)
cli.add_command(sync)
cli.add_command(set_security_key)
cli.add_command(add_server)
cli.add_command(init_remote)
cli.add_command(deploy)

if __name__ == "__main__":
    cli()
