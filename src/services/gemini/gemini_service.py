import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Any, Dict, Union
from prisma import Prisma

load_dotenv()

class MessageEvaluated(BaseModel):
    is_welcome: bool
    want_to_buy: bool
    is_giving_thanks: bool
    is_account_information: bool
    catalog: Union[None, List[Dict[str, Union[str, int, float]]]]
    is_orders: bool

class Product(BaseModel):
    id: str
    name: str
    quantity: int
    price: float

class GoogleAiService(Prisma):
    def __init__(self):
        super().__init__()
        genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.model = None

    async def on_module_init(self):
        await self.connect()

    async def generate_text(self, history: List[Dict[str, Any]], model: str = "gemini-pro") -> str:
        chat = self.model.start_chat(history=history, generation_config={"max_output_tokens": 100})
        last_message = history[-1]['parts'][0]['text']
        result = await chat.send_message(last_message)
        return result.response.text()

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
            self.model = self.gen_ai.get_generative_model(model="gemini-1.5-flash")
            result = await self.model.generate_content(prompt)
            return self.convert_to_json(result.response.text())
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
            self.model = self.gen_ai.get_generative_model(model="gemini-1.5-flash")
            result = await self.model.generate_content(prompt)
            return self.convert_products_to_json(result.response.text())
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
            self.model = self.gen_ai.get_generative_model(model="gemini-1.5-flash")
            result = await self.model.generate_content(prompt)
            json_generated = self.convert_to_json_object(result.response.text())
            for i in range(len(json_generated['screens'][0]['data']['products']['__example__'])):
                json_generated['screens'][0]['data']['products']['__example__'][i] = products[i]
            return json_generated
        except Exception as error:
            print(error)
            return {}

    async def generate_feedback_message(self, feedback: str, client: str) -> str:
        prompt = f"""Voy a darte un mensaje de feedback del cliente y quiero que me devuelvas **únicamente la respuesta que podríamos darle al cliente**. Aquí está el mensaje de feedback: "{feedback}". Recalcarle que es importante que estamos al tanto de su opinión y que estamos trabajando para mejorar nuestros servicios. Puedes agregar al feedback el nombre del cliente para hacerlo más personalizado. No olvides que la respuesta que me des debe de ser relacionada con el feedback del cliente. El nombre del cliente es: "{client}". También puedes agregar algún mensaje de agradecimiento y puedes utilizar emojis para hacerlo más amigable. Trata de no extenderte mucho en la respuesta."""
        try:
            self.model = self.gen_ai.get_generative_model(model="gemini-1.5-flash")
            result = await self.model.generate_content(prompt)
            return result.response.text()
        except Exception as error:
            print(error)
            return ""