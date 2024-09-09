# cloudinary_service.py
import cloudinary.uploader
from io import BytesIO

class CloudinaryService:
    def __init__(self):
        # Configura Cloudinary
        import cloudinary_provider
        cloudinary_provider.get_cloudinary_config()

    def upload_image(self, image_stream: BytesIO) -> dict:
        """
        Subir una imagen usando un flujo de bytes (BytesIO en lugar de Readable).
        """
        try:
            response = cloudinary.uploader.upload_stream(
                image_stream,
                resource_type='auto'  # Determina el tipo de archivo automáticamente
            )
            return response
        except Exception as e:
            print(f"Error uploading image: {e}")
            return {'error': str(e)}
