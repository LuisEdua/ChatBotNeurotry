from flask import Flask
from src.controllers.OpenAiController import openai_controller
from src.controllers.GeminiController import gemini_controller
from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(gemini_controller, url_prefix='/gemini')
app.register_blueprint(openai_controller, url_prefix='/openai')

CORS(app)

def main():
    cloudinary_module = CloudinaryModule()

    # Example usage: upload an image
    try:
        with open('/Users/keyel/Documents/ChatBotNeurotry/src/phone.png', 'rb') as image_file:  # Replace with your image file name
            image_stream = BytesIO(image_file.read())
            result = cloudinary_module.cloudinary_service.upload_image(image_stream)
            print(result)
    except FileNotFoundError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()