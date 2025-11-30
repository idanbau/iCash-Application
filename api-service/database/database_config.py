import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    """Shared declarative base for all models."""
    pass


# Flask-SQLAlchemy instance configured to use our Base.
db = SQLAlchemy(model_class=Base)


SQLAlchemy_DATABASE = URL.create(
    drivername=os.getenv("DATABASE_DRIVER", "postgresql+psycopg"),
    username=os.environ["DATABASE_USERNAME"],
    password=os.environ["DATABASE_PASSWORD"],  # plain (unescaped) text
    host=os.environ["DATABASE_HOST"],
    database=os.environ["DATABASE_NAME"],
)

def init_app(app):
    """Bind SQLAlchemy to the Flask app with sane defaults."""
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLAlchemy_DATABASE
    db.init_app(app)
    return db


__all__ = ["db", "Base", "init_app", "SQLAlchemy_DATABASE"]
