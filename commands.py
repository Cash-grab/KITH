import click
from flask.cli import with_appcontext

from app import db, User


@click.command("create-admin")
@click.argument("username")
@click.argument("password")
@with_appcontext
def create_admin(username, password):
    """Create a user with admin privileges via CLI."""
    existing = User.query.filter_by(username=username).first()
    if existing:
        click.echo(f"User {username} already exists.")
        raise click.Abort()

    user = User(username=username, role='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin user {username} created successfully.")


def init_app(flask_app):
    """Register CLI commands on the Flask app."""
    flask_app.cli.add_command(create_admin)
