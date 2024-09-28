from openai import OpenAI
from pydantic import BaseModel
import json
from typing import List, Any, Dict, Union
from sqlalchemy import Column, String, Integer, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
import os
from src.services.db.connection import Session as session, Product

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

class OpenAiService:
    def __init__(self):
        super().__init__()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.db_session = session()


    async def generate_text(self, history: List[Dict[str, Any]], model: str = "text-davinci-003") -> str:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for message in history:
            messages.append({"role": message['role'], "content": message['parts'][0]['text']})
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message['content']

    async def evaluate_client_response(self, message_to_evaluate: str) -> MessageEvaluated:
        prompt = f"""Voy a darte un mensaje de un cliente y quiero que me devuelvas **únicamente** un objeto JSON que indique lo que el cliente quiere. Evalúa el mensaje según los siguientes parámetros:
        - Si el cliente está saludando o es alguien nuevo: {{ isWelcome: true }}
        - Si el cliente quiere comprar algo o ver el catalogo de productos: {{ wantToBuy: true }}
        - Si el cliente quiere comprar y selecciona uno o mas productos: {{ wantToBuy: true, catalog: [{{name: "product_name", quantity: 1, price: 1}}] }}
        - Si el cliente está agradeciendo o dando las gracias: {{ isGivingThanks: true }}
        - Si el cliente quiere información de su cuenta: {{ isAccountInformation: true }}
        - Si el cliente quiere logearse {{ isLogin: true }}
        - Si el cliente quiere ver sus pedidos: {{ isOrders: true }},
        - Si el cliente nos da información personal debes devolverla en un array de objetos JSON el json debe tener la llave user_profile_data y dentro de ella un array de objetos JSON con la llave data que tendrá un string y con la llave title que también será string.
        - Debes segmentar el mensaje en distintas categorías y devolver un array de objetos JSON con la llave segmentations y dentro de ella un array de objetos JSON con la llave name y data.
        - Para la segmentación todo mensaje debe ser segmentado, desde información basica como un saludo hasta información relevante como su situación sentimental, nada se debe dejar fuera.
        - Para el perfil de usuario, si el cliente no proporciona información releventate el arreglo debe quedar vacio.
        El JSON debe seguir este formato exacto:
        {{
          "isWelcome": false,
          "wantToBuy": false,
          "isGivingThanks": false,
          "isAccountInformation": false,
          "isOrders": false,
          "catalog": null,
          "isLogin": false,
          "user_profile_data":[
            {{
                "title": null,
                "data": null
            }}
          ],
          "segmentations":[
            {{
                "title": null,
                "data": null
            }}
          ]
        }}
        IMPORTANTE: Quiero que únicamente me devuelvas el objeto JSON sin ningún texto adicional.
        Aquí está el mensaje que quiero que analices: "{message_to_evaluate}" """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}]
            )
            choice_string = response.choices[0].message.content
            return json.loads(choice_string)
        except Exception as error:
            print(error)
            return MessageEvaluated(is_welcome=False, want_to_buy=False, is_giving_thanks=False,
                                    is_account_information=False, is_orders=False, catalog=None)

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
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}]
            )
            return self.convert_products_to_json(response.choices[0].text)
        except Exception as error:
            print(error)
            return []

    async def generate_json_products_catalog(self, products_no_image: List[Dict[str, str]],
                                             products: List[Dict[str, str]]) -> Dict[str, Any]:
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
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}]
            )
            json_generated = self.convert_to_json_object(response.choices[0].text)
            for i in range(len(json_generated['screens'][0]['data']['products']['__example__'])):
                json_generated['screens'][0]['data']['products']['__example__'][i] = products[i]
            return json_generated
        except Exception as error:
            print(error)
            return {}

    async def generate_feedback_message(self, feedback: str, client: str) -> str:
        prompt = f"""Voy a darte un mensaje de feedback del cliente y quiero que me devuelvas **únicamente la respuesta que podríamos darle al cliente**. Aquí está el mensaje de feedback: "{feedback}". Recalcarle que es importante que estamos al tanto de su opinión y que estamos trabajando para mejorar nuestros servicios. Puedes agregar al feedback el nombre del cliente para hacerlo más personalizado. No olvides que la respuesta que me des debe de ser relacionada con el feedback del cliente. El nombre del cliente es: "{client}". También puedes agregar algún mensaje de agradecimiento y puedes utilizar emojis para hacerlo más amigable. Trata de no extenderte mucho en la respuesta."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}]
            )
            return response.choices[0].text
        except Exception as error:
            print(error)
            return ""