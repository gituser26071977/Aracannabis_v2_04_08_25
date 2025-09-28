from app_cors_livre import create_app
from models import db, ReminderSettings

app = create_app()
with app.app_context():
    # Check if ReminderSettings is a registered model
    is_registered = ReminderSettings in db.Model.registry._class_registry.values()
    print(f"ReminderSettings model is registered: {is_registered}")
    
    # Check if the table exists in metadata
    table_exists = db.metadata.tables.get('reminder_settings') is not None
    print(f"reminder_settings table exists in metadata: {table_exists}")
