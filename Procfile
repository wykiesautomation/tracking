web: gunicorn wsgi:app --workers 2 --threads 4 --timeout 120
worker: python worker.py
notifications: python notification_worker.py
