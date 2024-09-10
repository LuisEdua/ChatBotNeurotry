# src/services/Cloudinary/cloudinary_module.py

from .cloudinary_service import CloudinaryService

class CloudinaryModule:
    def __init__(self):
        self.cloudinary_service = CloudinaryService()
