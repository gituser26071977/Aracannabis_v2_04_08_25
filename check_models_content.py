try:
    # Try to read the models.py file directly
    with open('models.py', 'r') as f:
        content = f.read()
        print("✅ Successfully read models.py")
        # Check if the ReminderSettings class is in the content
        if 'class ReminderSettings(db.Model):' in content:
            print("✅ ReminderSettings class found in models.py")
        else:
            print("❌ ReminderSettings class NOT found in models.py")
except Exception as e:
    print(f"❌ Error reading models.py: {e}")
