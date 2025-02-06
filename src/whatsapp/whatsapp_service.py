import os
import json
import stripe
from typing import List, Any
from datetime import datetime, timedelta
from src.services.db.connection import Session as session, Message, Segmentations, UserProfile
from src.services.Encrytation.Encryptation import EncryptationService
from src.services.Cloudinary.cloudinary_service import CloudinaryService
from src.whatsapp.constants.send_registration_messages_fetch import send_registration_fetch
from src.whatsapp.constants.send_message_fetch import send_message_fetch
from src.whatsapp.constants.send_catalog_fetch import send_catalog_fetch
from src.whatsapp.constants.gen_nex_screen import get_next_screen
from src.whatsapp.interfaces.interactive_message_interface import InteractiveMessage
from src.whatsapp.interfaces.register_response_interface import RegisterResponse
from src.whatsapp.dtos.message import MessageDto
from src.services.db.connection import User, Product
from src.whatsapp.constants.send_login_fetch import send_login_fetch
from src.whatsapp.constants.send_data_admin import send_catalog_admin_fetch
import logging
import requests
import base64
import whisper
import subprocess

# Configura la clave de API de Stripe
stripe.api_key = os.getenv('STRIPE_SECRET')

# Configura el logging
logging.basicConfig(level=logging.INFO)


