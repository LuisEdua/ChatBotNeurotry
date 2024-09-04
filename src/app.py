from flask import Flask
from src.controllers.GeminiController import gemini_controller
from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(gemini_controller, url_prefix='/gemini')
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)
