from flask import Blueprint, jsonify, request
from models import init_db, get_all_tools, add_tool_from_dict

ai_tools_api = Blueprint('ai_tools_api', __name__)

init_db()

@ai_tools_api.route('/api/ai-tools', methods=['GET'])
def list_tools():
    tools = get_all_tools()
    return jsonify(tools)

@ai_tools_api.route('/api/ai-tools', methods=['POST'])
def create_tool():
    data = request.json
    tool = add_tool_from_dict(data)
    return jsonify(tool.to_dict()), 201

@ai_tools_api.route('/api/ai-tools/health', methods=['GET'])
def health():
    return jsonify({"status": "ai-tools-api-up"}), 200