class WhatsappService:
    def __init__(self, model, encrypt_service: EncryptationService, cloudinary_service: CloudinaryService):
        self.model = model
        self.encrypt_service = encrypt_service
        self.cloudinary_service = cloudinary_service

    def verify(self, verify_token: str, challenge: str):
        logging.info(f"Verifying token: {verify_token}")
        if verify_token == os.getenv('SECRET_WPP_TOKEN') and challenge:
            logging.info("Token verified successfully.")
            return challenge
        else:
            logging.error("Invalid verify token.")
            raise ValueError("Invalid verify token")

    async def handle_message(self, message_dto: Any):
        type = message_dto.get("type", None)
        logging.info(f"Handling message of type: {type}")
        if type == "text":
            await self.handle_text_message(message_dto)
        elif type == "interactive":
            await self.handle_interactive_message(message_dto)
        elif type == "audio":
            text = await self.handle_audio_message(message_dto)
            message_dto["text"] = {"body": text}
            await self.handle_text_message(message_dto)
        else:
            logging.info("Message type not supported.")

    async def handle_interactive_message(self, message: InteractiveMessage):
        logging.info(f"Handling interactive message from: {message['from']}")
        response_parsed = json.loads(message["interactive"]["nfm_reply"]["response_json"])

        if "products" in response_parsed:
            await send_message_fetch("Los productos se han agregado, por favor verifique sus pedidos", message["from"])
        elif response_parsed.get("type") == "feedback":
            client = await session().user.find_first(where={"phone": message["from"]})
            response = await self.model.generate_feedback_message(response_parsed["feedback_text"], client.name)
            await send_message_fetch(response, message["from"])
        else:
            payload = RegisterResponse(**json.loads(message["interactive"]["nfm_reply"]["response_json"]))

            existing_user_by_phone = session().query(User).filter(User.phone == message["from"]).first()
            if existing_user_by_phone:
                await send_message_fetch(
                    "Ya estás registrado en nuestra plataforma. Puedes comenzar a explorar productos. 🚀",
                    message["from"])
                return

            existing_user_by_email = session().query(User).filter(User.email == payload.email).first()
            if existing_user_by_email:
                await send_message_fetch(
                    "El correo proporcionado ya está registrado. Intenta con otro correo o inicia sesión.",
                    message["from"])
                return

            try:
                user_count = session().query(User).count()
                if user_count == 0:
                    await send_message_fetch("No hay registros en el sistema. Por favor, inténtalo más tarde.",
                                             message["from"])
                    return

                encrypted_password = self.encrypt_service.encrypt_password(payload.password)
                user = User(
                    name=payload.name,
                    email=payload.email,
                    phone=message["from"],
                    password=encrypted_password,
                    admin=False
                )
                session().add(user)
                session().commit()
                await send_message_fetch(
                    f"Gracias por registrarte {user.name}. Ahora puedes comenzar a comprar productos con tu asistente Duna 🚀",
                    message["from"])
                await send_message_fetch("¿En qué puedo ayudarte hoy? 🤔", message["from"])
            except Exception as error:
                logging.error(f"Error registering user: {error}")
                await send_message_fetch("Ocurrió un error al registrar tu cuenta. Por favor, intenta de nuevo. 🙏",
                                         message["from"])

    async def handle_text_message(self, message: MessageDto):
        try:
            if self.validate_message(message):
                client_service = await self.model.evaluate_client_response(message["text"]["body"].lower())
                if not client_service['error']:
                    print(client_service)
                    await self.save_message(message["text"]["body"], message["id"], message["from"],
                                            client_service["segmentations"], client_service["userProfileData"])
                    if client_service['isAttack']:
                        await self.send_message("Lo siento, no puedo responder a ese tipo de mensajes.", message["from"])
                    elif client_service['isWantToSeeProducts']:
                        user = session().query(User).filter(User.phone == message['from']).first()
                        if user.admin:
                            await self.want_to_see_products(message)
                        else:
                            await self.send_message("No tienes permisos para ver esta información.", message["from"])
                    elif client_service['isSummary']:
                        await self.generate_summary(message)
                    elif client_service['isRegister']:
                        await self.send_message("Por favor, proporciona tus credenciales para registrarte.", message["from"])
                        await self.send_registration_message(message["from"])
                    elif client_service['isLogin']:
                        await self.handle_login(message)
                    elif client_service['wantToRecommend']:
                        await self.recommentdation(message)
                    elif client_service['isWelcome']:
                        await self.is_welcome(message)
                    elif client_service['wantToBuy'] and not client_service['catalog']:
                        await self.want_to_buy(message)
                    elif client_service['isGivingThanks']:
                        await self.is_thanks(message)
                    elif client_service['isAccountInformation']:
                        user = session().query(User).filter(User.phone == message['from']).first()
                        if user.admin:
                            await self.send_seller_information(message)
                        else:
                            await self.is_account_information(message)
                    elif client_service['wantToBuy'] and client_service['catalog']:
                        products = await self.model.evaluate_extracted_products(client_service["catalog"])
                        await self.handle_buy_product(message, products)
                    else:
                        await self.did_not_understand(message)
        except Exception as error:
            print(error)

    async def handle_login(self, message: MessageDto):
        logging.info(f"User {message['from']} is attempting to log in.")
        # Here you can add the logic for handling user login, e.g., verifying credentials.
        await send_login_fetch(message["from"])
        await send_message_fetch("Por favor, proporciona tus credenciales para iniciar sesión.", message["from"])

    async def handle_buy_product(self, message: MessageDto, products: List[dict]):
        logging.info(f"Handling product purchase for user: {message['from']}")
        line_items = [{"price_data": {"currency": "mxn", "product_data": {"name": product["name"]}, "unit_amount": round(product["price"] * 100)}, "quantity": product["quantity"]} for product in products]
        session = await stripe.checkout.sessions.create(
            payment_intent_data={"metadata": {"orderId": "12345", "phone": message["from"]}},
            line_items=line_items,
            mode="payment",
            success_url="https://r945484c-3000.use2.devtunnels.ms/api/v1/whatsapp/payments/success",
            cancel_url="https://r945484c-3000.use2.devtunnels.ms/api/v1/whatsapp/payments/cancel"
        )
        await send_message_fetch("En seguida enviamos el link para que puedas completar tu compra 🛍️", message["from"])
        await send_message_fetch(session.url, message["from"], True)
        logging.info("Purchase session created successfully.")
        await send_message_fetch("Este link tiene una duración de 24 horas, si no completas tu compra en ese tiempo, deberás solicitar uno nuevo 🕒", message["from"])

    async def did_not_understand(self, message: MessageDto):
        logging.info(f"Message not understood from: {message['from']}")
        response = await self.model.message_not_understood(message["text"]["body"])
        await send_message_fetch(response, message["from"])

    async def save_message(self, message: str, message_id: str, number: str, segs, user_profile):
        session_instance = session()
        if not session_instance.query(Message).filter(Message.whatsapp_id == message_id).first():
            new_message = Message(whatsapp_id=message_id, text=message, number=number)
            session_instance.add(new_message)
            session_instance.commit()
            if segs:
                for seg in segs:
                    session_instance.add(Segmentations(phone=number, title=seg["title"], data=seg["data"]))
                session_instance.commit()
            if user_profile:
                for profile in user_profile:
                    session_instance.add(UserProfile(phone=number, title=profile["title"], data=profile["data"]))
                session_instance.commit()

    async def want_to_buy(self, message: MessageDto):
        try:
            user = session().query(User).filter(User.phone == message["from"]).first()
            if not user:
                await send_message_fetch(
                    "Hola, parece que no estás registrado en nuestra plataforma. ¿Te gustaría registrarte?",
                    message["from"])
                await self.send_registration_message(message["from"])
            else:
                await send_message_fetch("Enseguida te muestro los productos disponibles en nuestra tienda 🛍️",
                                         message["from"])
                products = await self.find_items()
                if not products:
                    await send_message_fetch("Actualmente no hay productos disponibles. Vuelve a intentarlo más tarde.",
                                             message["from"])
                    return

                products_list = []
                for product_id in products:
                    product_data = await self.get_product_data(product_id)
                    if not product_data:
                        continue

                    product_description = await self.get_product_description(product_id)
                    product_image = await self.get_image(product_data.get("pictures", [{}])[0].get("url", ""))
                    products_list.append({
                        "id": product_data.get("id"),
                        "title": product_data.get("title"),
                        "description": product_description or "Sin descripción",
                        "image": product_image
                    })

                if products_list:
                    await send_catalog_fetch(message["from"], {"products": products_list})
                else:
                    await send_message_fetch("No encontramos productos disponibles para mostrar. Intenta más tarde.",
                                             message["from"])
        except Exception as error:
            await send_message_fetch(
                "Ocurrió un error al intentar obtener los productos. Por favor, intenta de nuevo más tarde.",
                message["from"])

    async def is_welcome(self, message: MessageDto):
        user = session().query(User).filter(User.phone == message["from"]).first()
        if user:
            await send_message_fetch(f"Hola {user.name.split(' ')[0]} 🤗, bienvenido a tu tienda, ¿en qué puedo ayudarte hoy? 🤔", message["from"])
        else:
            await send_message_fetch("Hola, soy Duna, tu asistente virtual, ¿en qué puedo ayudarte hoy? 🤗", message["from"])

    async def is_thanks(self, message: MessageDto):
        user = session().query(User).filter(User.phone == message["from"]).first()
        if user:
            await send_message_fetch(f"De nada, es un placer ayudarte {user.name.split(' ')[0]} 🤗", message["from"])
        else:
            await send_message_fetch("Gracias por tu mensaje, ¿te gustaría registrarte?", message["from"])
            await self.send_registration_message(message["from"])

    async def is_account_information(self, message: MessageDto):
        user = session().query(User).filter(User.phone == message["from"]).first()
        if user:
            await send_message_fetch("En seguida te muestro la información de tu cuenta", message["from"])
            await send_message_fetch(f"Nombre: {user.name}\nCorreo: {user.email}\nTeléfono: {user.phone}", message["from"])
        else:
            await send_message_fetch("No estás registrado en nuestra plataforma, ¿te gustaría registrarte?", message["from"])
            await self.send_registration_message(message["from"])

    async def send_registration_message(self, phone_number: str):
        await send_registration_fetch(phone_number)

    async def send_registration_message(self, to: str):
        await send_registration_fetch(to)

    async def send_message(self, message: str, to: str, preview_url: bool = False):
        await send_message_fetch(message, to, preview_url)

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


    async def generate_summary(self, message):
        last_24_hours = datetime.now() - timedelta(hours=48)
        new_session = session()
        messages = new_session.query(Message).filter(
            Message.number == message["from"],
            Message.create_at >= last_24_hours
        ).all()
        data = [m.text for m in messages]
        sumary = await self.model.generate_sumary(data)
        await send_message_fetch(sumary, message["from"])

    async def recommentdation(self, message):
        new_session = session()
        products = new_session.query(Product).all()
        products_to_recomment = [{"id": p["id"], "name": p["name"]} for p in products]
        profile_data = new_session.query(UserProfile).filter(UserProfile.phone == message["from"]).all()
        data = [d.data for d in profile_data]
        recomendation = self.model.generate_recomendation(products_to_recomment, data)
        products_list_images = [
            {"id": product.id, "title": product.name, "description": f"${product.price}", "image": product.image} for
            product in products if product.id in recomendation]
        if products_list_images:
            await send_catalog_fetch(message["from"], {"products": products_list_images})
        else:
            response = await self.model.personalize_message("No hay productos para recomendarte")
            await send_message_fetch(response, message["from"])

    def validate_message(self, message):
        new_session = session()
        if not new_session.query(Message).filter(Message.whatsapp_id == message["id"]).first():
            return True
        return False

    async def want_to_see_products(self, message):
        await send_message_fetch("Enseguida te muestro tus publicaciones de Mercado Libre 🛍️", message["from"])
        products = await self.find_items()
        products_list = []
        for product in products:
            product_data = await self.get_product_data(product)
            product_description = await self.get_product_description(product)
            product_image = await self.get_image(product_data.get("pictures")[0].get("url"))
            product_obj = {"id": product_data.get("id"), "title": product_data.get("title"), "description": product_description, "image": product_image}
            products_list.append(product_obj)
        await send_catalog_admin_fetch(message["from"], {"products": products_list})

    async def find_items(self):
        url = "https://api.mercadolibre.com/users/712867753/items/search"

        payload = ""
        headers = {
            'Authorization': f"Bearer {os.getenv('MELI_TOKEN')}"
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json().get("results")
        else:
            return []

    async def get_product_data(self, product):
        url = f"https://api.mercadolibre.com/items/{product}"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {}

    async def get_product_description(self, product):
        url = f"https://api.mercadolibre.com/items/{product}/description"

        payload = {}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code == 200:
            return response.json().get("plain_text")
        else:
            return ""

    async def get_image(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
            else:
                return ""
        except Exception as error:
            return url

    async def send_seller_information(self, message):
        information = self.get_seller_information()
        response = await self.model.generate_seller_information(information, message["text"]["body"])
        await send_message_fetch(response, message["from"])

    def get_seller_information(self):
        url = "https://api.mercadolibre.com/users/me"

        payload = ""
        headers = {
            'Authorization': f"Bearer {os.getenv('MELI_TOKEN')}"
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"data": "No se pudo obtener la información del vendedor"}

    async def handle_audio_message(self, message_dto):
        audio_id = message_dto.get("audio").get("id")
        token = os.getenv('FACEBOOK_API_TOKEN')
        url = f"https://graph.facebook.com/v15.0/{audio_id}"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)
        url = response.json().get("url")
        audio = requests.get(url, headers=headers)
        with open("audio.mp3", "wb") as file:
            file.write(audio.content)
        model = whisper.load_model("base")
        result = model.transcribe("audio.mp3", language="es")
        print(result)
        return result.get("text")
