# Deployment Plan for Aracannabis Prontuário Application

## 1. Server Setup (Debian 12)

### System Updates and Essential Packages
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib nginx certbot python3-certbot-nginx git
```

### Create Application Directory
```bash
sudo mkdir -p /var/www/aracannabis
sudo chown -R $USER:$USER /var/www/aracannabis
```

## 2. Database Setup

### Configure PostgreSQL
```bash
sudo -u postgres psql -c "CREATE DATABASE aracannabis;"
sudo -u postgres psql -c "CREATE USER aracannabis_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE aracannabis TO aracannabis_user;"
```

## 3. Application Structure Reorganization

### Backend Structure
1. Create a proper directory structure:
```
/var/www/aracannabis/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── pacientes.py
│   │   ├── sintomas.py
│   │   ├── dosagens.py
│   │   └── evolucoes.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── contexts/
    │   ├── services/
    │   ├── App.js
    │   └── index.js
    ├── package.json
    └── .env
```

2. Create requirements.txt for backend dependencies:
```
Flask==2.0.3
Flask-JWT-Extended==4.7.1
Flask-CORS==5.0.1
Flask-SQLAlchemy==2.5.1
SQLAlchemy==2.0.38
python-dotenv==1.0.1
psycopg2-binary==2.9.10
Werkzeug==2.0.3
```

3. Create .env file for backend:
```
FLASK_ENV=production
FLASK_APP=app.py
DATABASE_URL=postgresql://aracannabis_user:secure_password@localhost:5432/aracannabis
JWT_SECRET_KEY=your_secure_jwt_secret_key
SECRET_KEY=your_secure_secret_key
```

### Frontend Structure
1. Create package.json for frontend dependencies:
```json
{
  "name": "aracannabis-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "@mui/material": "^5.15.0",
    "@mui/icons-material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "axios": "^1.6.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "react-scripts": "5.0.1"
  },
  "proxy": "http://localhost:5000"
}
```

2. Create .env file for frontend:
```
REACT_APP_API_URL=http://localhost:5000/api
```

## 4. Backend Deployment

### Setup Python Environment
```bash
cd /var/www/aracannabis/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Fix app.py to Match Directory Structure
Update app.py to correctly import routes from the routes directory.

### Initialize Database
```bash
source venv/bin/activate
python -c "from app import create_app; app = create_app(); from models import db; app.app_context().push(); db.create_all()"
```

### Create Systemd Service for Backend
Create a file at `/etc/systemd/system/aracannabis-backend.service`:
```
[Unit]
Description=Aracannabis Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aracannabis/backend
Environment="PATH=/var/www/aracannabis/backend/venv/bin"
ExecStart=/var/www/aracannabis/backend/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:create_app()

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable aracannabis-backend
sudo systemctl start aracannabis-backend
```

## 5. Frontend Deployment

### Build Frontend
```bash
cd /var/www/aracannabis/frontend
npm install
npm run build
```

## 6. Nginx Configuration

### Create Nginx Configuration
Create a file at `/etc/nginx/sites-available/aracannabis`:
```
server {
    listen 80;
    server_name your_domain.com;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /var/www/aracannabis/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/aracannabis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Setup SSL with Certbot
```bash
sudo certbot --nginx -d your_domain.com
```

## 7. Security Considerations

### Firewall Configuration
```bash
sudo apt install -y ufw
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### Database Backups
Set up a cron job for regular database backups:
```bash
sudo crontab -e
```
Add the following line to run a backup daily at 2 AM:
```
0 2 * * * pg_dump -U aracannabis_user aracannabis > /var/backups/aracannabis_$(date +\%Y\%m\%d).sql
```

## 8. Monitoring and Maintenance

### Install and Configure Monitoring Tools
```bash
sudo apt install -y prometheus node-exporter
```

### Regular Updates
Set up a cron job for regular system updates:
```bash
0 3 * * 0 apt update && apt upgrade -y
```

## 9. Testing

1. Test backend API endpoints
2. Test frontend functionality
3. Test database connections
4. Test SSL configuration
5. Test user authentication and authorization
