import json
import google.generativeai as genai
from typing import List, Any, Dict, Union
from sqlalchemy import Column, String, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
import os
from src.services.db.connection import Session as session

Base = declarative_base()

class MessageEvaluated(Base):
    __tablename__ = 'message_evaluated'
    id = Column(Integer, primary_key=True)
    is_welcome = Column(Boolean)
    want_to_buy = Column(Boolean)
    is_giving_thanks = Column(Boolean)
    is_account_information = Column(Boolean)
    is_orders = Column(Boolean)
    catalog = Column(String)

class Product(Base):
    __tablename__ = 'product'
    id = Column(String, primary_key=True)
    name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)

class GoogleAiService:
    def __init__(self):
        super().__init__()
        genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.db_session = session()

    async def on_module_init(self):
        await self.connect()

    async def generate_text(self, history: List[Dict[str, Any]], model: str = "gemini-pro") -> str:
        chat = self.model.start_chat(history=history, generation_config={"max_output_tokens": 100})
        last_message = history[-1]['parts'][0]['text']
        result = await chat.send_message(last_message)
        return result

    async def evaluate_client_response(self, message_to_evaluate: str) -> MessageEvaluated:
        prompt = f"""Voy a darte un mensaje de un cliente y quiero que me devuelvas **únicamente** un objeto JSON que indique lo que el cliente quiere. Evalúa el mensaje según los siguientes parámetros:
        - Si el cliente está saludando o es alguien nuevo: {{ isWelcome: true }}
        - Si el cliente quiere comprar algo o ver el catalogo de productos: {{ wantToBuy: true }}
        - Si el cliente quiere comprar y selecciona uno o mas productos: {{ wantToBuy: true, catalog: [{{name: "product_name", quantity: 1, price: 1}}] }}
        - Si el cliente está agradeciendo o dando las gracias: {{ isGivingThanks: true }}
        - Si el cliente quiere información de su cuenta: {{ isAccountInformation: true }}
        - Si el cliente quiere ver sus pedidos: {{ isOrders: true }}
        El JSON debe seguir este formato exacto:
        {{
        "isWelcome": false,
        "wantToBuy": false,
        "isGivingThanks": false,
        "isAccountInformation": false,
        "isOrders": false,
        "catalog": null
        }}
        IMPORTANTE: Quiero que únicamente me devuelvas el objeto JSON sin ningún texto adicional. 
        Aquí está el mensaje que quiero que analices: "{message_to_evaluate}" """
        try:
            text = self.model.generate_content(prompt).text
            return json.loads(text)
        except Exception as error:
            print(error)
            return MessageEvaluated(is_welcome=False, want_to_buy=False, is_giving_thanks=False, is_account_information=False, is_orders=False, catalog=None)

    def convert_to_json(self, text: str) -> MessageEvaluated:
        cleaned_text = text.replace('```json', '').replace('```', '').strip()
        return MessageEvaluated.parse_raw(cleaned_text)

    def convert_products_to_json(self, text: str) -> List[Product]:
        cleaned_text = text.replace('```json', '').replace('```', '').strip()
        return [Product.parse_raw(item) for item in json.loads(cleaned_text)]

    def convert_to_json_object(self, text: str) -> Dict[str, Any]:
        cleaned_text = text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)

    async def evaluate_extracted_products(self, products: List[Dict[str, Union[str, int, float]]]) -> List[Product]:
        existing_products = await self.product.find_many()
        prompt = f"""Voy a darte un array de productos y quiero que me devuelvas **únicamente** un objeto JSON que indique lo que el cliente quiere. Este es el array de productos existentes: {json.dumps(existing_products)}, ahora quiero que me devuelvas un array JSON con los productos que el cliente quiere según los productos existentes. Ejemplo: [{{id: '12', name: "product_name", quantity: 1, price: 1}}] IMPORTANTE: Quiero que únicamente me devuelvas el objeto JSON sin ningún texto adicional. Aquí está el array de productos que quiero que analices: {json.dumps(products)}"""
        try:
            result = self.model.generate_content(prompt).text
            return json.loads(result)
        except Exception as error:
            print(error)
            return []

    async def generate_json_products_catalog(self, products_no_image: List[Dict[str, str]], products: List[Dict[str, str]]) -> Dict[str, Any]:
        prompt = f"""Voy a darte un prompt y quiero que me devuelvas **únicamente** un objeto JSON que me ayude a remplazar el contenido de un objeto JSON con un array de productos en la base de dataSource. Este es el arreglo de productos de la base de datos {json.dumps(products_no_image)}. Y este es un ejemplo de como debe ser el objeto JSON que debes devolver: {{
        "version": "5.0",
        "screens": [
            {{
                "id": "CATALOG",
                "title": "Catalogo",
                "terminal": true,
                "data": {{
                    "catalog_heading": {{
                        "type": "string",
                        "__example__": "Colección de productos"
                    }},
                    "products": {{
                        "type": "array",
                        "items": {{
                            "type": "object",
                            "properties": {{
                                "id": {{
                                    "type": "string"
                                }},
                                "title": {{
                                    "type": "string"
                                }},
                                "description": {{
                                    "type": "string"
                                }},
                                "image": {{}}
                            }}
                        }},
                        "__example__": [
                            {{
                                "id": "1",
                                "title": "Angular",
                                "description": "$499.00",
                                "image": "[image_base64]"
                            }}
                        ]
                    }}
                }},
                "layout": {{
                    "type": "SingleColumnLayout",
                    "children": [
                        {{
                            "type": "Form",
                            "name": "form",
                            "children": [
                                {{
                                    "type": "CheckboxGroup",
                                    "name": "selected_products",
                                    "label": "${{data.catalog_heading}}",
                                    "required": true,
                                    "data-source": "${{data.products}}"
                                }},
                                {{
                                    "type": "Footer",
                                    "label": "Continue",
                                    "on-click-action": {{
                                        "name": "complete",
                                        "payload": {{
                                            "products": "${{form.selected_products}}"
                                        }}
                                    }}
                                }}
                            ]
                        }}
                    ]
                }}
            }}
        ]
    }}. Necesito que me regreses este objeto JSON reemplazando el arreglo de productos que está en __example__ por el arreglo de productos que te estoy enviando. No olvides que no quiero que me regreses texto adicional, solo el objeto JSON."""
        try:
            result = self.model.generate_content(prompt)
            json_generated = self.convert_to_json_object(result)
            for i in range(len(json_generated['screens'][0]['data']['products']['__example__'])):
                json_generated['screens'][0]['data']['products']['__example__'][i] = products[i]
            return json_generated
        except Exception as error:
            print(error)
            return {}

    async def generate_feedback_message(self, feedback: str, client: str) -> str:
        prompt = f"""Voy a darte un mensaje de feedback del cliente y quiero que me devuelvas **únicamente la respuesta que podríamos darle al cliente**. Aquí está el mensaje de feedback: "{feedback}". Recalcarle que es importante que estamos al tanto de su opinión y que estamos trabajando para mejorar nuestros servicios. Puedes agregar al feedback el nombre del cliente para hacerlo más personalizado. No olvides que la respuesta que me des debe de ser relacionada con el feedback del cliente. El nombre del cliente es: "{client}". También puedes agregar algún mensaje de agradecimiento y puedes utilizar emojis para hacerlo más amigable. Trata de no extenderte mucho en la respuesta."""
        try:
            result = self.model.generate_content(prompt)
            return result
        except Exception as error:
            print(error)
            return ""