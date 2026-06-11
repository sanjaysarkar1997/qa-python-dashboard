from app import app

# Expose the Flask server instance for WSGI deployment (Gunicorn / uWSGI)
server = app.server
