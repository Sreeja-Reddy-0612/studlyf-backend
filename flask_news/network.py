import sys
import os

# Add parent directory (backend/) to sys.path so 'models' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Blueprint, request, jsonify
from models.User import User
from bson import ObjectId

network_bp = Blueprint('network', __name__, url_prefix='/api/network')

@network_bp.route('/users', methods=['GET'])
def get_users():
    user_id = request.args.get("userId")
    users = User.objects(id__ne=ObjectId(user_id))
    user_list = [user.to_json() for user in users]
    return jsonify(user_list), 200

@network_bp.route('/connections', methods=['GET'])
def get_connections():
    user_id = request.args.get("userId")
    connections = Connection.objects(__raw__={
        "$or": [{"user1": ObjectId(user_id)}, {"user2": ObjectId(user_id)}]
    })
    conn_list = [conn.to_json() for conn in connections]
    return jsonify(conn_list), 200

@network_bp.route('/connection-requests', methods=['GET'])
def get_connection_requests():
    user_id = request.args.get("userId")
    requests = ConnectionRequest.objects(to=ObjectId(user_id), status='pending')
    req_list = [req.to_json() for req in requests]
    return jsonify(req_list), 200

@network_bp.route('/connection-requests', methods=['POST'])
def send_connection_request():
    data = request.get_json()
    from_user = data.get("from")
    to_user = data.get("to")
    if from_user == to_user:
        return jsonify({"message": "Cannot connect to yourself."}), 400

    existing_req = ConnectionRequest.objects(from_=ObjectId(from_user), to=ObjectId(to_user), status='pending').first()
    if existing_req:
        return jsonify({"message": "Request already pending."}), 409

    existing_conn = Connection.objects(__raw__={
        "$or": [
            {"user1": ObjectId(from_user), "user2": ObjectId(to_user)},
            {"user1": ObjectId(to_user), "user2": ObjectId(from_user)}
        ]
    }).first()
    if existing_conn:
        return jsonify({"message": "Already connected."}), 409

    new_request = ConnectionRequest(from_=ObjectId(from_user), to=ObjectId(to_user), status='pending')
    new_request.save()
    return jsonify({"message": "Request sent."}), 201

@network_bp.route('/connection-requests/<string:req_id>/accept', methods=['POST'])
def accept_connection_request(req_id):
    request_obj = ConnectionRequest.objects(id=ObjectId(req_id)).first()
    if not request_obj or request_obj.status != 'pending':
        return jsonify({"message": "No such pending request."}), 404

    request_obj.status = 'accepted'
    request_obj.save()

    new_connection = Connection(user1=request_obj.from_, user2=request_obj.to)
    new_connection.save()
    return jsonify({"message": "Connection established."}), 200

@network_bp.route('/connection-requests/<string:req_id>/reject', methods=['POST'])
def reject_connection_request(req_id):
    request_obj = ConnectionRequest.objects(id=ObjectId(req_id)).first()
    if not request_obj or request_obj.status != 'pending':
        return jsonify({"message": "No such pending request."}), 404

    request_obj.status = 'rejected'
    request_obj.save()
    return jsonify({"message": "Request rejected."}), 200

@network_bp.route('/<uid>', methods=['GET'])
def get_user_connections(uid):
    # TODO: Replace with actual logic to fetch connections for user
    return jsonify([])

@network_bp.route('/requests/<uid>', methods=['GET'])
def get_user_connection_requests(uid):
    # TODO: Replace with actual logic to fetch pending requests for user
    return jsonify([])
