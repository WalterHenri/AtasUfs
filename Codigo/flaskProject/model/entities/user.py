# model/entities/user.py
from ..database import db
from flask_security import UserMixin, RoleMixin
from sqlalchemy.dialects.postgresql import UUID  # Keep if used elsewhere
import uuid  # For fs_uniquifier default

# Link table for many-to-many relationship between Users and Roles
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
                       )


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role {self.name}>"


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Will be hashed by Flask-Security
    departamento = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean(), default=True)  # Users are active by default
    # fs_uniquifier is critical for Flask-Security-Too for security tokens
    # It must be unique and non-nullable.
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
                           onupdate=db.func.current_timestamp())

    # Relationships
    # 'roles' relationship defined by Flask-Security's SQLAlchemyUserDatastore
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    interacoes = db.relationship('ChatPrompt', backref='usuario', lazy=True, foreign_keys='ChatPrompt.user_id')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.fs_uniquifier:  # Ensure fs_uniquifier is set on creation
            self.fs_uniquifier = str(uuid.uuid4())

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "departamento": self.departamento,
            "active": self.active,
            "roles": [role.name for role in self.roles],
            "fs_uniquifier": self.fs_uniquifier,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def __repr__(self):
        return f"<User {self.email} (ID: {self.id})>"

