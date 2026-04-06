from waitress import serve

from app import app
from database import init_db


if __name__ == "__main__":
    init_db()
    print("servidor rodando... ")
    serve(app, host="0.0.0.0", port=5000)
