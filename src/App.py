# main.py
from src.services.Cloudinary.cloudinary_module import CloudinaryModule
from io import BytesIO


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