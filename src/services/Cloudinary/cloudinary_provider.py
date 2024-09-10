# src/services/Cloudinary/cloudinary_provider.py

import cloudinary
import cloudinary.uploader
import cloudinary.api

def get_cloudinary_config():
    """
    Configures the Cloudinary settings.
    """
    cloudinary.config(
        cloud_name='dlgusambk',
        api_key='943321515132595',
        api_secret='LKUIVvMVINoZgo-HHYZqCWt2ylQ'
    )
