from flask import Flask, jsonify, request, session , send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
import sqlite3, os, requests, json, base64
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
from models import init_db
from ai_tools_routes import ai_tools_api
from werkzeug.utils import secure_filename
import os
from gemini_api import gemini_bp


from stud import (
    get_me, login, logout,
    get_categories, add_category, remove_category,
    get_videos, add_video, delete_video,
)


from apscheduler.schedulers.background import BackgroundScheduler
from func import (
    add_project, get_projects,
    add_event, get_events,
    fetch_courses_from_url, URLS  # <-- Add these imports
)
import func

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "a968bac0ac08ac9e4f723563936fc8b01e37e1eaa2e1829b08be72f8e88ccaec"

CORS(app, supports_credentials=True,origins=["http://localhost:8080", "http://localhost:3000","https://studlyf.in", "https://www.studlyf.in"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["SESSION_COOKIE_SAMESITE"] = "None"
app.config["SESSION_COOKIE_SECURE"] = True

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BLOGS_API_KEY = os.getenv("BLOGS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("WARNING: MONGO_URI not found in environment variables")
    MONGO_URI = "mongodb://localhost:27017/studlyf"

try:
    # Configure MongoDB client with proper SSL settings for Atlas
    mongo_client = MongoClient(
        MONGO_URI,
        tls=True,  # Enable TLS/SSL
        tlsAllowInvalidCertificates=False,  # Keep certificate validation
        tlsAllowInvalidHostnames=False,  # Keep hostname validation
        serverSelectionTimeoutMS=20000,  # 20 second timeout
        connectTimeoutMS=20000,  # 20 second connection timeout
        socketTimeoutMS=20000,  # 20 second socket timeout
        retryWrites=True,
        w='majority'
    )
    db = mongo_client.studlyf  # Database name
    users_collection = db.users
    connections_collection = db.connections
    connection_requests_collection = db.connection_requests
    messages_collection = db.messages
    
    # Test the connection
    mongo_client.admin.command('ping')
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    # Try alternative connection method for development
    try:
        print("🔄 Trying alternative connection method...")
        mongo_client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsAllowInvalidCertificates=True,  # Allow invalid certificates for development
            tlsAllowInvalidHostnames=True,  # Allow invalid hostnames for development
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w='majority'
        )
        db = mongo_client.studlyf
        users_collection = db.users
        connections_collection = db.connections
        connection_requests_collection = db.connection_requests
        messages_collection = db.messages
        
        # Test the connection
        mongo_client.admin.command('ping')
        print("✅ Connected to MongoDB (with relaxed SSL settings)")
    except Exception as e2:
        print(f"❌ Alternative MongoDB connection also failed: {e2}")
        db = None

# Firebase Admin Initialization
FIREBASE_ADMIN_KEY = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
if FIREBASE_ADMIN_KEY:
    try:
        # Decode base64 Firebase admin key
        firebase_key = json.loads(base64.b64decode(FIREBASE_ADMIN_KEY).decode('utf-8'))
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized")
    except Exception as e:
        print(f"❌ Firebase Admin initialization error: {e}")
else:
    print("WARNING: FIREBASE_ADMIN_KEY not found in environment variables")

app.register_blueprint(gemini_bp, url_prefix="/api")

@app.route("/")
def index():
    return jsonify({"message": "Flask backend is running!"})

# ===================== AUTHENTICATION MIDDLEWARE =====================
def authenticate_user(f):
    """Decorator to authenticate Firebase users"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get the authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401
            
            # Extract the token
            token = auth_header.split('Bearer ')[1]
            
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(token)
            request.user_uid = decoded_token['uid']
            request.user_email = decoded_token.get('email')
            
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Authentication error: {e}")
            return jsonify({'error': 'Invalid token'}), 401
    
    return decorated_function

# ===================== USER MANAGEMENT ROUTES =====================

@app.route('/api/user', methods=['POST'])
@authenticate_user
def create_or_update_user():
    """Create or update user profile"""
    try:
        data = request.get_json()
        uid = data.get('uid')
        
        # Ensure user can only create/update their own profile
        if request.user_uid != uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Check if user exists
        existing_user = users_collection.find_one({'uid': uid})
        
        if existing_user:
            # Update existing user
            users_collection.update_one(
                {'uid': uid},
                {'$set': {**data, 'updatedAt': datetime.utcnow()}}
            )
            updated_user = users_collection.find_one({'uid': uid})
            # Convert ObjectId to string for JSON serialization
            updated_user['_id'] = str(updated_user['_id'])
            return jsonify(updated_user)
        else:
            # Create new user
            user_data = {
                'uid': uid,
                'name': data.get('name'),
                'email': data.get('email'),
                'photoURL': data.get('photoURL'),
                'firstName': '',
                'lastName': '',
                'bio': '',
                'branch': '',
                'year': '',
                'college': '',
                'city': '',
                'phoneNumber': '',
                'linkedinUrl': '',
                'githubUrl': '',
                'portfolioUrl': '',
                'profilePicture': data.get('photoURL', ''),
                'skills': [],
                'interests': [],
                'careerGoals': '',
                'dateOfBirth': '',
                'resumeFiles': [],
                'projectFiles': [],
                'certificationFiles': [],
                'isOnline': True,
                'completedProfile': False,
                'createdAt': datetime.utcnow(),
                'updatedAt': datetime.utcnow()
            }
            
            # Set _id to uid for consistency
            user_data['_id'] = uid
            
            users_collection.insert_one(user_data)
            user_data['_id'] = str(user_data['_id'])
            return jsonify(user_data), 201
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/<uid>', methods=['GET'])
@authenticate_user
def get_user_profile(uid):
    """Get user profile (protected - only own profile)"""
    try:
        # Ensure user can only access their own profile
        if request.user_uid != uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        user = users_collection.find_one({'uid': uid})
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        return jsonify(user)
        
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/<uid>/public', methods=['GET'])
@authenticate_user
def get_public_user_profile(uid):
    """Get any user's public profile (read-only, requires authentication)"""
    try:
        user = users_collection.find_one({'uid': uid})
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Convert ObjectId to string
        user['_id'] = str(user['_id'])
        return jsonify(user)
        
    except Exception as e:
        print(f"Error getting public user profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile/<uid>', methods=['POST'])
@authenticate_user
def update_user_profile(uid):
    """Update user profile (protected - only own profile)"""
    try:
        # Ensure user can only update their own profile
        if request.user_uid != uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        data = request.get_json()
        
        # Check data size limit (100KB)
        data_size = len(json.dumps(data).encode('utf-8'))
        if data_size > 100 * 1024:
            return jsonify({'error': 'Profile data exceeds 100KB limit'}), 400
        
        # Update user profile
        data['uid'] = uid
        data['_id'] = uid
        data['updatedAt'] = datetime.utcnow()
        
        users_collection.update_one(
            {'uid': uid},
            {'$set': data},
            upsert=True
        )
        
        updated_user = users_collection.find_one({'uid': uid})
        updated_user['_id'] = str(updated_user['_id'])
        return jsonify(updated_user)
        
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Get all users (public - no authentication required)"""
    try:
        # Only return essential public fields
        users = list(users_collection.find({}, {
            '_id': 1,
            'uid': 1,
            'firstName': 1,
            'lastName': 1,
            'profilePicture': 1,
            'bio': 1,
            'skills': 1,
            'interests': 1,
            'college': 1,
            'year': 1,
            'branch': 1,
            'city': 1,
            'isOnline': 1
        }))
        
        # Convert ObjectId to string for each user
        for user in users:
            user['_id'] = str(user['_id'])
        
        return jsonify(users)
        
    except Exception as e:
        print(f"Error getting all users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

# ===================== CONNECTION MANAGEMENT ROUTES =====================

@app.route('/api/connections/<uid>', methods=['GET'])
@authenticate_user
def get_user_connections(uid):
    """Get all connections for a user (protected - only own connections)"""
    try:
        # Ensure user can only access their own connections
        if request.user_uid != uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        connections = list(connections_collection.find({
            '$or': [
                {'fromUid': uid},
                {'toUid': uid}
            ]
        }))
        
        # Convert ObjectId to string for each connection
        for conn in connections:
            conn['_id'] = str(conn['_id'])
        
        return jsonify(connections)
        
    except Exception as e:
        print(f"Error getting user connections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections/request', methods=['POST'])
@authenticate_user
def send_connection_request():
    """Send connection request (protected)"""
    try:
        data = request.get_json()
        from_uid = data.get('from')
        to_uid = data.get('to')
        
        if not from_uid or not to_uid:
            return jsonify({'error': 'Missing from or to'}), 400
        
        # Ensure user can only send requests from their own UID
        if request.user_uid != from_uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Check if request already exists
        existing_request = connection_requests_collection.find_one({
            'from': from_uid,
            'to': to_uid
        })
        if existing_request:
            return jsonify({'error': 'Request already sent'}), 409
        
        # Check if already connected
        existing_connection = connections_collection.find_one({
            '$or': [
                {'fromUid': from_uid, 'toUid': to_uid},
                {'fromUid': to_uid, 'toUid': from_uid}
            ]
        })
        if existing_connection:
            return jsonify({'error': 'Already connected'}), 409
        
        # Create connection request with auto-expiry after 24 hours
        request_data = {
            'from': from_uid,
            'to': to_uid,
            'createdAt': datetime.utcnow()
        }
        
        result = connection_requests_collection.insert_one(request_data)
        request_data['_id'] = str(result.inserted_id)
        
        return jsonify(request_data), 201
        
    except Exception as e:
        print(f"Error sending connection request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections/accept', methods=['POST'])
@authenticate_user
def accept_connection_request():
    """Accept connection request (protected)"""
    try:
        data = request.get_json()
        from_uid = data.get('from')
        to_uid = data.get('to')
        
        if not from_uid or not to_uid:
            return jsonify({'error': 'Missing from or to'}), 400
        
        # Ensure user can only accept requests sent to them
        if request.user_uid != to_uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Create connection
        connection_data = {
            'fromUid': from_uid,
            'toUid': to_uid,
            'createdAt': datetime.utcnow()
        }
        connections_collection.insert_one(connection_data)
        
        # Remove connection request
        connection_requests_collection.delete_one({
            'from': from_uid,
            'to': to_uid
        })
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error accepting connection request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections/reject', methods=['POST'])
@authenticate_user
def reject_connection_request():
    """Reject connection request (protected)"""
    try:
        data = request.get_json()
        from_uid = data.get('from')
        to_uid = data.get('to')
        
        if not from_uid or not to_uid:
            return jsonify({'error': 'Missing from or to'}), 400
        
        # Ensure user can only reject requests sent to them
        if request.user_uid != to_uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Remove connection request
        connection_requests_collection.delete_one({
            'from': from_uid,
            'to': to_uid
        })
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"Error rejecting connection request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections/requests/<uid>', methods=['GET'])
@authenticate_user
def get_connection_requests(uid):
    """Get connection requests for a user (protected - only own requests)"""
    try:
        # Ensure user can only view their own requests
        if request.user_uid != uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        requests = list(connection_requests_collection.find({'to': uid}))
        
        # Convert ObjectId to string for each request
        for req in requests:
            req['_id'] = str(req['_id'])
        
        return jsonify(requests)
        
    except Exception as e:
        print(f"Error getting connection requests: {e}")
        return jsonify({'error': str(e)}), 500

# ===================== MESSAGING ROUTES =====================

@app.route('/api/messages/send', methods=['POST'])
@authenticate_user
def send_message():
    """Send a message (protected)"""
    try:
        data = request.get_json()
        from_uid = data.get('from')
        to_uid = data.get('to')
        text = data.get('text')
        
        if not from_uid or not to_uid or not text:
            return jsonify({'error': 'Missing from, to, or text'}), 400
        
        # Ensure user can only send messages from their own UID
        if request.user_uid != from_uid:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        # Create message with auto-expiry after 24 hours
        message_data = {
            'from': from_uid,
            'to': to_uid,
            'text': text,
            'createdAt': datetime.utcnow()
        }
        
        result = messages_collection.insert_one(message_data)
        message_data['_id'] = str(result.inserted_id)
        
        return jsonify(message_data), 201
        
    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/<uid1>/<uid2>', methods=['GET'])
@authenticate_user
def get_messages(uid1, uid2):
    """Get messages between two users (protected - only if user is involved)"""
    try:
        # Ensure user can only view messages they're involved in
        if request.user_uid != uid1 and request.user_uid != uid2:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        messages = list(messages_collection.find({
            '$or': [
                {'from': uid1, 'to': uid2},
                {'from': uid2, 'to': uid1}
            ]
        }).sort('createdAt', 1))
        
        # Convert ObjectId to string for each message
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        
        return jsonify(messages)
        
    except Exception as e:
        print(f"Error getting messages: {e}")
        return jsonify({'error': str(e)}), 500

# ===================== HEALTH CHECK ROUTES =====================

@app.route('/api', methods=['GET'])
def api_health():
    """API health check"""
    return 'StudLyf Flask Backend API is running!'

@app.route('/api/health', methods=['GET'])
def health_check():
    """Detailed health check"""
    try:
        # Test MongoDB connection
        db.command('ping')
        mongo_status = 'Connected'
    except:
        mongo_status = 'Disconnected'
    
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.utcnow().isoformat(),
        'mongodb': mongo_status,
        'cors': {
            'allowedOrigins': ['http://localhost:8080', 'https://studlyf.in', 'https://www.studlyf.in']
        }
    })

# ===================== BACKGROUND TASK FOR MESSAGE/REQUEST CLEANUP =====================

def cleanup_expired_data():
    """Clean up expired messages and connection requests"""
    try:
        # Remove messages older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        messages_collection.delete_many({'createdAt': {'$lt': cutoff_time}})
        
        # Remove connection requests older than 24 hours
        connection_requests_collection.delete_many({'createdAt': {'$lt': cutoff_time}})
        
        print(f"[{datetime.utcnow()}] Cleaned up expired data")
    except Exception as e:
        print(f"Error during cleanup: {e}")

# ----------------- COURSES, PROJECTS, CERTIFICATIONS SCRAPING ROUTES -----------------
@app.route('/free-courses')
def free_courses():
    courses = fetch_courses_from_url(URLS["courses"], "Coursera")
    return jsonify({"courses": courses[:20]})

@app.route('/projects')
def guided_projects():
    projects = fetch_courses_from_url(URLS["projects"], "Coursera")
    return jsonify({"projects": projects[:20]})

@app.route('/certifications')
def certifications():
    certificates = fetch_courses_from_url(URLS["certificates"], "Coursera")
    return jsonify({"certificates": certificates[:20]})

# Projects routes
@app.route("/project-hunt", methods=["GET", "POST"])
def projects():
    if request.method == "POST":
        data = request.json
        new_project = add_project(data)
        return jsonify({
            "id": new_project[0],
            "title": new_project[1],
            "description": new_project[2],
            "tech_stack": new_project[3],
            "roles": new_project[4],
            "duration": new_project[5],
            "last_date": new_project[6],
            "links": new_project[7]
        }), 201
    else:
        projects = get_projects()
        return jsonify({
            "projects": [
                {
                    "id": p[0],
                    "title": p[1],
                    "description": p[2],
                    "tech_stack": p[3],
                    "roles": p[4],
                    "duration": p[5],
                    "last_date": p[6],
                    "links": p[7]
                } for p in projects
            ]
        })

# Register blueprints
from youtube_course import youtubecourse_api
app.register_blueprint(youtubecourse_api)



def allowed_file(filename):
    """Check file extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("username") or session.get("role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        return f(*args, **kwargs)

    return wrapper


# -------------------- Authentication --------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    user = func.get_user_by_username(username)
    if user and func.verify_password(user[2], password):
        session["username"] = username
        session["role"] = user[3]
        return jsonify({"message": "Login successful", "role": user[3]})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# -------------------- Event CRUD --------------------
@app.route("/events", methods=["POST"])
# @app.route("/events", methods=["POST"])
def create_event():
    """Add new event with optional image (<500KB)."""
    try:
        image = request.files.get("image")
        image_url = None

        # Validate & save image
        if image and allowed_file(image.filename):
            image.seek(0, os.SEEK_END)
            size = image.tell()
            image.seek(0)
            if size > 500 * 1024:
                return jsonify({"error": "Image exceeds 500 KB limit"}), 400

            filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, filename))
            image_url = f"/uploads/{filename}"

        # Other form data
        data = {k: request.form.get(k) for k in request.form.keys()}
        data["image_url"] = image_url

        new_event = func.add_event(data)

        return jsonify({
            "id": new_event[0],
            "title": new_event[1],
            "description": new_event[2],
            "type": new_event[3],
            "location": new_event[4],
            "event_date": new_event[5],
            "time": new_event[6],
            "attendees": new_event[7],
            "registration_link": new_event[8],
            "registration_end_date": new_event[9],
            "image_url": new_event[10],
        }), 201
    except Exception as e:
        print("Error creating event:", e)
        return jsonify({"error": str(e)}), 500




@app.route("/events", methods=["GET"])
def list_events():
    """List all events."""
    try:
        events = func.get_events()
        return jsonify({
            "events": [
                {
                    "id": e[0],
                    "title": e[1],
                    "description": e[2],
                    "type": e[3],
                    "location": e[4],
                    "event_date": e[5],
                    "time": e[6],
                    "attendees": e[7],
                    "registration_link": e[8],
                    "registration_end_date": e[9],
                    "image_url": e[10],
                } for e in events
            ]
        })
    except Exception as e:
        print("Error listing events:", e)
        return jsonify({"error": str(e)}), 500




@app.route("/events/<int:event_id>", methods=["DELETE"])
def remove_event(event_id):
    """Delete an event by ID."""
    try:
        func.delete_event(event_id)
        return jsonify({"message": "Event deleted"})
    except Exception as e:
        print("Error deleting event:", e)
        return jsonify({"error": str(e)}), 500


# -------------------- Serve uploads --------------------
@app.route("/uploads/<path:filename>")
def serve_image(filename):
    """Serve uploaded images."""
    return send_from_directory(UPLOAD_FOLDER, filename)



cached_news = []
cached_blogs = []
cached_shorts = []

# ----------------- FETCH FUNCTIONS -----------------
def fetch_news():
    global cached_news
    query = "AI OR technology OR software OR cloud computing"
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en&sortBy=publishedAt&pageSize=20&apiKey={NEWS_API_KEY}"
    )
    r = requests.get(url)
    if r.status_code == 200:
        cached_news = r.json().get("articles", [])
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_news)} news articles")
    else:
        print(f"News fetch error: {r.status_code}, {r.text}")

