from app_cors_livre import create_app
from flask_migrate import Migrate
from models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    import sys
    from flask_migrate import upgrade, init, migrate as _migrate
    
    with app.app_context():
        if len(sys.argv) > 1:
            if sys.argv[1] == 'init':
                init(directory='migrations')
            elif sys.argv[1] == 'migrate':
                _migrate(directory='migrations', message='Add reminder_settings table')
            elif sys.argv[1] == 'upgrade':
                upgrade(directory='migrations')
        else:
            print("Usage: python init_migrations.py [init|migrate|upgrade]")
