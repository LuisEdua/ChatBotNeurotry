# __init__.py
from .cloudinary import CloudinaryProvider, CloudinaryService

class CloudinaryModule:
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        self.cloudinary_provider = CloudinaryProvider(cloud_name, api_key, api_secret)
        self.cloudinary_service = CloudinaryService(self.cloudinary_provider)

    def get_provider(self):
        return self.cloudinary_provider

    def get_service(self):
        return self.cloudinary_service
