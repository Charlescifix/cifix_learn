web: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
worker: cd backend && python -m celery worker --app=app.tasks:celery_app --loglevel=info