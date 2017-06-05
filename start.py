from tournament import app
import db

db.migrate()

if __name__ == "__main__":
    app.run()
