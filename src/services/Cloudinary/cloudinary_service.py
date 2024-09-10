# src/services/Cloudinary/cloudinary_service.py

from .cloudinary_provider import get_cloudinary_config
import cloudinary.uploader
from io import BytesIO


class CloudinaryService:
    def __init__(self):
        get_cloudinary_config()  # Configure Cloudinary

    def upload_image(self, image_stream: BytesIO) -> dict:
        """
        Upload an image using a BytesIO stream.

        :param image_stream: A BytesIO stream of the image to upload.
        :return: The result of the upload operation.
        """
        # Upload the image
        result = cloudinary.uploader.upload(image_stream, resource_type='auto')
        return result
