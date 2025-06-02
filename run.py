from app import create_app, db
from app.models import User
from flask_bcrypt import Bcrypt
import os

app = create_app()
bcrypt = Bcrypt(app)

def create_admin():
    with app.app_context():
        if not User.query.filter_by(username=os.getenv('ADMIN_USERNAME')).first():
            admin = User(
                username=os.getenv('ADMIN_USERNAME'),
                email='admin@casinoup.com',
                password_hash=bcrypt.generate_password_hash(os.getenv('ADMIN_PASSWORD')).decode('utf-8'),
                is_admin=True,
                balance=1000.0
            )
            db.session.add(admin)
            db.session.commit()

if __name__ == '__main__':
    create_admin()
    app.run(debug=True) 