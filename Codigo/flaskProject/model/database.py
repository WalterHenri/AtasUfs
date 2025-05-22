from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from datetime import datetime, timezone

db = SQLAlchemy()


def configure_database(app):
    user = 'postgres'
    password = '%3Ft1t4n%3F'  # Password "?t1t4n?" URL-encoded
    host = 'localhost'
    port = '5432'
    db_name = 'AtasUfs'

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'postgresql://{user}:{password}@{host}:{port}/{db_name}'
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()


@event.listens_for(db.Model, 'before_update', propagate=True)
def update_updated_at(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)