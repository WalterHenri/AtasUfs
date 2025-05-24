from flask_security.forms import RegisterForm, LoginForm
from wtforms import StringField
from wtforms.validators import DataRequired

class ExtendedRegisterForm(RegisterForm):
    """
    Custom registration form that includes 'nome' (name) and 'departamento'.
    """
    nome = StringField('Nome Completo', [DataRequired(message="Nome é obrigatório")])
    departamento = StringField('Departamento')

class ExtendedLoginForm(LoginForm):
    """
    Custom login form (can be extended if needed, but often default is fine).
    For now, it's the same as the default, but allows for future customization.
    """
    # email = StringField('Email', [DataRequired(message="Email é obrigatório")])
    # password = PasswordField('Senha', [DataRequired(message="Senha é obrigatória")])
    # submit = SubmitField("Login")
    pass

