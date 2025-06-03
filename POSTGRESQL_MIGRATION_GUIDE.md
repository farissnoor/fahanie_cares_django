# PostgreSQL Migration Guide

## Overview
This guide walks you through migrating from SQLite to PostgreSQL for your Django application.

## What I've Done
✅ Updated `config/settings/development.py` to support PostgreSQL
✅ Confirmed psycopg2-binary is in requirements.txt
✅ Verified .env.example has PostgreSQL configuration

## What You Need to Do

### 1. Install PostgreSQL
```bash
# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Windows
# Download installer from https://www.postgresql.org/download/windows/
```

### 2. Create Database and User
```bash
# Access PostgreSQL prompt
psql postgres

# Create database
CREATE DATABASE fahanie_cares_dev;

# Create user with password
CREATE USER your_db_user WITH PASSWORD 'your_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE fahanie_cares_dev TO your_db_user;

# Exit
\q
```

### 3. Configure Environment Variables
Create or update `.env` file in the Django project:
```bash
cd /Users/macbookpro/Documents/fahanie-cares/fahanie_cares_django
cp .env.example .env
```

Edit `.env` and update these values:
```
DB_NAME=fahanie_cares_dev
DB_USER=your_db_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Install Python Dependencies
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../requirements.txt
```

### 5. Migrate Data (if you have existing data)

#### Option A: Fresh Start (Recommended for development)
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (if available)
python create_sample_data.py
```

#### Option B: Migrate Existing Data
```bash
# Export data from SQLite
python manage.py dumpdata --exclude contenttypes --exclude auth.permission > datadump.json

# Switch to PostgreSQL (DB_NAME should be set in .env)
python manage.py migrate

# Load data into PostgreSQL
python manage.py loaddata datadump.json
```

### 6. Test the Connection
```bash
# Test database connection
python manage.py dbshell

# If successful, you'll see:
# psql (version)
# Type "help" for help.
# fahanie_cares_dev=>

# Exit with \q
```

## Working with Me (Claude) Using PostgreSQL

Once PostgreSQL is set up:

1. **I can read your .env file** to understand your database configuration
2. **I can generate and run migrations** for any model changes
3. **I can write database queries** using Django ORM
4. **I cannot directly access your PostgreSQL instance** - you need to run commands

### Common Commands I Might Ask You to Run:
```bash
# Check migrations
python manage.py showmigrations

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Database shell
python manage.py dbshell

# Django shell (for testing queries)
python manage.py shell_plus
```

## Troubleshooting

### Connection Refused
```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

### Authentication Failed
```bash
# Check pg_hba.conf settings
# Location varies by OS, common locations:
# macOS: /usr/local/var/postgres/pg_hba.conf
# Linux: /etc/postgresql/*/main/pg_hba.conf

# Ensure it has:
# local   all   all   md5
# host    all   all   127.0.0.1/32   md5
```

### psycopg2 Installation Issues
```bash
# If psycopg2-binary fails, try:
pip install psycopg2

# On macOS, may need:
brew install postgresql
export LDFLAGS="-L/usr/local/opt/postgresql/lib"
export CPPFLAGS="-I/usr/local/opt/postgresql/include"
pip install psycopg2
```

## Benefits of PostgreSQL over SQLite
- Better performance for concurrent users
- Full-text search capabilities
- JSON field support for Notion data caching
- Better data integrity and constraints
- Production-ready scaling

## Next Steps
1. Complete the PostgreSQL setup
2. Run migrations
3. Test the application
4. Let me know if you encounter any issues!