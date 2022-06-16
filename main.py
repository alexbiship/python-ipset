import click

from post_install import install_all
from utils import init_db, get_remote_db_data, sync_remote_and_local_db
from models import db


@click.group()
def cli():
    pass


@click.command()
def init():
    # Create SQLite DB
    init_db(db)
    # Post-Install
    install_all()


@click.command(help="Sync remote database and local db(sqlite) and update ipset rule(local server only)")
def sync():
    sync_remote_and_local_db()


@click.command()
@click.argument("key")
def set_security_key(key):
    print(key)
    click.echo("Generating a security key")


cli.add_command(init)
cli.add_command(sync)
cli.add_command(set_security_key)

if __name__ == "__main__":
    cli()
