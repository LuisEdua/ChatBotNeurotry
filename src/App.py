from flask import Flask
from src.controllers.OpenAiController import openai_controller
from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(openai_controller, url_prefix='/openai')
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)