def fetch_blogs():
    global cached_blogs
    query = "AI OR technology OR software OR cloud computing"
    from_date = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language=en"
        f"&from={from_date}"
        f"&sortBy=popularity"
        f"&pageSize=15&apiKey={BLOGS_API_KEY}"
    )
    r = requests.get(url)
    if r.status_code == 200:
        cached_blogs = r.json().get("articles", [])
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_blogs)} blogs")
    else:
        print(f"Blogs fetch error: {r.status_code}, {r.text}")

def fetch_shorts():
    global cached_shorts
    query = "AI OR technology OR software OR jobs OR cloud computing"
    published_after = (datetime.utcnow() - timedelta(days=30)).isoformat("T") + "Z"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "viewCount",
        "maxResults": 15,
        "publishedAfter": published_after,
        "key": YOUTUBE_API_KEY
    }
    r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
    if r.status_code == 200:
        items = r.json().get("items", [])
        cached_shorts = [
            {
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                "video_url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "published_at": item["snippet"]["publishedAt"]
            }
            for item in items
        ]
        print(f"[{datetime.now(timezone.utc)}] Fetched {len(cached_shorts)} YouTube shorts")
    else:
        print(f"YouTube fetch error: {r.status_code}, {r.text}")

# ----------------- ROUTES -----------------
@app.route("/tech-news")
def tech_news():
    return jsonify({"news": cached_news})

