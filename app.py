from flask import Flask
from src.whatsapp.whatsapp_controller import whatsapp_controller
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.register_blueprint(whatsapp_controller, url_prefix='/api/v1')


if __name__ == "__main__":
    app.run(debug=True)