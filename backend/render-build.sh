# Render.com Build & Start Commands

# Build Command (installation des dépendances)
pip install -r requirements.txt

# Start Command (lancement du serveur)
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
