# Codigo/flaskProject/app.py
from flask import Flask, redirect, url_for, render_template, flash, request  # Added request
from model.database import configure_database, db
from routes.ata_routes import ata_bp
from routes.chat_routes import chat_bp
# Import admin_routes later
from service import AtaService, ChatService
from dotenv import load_dotenv
import os
import uuid  # For fs_uniquifier

from flask_security import Security, SQLAlchemyUserDatastore, current_user, auth_required, roles_required
from flask_security.utils import hash_password, url_for_security
from model.entities.user import User, Role
from forms import ExtendedRegisterForm, ExtendedLoginForm

from flask_wtf.csrf import CSRFProtect  # Import CSRFProtect

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "default-flask-secret-key-change-me")
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", "default-salt-change-me")
app.config['UPLOAD_FOLDER'] = './uploads'

# Flask-Security-Too Configuration
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False  # Set to True if you configure email
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'security/login_user.html'
app.config['SECURITY_REGISTER_USER_TEMPLATE'] = 'security/register_user.html'
app.config['SECURITY_MSG_LOGIN'] = ("Por favor, faça login para acessar.", "info")
app.config['SECURITY_UNAUTHORIZED_VIEW'] = None  # Redirects to login by default

# Password Hashing Configuration - Prioritize argon2, fallback to bcrypt
# Ensure argon2-cffi is installed (added to requirements.txt)
# bcrypt is also a good option and often easier to install across platforms.
app.config['SECURITY_PASSWORD_HASH'] = 'argon2'  # Preferred
app.config['SECURITY_PASSWORD_SCHEMES'] = ['argon2', 'bcrypt']  # Available schemes
app.config['SECURITY_DEPRECATED_PASSWORD_SCHEMES'] = ['bcrypt']  # Allow login with older bcrypt hashes if you migrate

# CSRF Protection (Flask-WTF)
# Initialize CSRFProtect *before* Flask-Security
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Required when using SECURITY_CSRF_PROTECT_MECHANISMS
csrf = CSRFProtect(app)  # Initialize CSRFProtect

# Flask-Security CSRF settings (relies on Flask-WTF's CSRFProtect being initialized)
app.config['SECURITY_CSRF_PROTECT_MECHANISMS'] = ["session", "basic"]
app.config['SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS'] = True

# Ensure API keys are loaded
openai_api_key = os.getenv("OPENAI_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

if not openai_api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables.")
if not google_api_key:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")

configure_database(app)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore,
                    register_form=ExtendedRegisterForm,
                    login_form=ExtendedLoginForm)

# Pass API keys or let services pick them up from env
ata_service = AtaService()  # Global instance
chat_service_instance = ChatService(ata_service)  # Global instance

# Make chat_service_instance available in app context if needed by routes directly
app.chat_service = chat_service_instance
app.ata_service = ata_service

# --- Admin Routes ---
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users', methods=['GET'])
@auth_required()
@roles_required('admin')
def manage_users():
    users = User.query.all()
    return render_template('security/manage_users.html', users=users)


@admin_bp.route('/users/toggle_admin/<int:user_id>', methods=['POST'])
@auth_required()
@roles_required('admin')
def toggle_admin_role(user_id):
    # Use find_user instead of get_user
    user_to_modify = user_datastore.find_user(id=user_id)
    if not user_to_modify:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.manage_users'))

    if user_to_modify.id == current_user.id and 'admin' in [role.name for role in user_to_modify.roles]:
        flash('Você não pode remover seu próprio privilégio de administrador.', 'warning')
        return redirect(url_for('admin.manage_users'))

    admin_role = user_datastore.find_or_create_role(name='admin', description='Administrador do Sistema')
    action = request.form.get('action')

    if action == 'add':
        user_datastore.add_role_to_user(user_to_modify, admin_role)
        flash(f'{user_to_modify.email} agora é um administrador.', 'success')
    elif action == 'remove':
        user_datastore.remove_role_from_user(user_to_modify, admin_role)
        flash(f'Privilégios de administrador removidos de {user_to_modify.email}.', 'success')
    else:
        flash('Ação inválida.', 'danger')

    db.session.commit()
    return redirect(url_for('admin.manage_users'))


app.register_blueprint(admin_bp)
# --- End Admin Routes ---


app.register_blueprint(ata_bp)
app.register_blueprint(chat_bp)


@app.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for_security('login'))
    return redirect(url_for('chat.new_chat'))


# One-time setup for roles and admin user (run once)
@app.before_request
def create_initial_roles_and_admin_once():
    # This function will run before every request, but the logic inside
    # ensures it only really acts once due to the checks.
    # For a cleaner approach, consider a CLI command for setup.
    if not app.config.get('_INITIAL_SETUP_DONE'):
        with app.app_context():  # Ensure we are in an app context
            db.create_all()  # Ensure all tables are created

            admin_role_name = 'admin'
            user_role_name = 'user'

            admin_role = user_datastore.find_or_create_role(name=admin_role_name,
                                                            description='Administrador do Sistema')
            user_role = user_datastore.find_or_create_role(name=user_role_name, description='Usuário Padrão')

            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            # Use find_user instead of get_user
            if not user_datastore.find_user(email=admin_email):
                admin_password = os.environ.get('ADMIN_PASSWORD', 'password')
                admin_nome = os.environ.get('ADMIN_NOME', 'Admin User')

                print(f"Creating initial admin user: {admin_email}")
                user_datastore.create_user(
                    email=admin_email,
                    password=hash_password(admin_password),  # This will use the configured schemes
                    nome=admin_nome,
                    roles=[admin_role, user_role],
                    active=True,
                    fs_uniquifier=str(uuid.uuid4())
                )
            db.session.commit()
            app.config['_INITIAL_SETUP_DONE'] = True
            print("Initial setup for roles and admin user complete (if needed).")


# Assign default role to new users upon registration
from flask_security.signals import user_registered


@user_registered.connect_via(app)
def on_user_registered(sender, user, **extra):
    default_role = user_datastore.find_role('user')
    if default_role and default_role not in user.roles:  # Check if role already assigned
        user_datastore.add_role_to_user(user, default_role)
    if not user.fs_uniquifier:
        user.fs_uniquifier = str(uuid.uuid4())
    db.session.commit()


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('./vector_store/atas', exist_ok=True)
    app.run(debug=True, port=5000)

