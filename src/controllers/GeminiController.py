from flask import request, jsonify, Blueprint
from src.services.gemini import gemini_service, generate_prompt

gemini_controller = Blueprint('gemini_controller', __name__)

@gemini_controller.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    user_input = data['user_input']
    history = data['history']
    prompt = generate_prompt.generate(user_input, history)
    response = gemini_service.model.generate_content(prompt)
    return jsonify({'IA': response.text})