@app.route("/blogs")
def blogs():
    return jsonify({"blogs": cached_blogs})

@app.route("/youtube-shorts")
def youtube_shorts():
    return jsonify({"shorts": cached_shorts})

@app.route("/refresh-news")
def refresh_news():
    fetch_news()
    return jsonify({"status": "news refreshed"})

@app.route("/refresh-blogs")
def refresh_blogs():
    fetch_blogs()
    return jsonify({"status": "blogs refreshed"})

@app.route("/refresh-shorts")
def refresh_shorts():
    fetch_shorts()
    return jsonify({"status": "shorts refreshed"})

# ----------------- SCHEDULER -----------------
def schedule_jobs():
    scheduler = BackgroundScheduler()
    
    # Schedule news, blogs, and shorts fetching
    for hour in [0, 6, 12, 18]:
        scheduler.add_job(fetch_news, 'cron', hour=hour, minute=0)
    for hour in [0, 12]:
        scheduler.add_job(fetch_blogs, 'cron', hour=hour, minute=0)
        scheduler.add_job(fetch_shorts, 'cron', hour=hour, minute=0)
    
    # Schedule cleanup of expired data every hour
    scheduler.add_job(cleanup_expired_data, 'cron', minute=0)
    
    scheduler.start()

# ===================== DATABASE INDEXES FOR PERFORMANCE =====================
def create_indexes():
    """Create database indexes for better performance"""
    try:
        # User collection indexes
        users_collection.create_index('uid', unique=True)
        users_collection.create_index('email')
        
        # Connection collection indexes
        connections_collection.create_index([('fromUid', 1), ('toUid', 1)])
        connections_collection.create_index('fromUid')
        connections_collection.create_index('toUid')
        
        # Connection requests indexes
        connection_requests_collection.create_index([('from', 1), ('to', 1)])
        connection_requests_collection.create_index('to')
        connection_requests_collection.create_index('createdAt', expireAfterSeconds=86400)  # 24 hours
        
        # Messages indexes
        messages_collection.create_index([('from', 1), ('to', 1)])
        messages_collection.create_index('createdAt', expireAfterSeconds=86400)  # 24 hours
        
        print("✅ Database indexes created")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")





app.route("/api/me")(get_me)
app.route("/login", methods=["POST"])(login)
app.route("/logout", methods=["POST"])(logout)
app.route("/studverse/categories")(get_categories)
app.route("/studverse/categories", methods=["POST"])(add_category)
app.route("/studverse/categories/<category>", methods=["DELETE"])(remove_category)
app.route("/studverse/videos/<category>")(get_videos)
app.route("/studverse/videos/<category>", methods=["POST"])(add_video)
app.route("/studverse/videos/<category>", methods=["DELETE"])(delete_video)

app.register_blueprint(ai_tools_api)
from ads_api import get_ads, add_ad, delete_ad

app.route("/ads")(get_ads)
app.route("/ads", methods=["POST"])(add_ad)
app.route("/ads/<int:ad_id>", methods=["DELETE"])(delete_ad)
# ----------------- MAIN -----------------
if __name__ == "__main__":
    # Initialize data fetching
    fetch_news()
    fetch_blogs()
    fetch_shorts()
    
    # Create database indexes
    if db is not None:
        create_indexes()
    
    # Start background scheduler
    schedule_jobs()
    
    # Run the Flask appeven
    app.run(debug=True, port=5001, host='0.0.0.0')