import sqlite3
import os

dbs = ['aracannabis.db', 'instance/aracannabis.db', 'instance/database.db']

for db_path in dbs:
    if os.path.exists(db_path):
        print(f"Checking {db_path}...")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check users
            try:
                cursor.execute("SELECT id, nome, email FROM profissionais WHERE id=7")
                user = cursor.fetchone()
                if user:
                    print(f"  FOUND USER 7 in {db_path}: {user}")
                else:
                    print(f"  User 7 NOT found in {db_path}")
                    
                # Check max ID
                cursor.execute("SELECT MAX(id) FROM profissionais")
                max_id = cursor.fetchone()[0]
                print(f"  Max User ID: {max_id}")
            except Exception as e:
                print(f"  Error checking users: {e}")

            # Check patients
            try:
                cursor.execute("SELECT id, nome FROM pacientes WHERE id=1")
                patient = cursor.fetchone()
                if patient:
                    print(f"  FOUND PATIENT 1 in {db_path}: {patient}")
                else:
                    print(f"  Patient 1 NOT found in {db_path}")
            except Exception as e:
                print(f"  Error checking patients: {e}")
                
            conn.close()
        except Exception as e:
            print(f"Error connecting to {db_path}: {e}")
    else:
        print(f"{db_path} does not exist")
