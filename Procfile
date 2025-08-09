web: cd backend && python main.py
worker: cd backend && python -m celery worker --app=app.tasks:celery_app --loglevel=info