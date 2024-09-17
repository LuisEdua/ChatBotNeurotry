from flask import Blueprint, request, jsonify
from pydantic import BaseModel
from typing import Any, Dict
#from src.services.OpenAi.OpenAi_service import OpenAiService
from src.services.gemini.gemini_service import GoogleAiService
from src.whatsapp.whatsapp_service import WhatsappService
from src.services.Cloudinary.cloudinary_service import CloudinaryService
from src.services.Encrytation.Encryptation import EncryptationService

whatsapp_controller = Blueprint('whatsapp_controller', __name__)


class WebhookMessageDto(BaseModel):
    entry: list


class WhatsappController:
    def __init__(self, model, cloudinary_service: CloudinaryService, encryptation_service: EncryptationService):
        self.whatsapp_service = WhatsappService(model, encryptation_service, cloudinary_service)

    async def handle_message(self):
        message_dto = request.get_json()
        try:

            message = message_dto["entry"][0]["changes"][0]["value"]["messages"][0]
            await self.whatsapp_service.handle_message(message)

            return jsonify({"status": "EVENT_RECEIVED"}), 200
        except KeyError:
            return jsonify({"status": "Bad Request"}), 400

    def verify(self):
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        return self.whatsapp_service.verify(verify_token, challenge)

    def handle_payment_success(self):
        query = request.args.to_dict()
        return self.whatsapp_service.handle_payment_success(query)

    def handle_payment_cancel(self):
        query = request.args.to_dict()
        return self.whatsapp_service.handle_payment_cancel(query)

    def handle_payment_webhook(self):
        return self.whatsapp_service.handle_payment_webhook(request, jsonify)

    def handle_flow_webhook(self):
        return self.whatsapp_service.handle_encrypted_message(request, jsonify)


# Initialize services
#openai_service = OpenAiService()
google_ai_service = GoogleAiService()
cloudinary_service = CloudinaryService()
encryptation_service = EncryptationService()

# Initialize controller
whatsapp_controller_instance = WhatsappController(google_ai_service, cloudinary_service, encryptation_service)

whatsapp_controller.add_url_rule('/whatsapp', 'handle_message', whatsapp_controller_instance.handle_message,
                                 methods=['POST'])
whatsapp_controller.add_url_rule('/whatsapp', 'verify', whatsapp_controller_instance.verify, methods=['GET'])
whatsapp_controller.add_url_rule('/whatsapp/payments/success', 'handle_payment_success',
                                 whatsapp_controller_instance.handle_payment_success, methods=['GET'])
whatsapp_controller.add_url_rule('/whatsapp/payments/cancel', 'handle_payment_cancel',
                                 whatsapp_controller_instance.handle_payment_cancel, methods=['GET'])
whatsapp_controller.add_url_rule('/whatsapp/payments/webhook', 'handle_payment_webhook',
                                 whatsapp_controller_instance.handle_payment_webhook, methods=['POST'])
whatsapp_controller.add_url_rule('/whatsapp/flows/webhook', 'handle_flow_webhook',
                                 whatsapp_controller_instance.handle_flow_webhook, methods=['POST'])
