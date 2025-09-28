try:
    from models import ReminderSettings
    print("✅ ReminderSettings imported successfully!")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
