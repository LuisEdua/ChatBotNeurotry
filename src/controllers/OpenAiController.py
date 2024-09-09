from flask import request, jsonify, Blueprint
from src.services.OpenAi import generate_prompt, OpenAi_service

openai_controller = Blueprint('openai_controller', __name__)


@openai_controller.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_input = data['user_input']
    history = data['history']
    prompt = generate_prompt.generate(user_input, history)


    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]

    response = OpenAi_service.client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    return jsonify({'IA': response.choices[0].message.content})