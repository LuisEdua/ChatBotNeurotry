import os
import json
import stripe
from typing import List, Any
from src.services.db.connection import get_db_session
from src.services.Encrytation.Encryptation import EncryptationService
from src.services.Cloudinary.cloudinary_service import CloudinaryService
from src.whatsapp.constants.send_registration_messages_fetch import send_registration_fetch
from src.whatsapp.constants.send_message_fetch import send_message_fetch
from src.whatsapp.constants.send_catalog_fetch import send_catalog_fetch
from src.whatsapp.constants.gen_nex_screen import get_next_screen
from src.whatsapp.interfaces.interactive_message_interface import InteractiveMessage
from src.whatsapp.interfaces.register_response_interface import RegisterResponse
from src.whatsapp.dtos.message import MessageDto

# Configura la clave de API de Stripe
stripe.api_key = os.getenv('STRIPE_SECRET')

class WhatsappService:
    def __init__(self, model, encrypt_service: EncryptationService, cloudinary_service: CloudinaryService):
        self.model = model
        self.db_service = get_db_session()
        self.encrypt_service = encrypt_service
        self.cloudinary_service = cloudinary_service

    def verify(self, verify_token: str, challenge: str):
        if verify_token == os.getenv('SECRET_WPP_TOKEN') and challenge:
            return challenge
        else:
            raise ValueError("Invalid verify token")

    async def handle_message(self, message_dto: Any):
        if message_dto.type == "text":
            await self.handle_text_message(message_dto)
        elif message_dto.type == "interactive":
            await self.handle_interactive_message(message_dto)

    async def handle_interactive_message(self, message: InteractiveMessage):
        response_parsed = json.loads(message.interactive.nfm_reply.response_json)
        if "products" in response_parsed:
            print("products received")
            print(response_parsed)
        elif response_parsed.get("type") == "feedback":
            print("feedback received")
            print(response_parsed)
            client = await self.db_service.user.find_first(where={"phone": message.from_})
            response = await self.google_ai_service.generate_feedback_message(response_parsed["feedback_text"], client.name)
            await send_message_fetch(response, message.from_)
        else:
            payload = RegisterResponse(**json.loads(message.interactive.nfm_reply.response_json))
            exist = await self.db_service.user.find_unique(where={"email": payload.email})
            if exist:
                await send_message_fetch("Este correo ya ha sido registrado con anterioridad, intenta de nuevo 🙏", message.from_)
            else:
                try:
                    user = await self.db_service.user.create(data={"email": payload.email, "name": payload.name, "phone": message.from_, "password": payload.password})
                    await send_message_fetch(f"Gracias por registrarte {user.name}, ahora puedes comenzar a comprar productos con tu asistente Duna 🚀", message.from_)
                    await send_message_fetch("En que puedo ayudarte hoy? 🤔\n_____________________\nComprar un producto de nuestra tienda 🛍️\nVer todos mis pedidos 📦\n Ver información de mi cuenta 📊~", message.from_)
                except Exception as error:
                    await send_message_fetch("Ocurrió un error al registrar tu cuenta, intenta de nuevo 🙏", message.from_)

    async def handle_text_message(self, message: MessageDto):
        print({"message_received": message.text.body})
        client_service = await self.google_ai_service.evaluate_client_response(message.text.body.lower())
        if client_service.is_welcome:
            await self.is_welcome(message)
        elif client_service.want_to_buy and not client_service.catalog:
            await self.want_to_buy(message)
        elif client_service.is_giving_thanks:
            await self.is_thanks(message)
        elif client_service.is_account_information:
            await self.is_account_information(message)
        elif client_service.want_to_buy and client_service.catalog:
            products = await self.google_ai_service.evaluate_extracted_products(client_service.catalog)
            await self.handle_buy_product(message, products)
        else:
            await self.did_not_understand(message)

    async def handle_buy_product(self, message: MessageDto, products: List[dict]):
        line_items = [{"price_data": {"currency": "mxn", "product_data": {"name": product["name"]}, "unit_amount": round(product["price"] * 100)}, "quantity": product["quantity"]} for product in products]
        session = await stripe.checkout.sessions.create(
            payment_intent_data={"metadata": {"orderId": "12345", "phone": message.from_}},
            line_items=line_items,
            mode="payment",
            success_url="https://r945484c-3000.use2.devtunnels.ms/api/v1/whatsapp/payments/success",
            cancel_url="https://r945484c-3000.use2.devtunnels.ms/api/v1/whatsapp/payments/cancel"
        )
        await send_message_fetch("En seguida enviamos el link para que puedas completar tu compra 🛍️", message.from_)
        await send_message_fetch(session.url, message.from_, True)
        await send_message_fetch("Este link tiene una duración de 24 horas, si no completas tu compra en ese tiempo, deberás solicitar uno nuevo 🕒", message.from_)

    async def did_not_understand(self, message: MessageDto):
        await send_message_fetch("Lo siento, no entendí tu mensaje, ¿puedes repetirlo? 🙏", message.from_)

    async def want_to_buy(self, message: MessageDto):
        try:
            is_registered = await self.db_service.user.find_unique(where={"phone": message.from_})
            if not is_registered:
                await send_message_fetch("Hola, parece que no estás registrado en nuestra plataforma, ¿te gustaría registrarte?", message.from_)
                await self.send_registration_message(message.from_)
            else:
                await send_message_fetch("Enseguida te muestro los productos disponibles en nuestra tienda 🛍️", message.from_)
                products = await self.db_service.product.find_many()
                products_list = [{"id": product.id, "title": product.name, "description": f"${product.price}", "image": "[image_base64]"} for product in products]
                products_list_images = [{"id": product.id, "title": product.name, "description": f"${product.price}", "image": product.image} for product in products]
                await send_catalog_fetch(message.from_, {"products": products_list_images})
                flow_generated = await self.google_ai_service.generate_json_products_catalog(products_list, products_list_images)
        except Exception as error:
            await send_message_fetch("Ocurrió un error al intentar obtener los productos, intenta de nuevo 🙏", message.from_)

    async def is_welcome(self, message: MessageDto):
        user = await self.db_service.user.find_unique(where={"phone": message.from_})
        if user:
            await send_message_fetch(f"Hola de nuevo {user.name.split(' ')[0]} 🤗, ¿en qué puedo ayudarte hoy? 🤔\n\n1️⃣ Comprar un producto 🛍️\n 2️⃣ Ver mis pedidos 📦\n 3️⃣ Ver información de mi cuenta 📊", message.from_)
        else:
            await send_message_fetch("Hola, soy Duna, tu asistente virtual, ¿en qué puedo ayudarte hoy? 🤗", message.from_)

    async def is_thanks(self, message: MessageDto):
        user = await self.db_service.user.find_unique(where={"phone": message.from_})
        if user:
            await send_message_fetch(f"De nada, es un placer ayudarte {user.name.split(' ')[0]} 🤗", message.from_)
        else:
            await send_message_fetch("Gracias por tu mensaje, ¿te gustaría registrarte?", message.from_)
            await self.send_registration_message(message.from_)

    async def is_account_information(self, message: MessageDto):
        user = await self.db_service.user.find_unique(where={"phone": message.from_})
        if user:
            await send_message_fetch("En seguida te muestro la información de tu cuenta", message.from_)
            await send_message_fetch(f"Nombre: {user.name}\nCorreo: {user.email}\nTelefono: {user.phone}", message.from_)
        else:
            await send_message_fetch("Parece que no estás registrado en nuestra plataforma, ¿te gustaría registrarte?", message.from_)
            await self.send_registration_message(message.from_)

    async def send_registration_message(self, to: str):
        await send_registration_fetch(to)

    async def send_message(self, message: str, to: str, preview_url: bool = False):
        await send_message_fetch(to, message, preview_url)

    async def save_message(self, role: str, text: str, conversation_id: str):
        await self.db_service.message.create(data={"role": role, "text": text, "conversationId": conversation_id})

    async def handle_encrypted_message(self, req, res):
        if not os.getenv('FACEBOOK_PRIVATE_KEY'):
            raise ValueError('Private key is empty. Please check your env variable "PRIVATE_KEY".')
        if not self.is_request_signature_valid(req):
            return res.status(432).send('Invalid signature.')

        message = json.loads(req.body.decode('utf-8'))
        user = message.get("entry")[0].get("changes")[0].get("value")
        user = json.loads(user["message"])
        if user.get("type") == "text":
            message_dto = MessageDto(**user)
            await self.handle_message(message_dto)
        return res.status(200).send('OK')

    def is_request_signature_valid(self, req) -> bool:
        # Implementa la lógica para validar la firma aquí
        pass

    async def get_next_screen(self, phone_number: str, intent: str):
        response = await get_next_screen(phone_number, intent)
        return response
