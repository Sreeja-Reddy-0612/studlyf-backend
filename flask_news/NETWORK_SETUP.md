# Network Page Setup Instructions

## Prerequisites

1. **MongoDB Atlas Account**: Create a MongoDB Atlas cluster and get your connection string
2. **Firebase Admin SDK**: Download your Firebase Admin SDK JSON file from Firebase Console
3. **Python Environment**: Python 3.8+ with virtual environment

## Setup Steps

### 1. Install Dependencies

```bash
cd backend/flask_news
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in `backend/flask_news/` with the following variables:

```bash
# MongoDB Configuration
MONGO_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/studlyf?retryWrites=true&w=majority

# Firebase Admin SDK Configuration (Base64 encoded JSON)
FIREBASE_ADMIN_KEY=your_base64_encoded_firebase_admin_key_here

# News API Keys (optional for network functionality)
NEWS_API_KEY=your_news_api_key_here
BLOGS_API_KEY=your_blogs_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 3. Firebase Admin Key Setup

1. Go to Firebase Console > Project Settings > Service Accounts
2. Click "Generate new private key" and download the JSON file
3. Convert the JSON file to base64:

**Linux/Mac:**
```bash
base64 -i path/to/your/firebase-admin-key.json
```

**Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("path\to\your\firebase-admin-key.json"))
```

4. Copy the base64 string and paste it as the value for `FIREBASE_ADMIN_KEY` in your `.env` file

### 4. MongoDB Setup

1. Create a MongoDB Atlas cluster
2. Create a database named `studlyf`
3. The following collections will be created automatically:
   - `users` - User profiles
   - `connections` - User connections
   - `connection_requests` - Pending connection requests
   - `messages` - Chat messages (auto-expire after 24 hours)

### 5. Run the Flask Backend

```bash
cd backend/flask_news
python app.py
```

The server will start on `http://localhost:5001`

### 6. Frontend Configuration

The frontend is already configured to use the Flask backend. Make sure your frontend points to:
- Development: `http://localhost:5001`
- Production: Update the URL in `frontend/src/lib/api.ts`

## API Endpoints

### User Management
- `POST /api/user` - Create/update user profile
- `GET /api/profile/<uid>` - Get own profile
- `GET /api/profile/<uid>/public` - Get any user's public profile
- `POST /api/profile/<uid>` - Update own profile
- `GET /api/users` - Get all users (public)

### Connections
- `GET /api/connections/<uid>` - Get user's connections
- `POST /api/connections/request` - Send connection request
- `POST /api/connections/accept` - Accept connection request
- `POST /api/connections/reject` - Reject connection request
- `GET /api/connections/requests/<uid>` - Get pending requests

### Messaging
- `POST /api/messages/send` - Send message
- `GET /api/messages/<uid1>/<uid2>` - Get conversation

### Health Check
- `GET /api` - Basic health check
- `GET /api/health` - Detailed health check with MongoDB status

## Features

✅ **Complete Authentication**: Firebase JWT token verification
✅ **User Profiles**: Full CRUD operations with MongoDB
✅ **Connection System**: Send, accept, reject connection requests
✅ **Real-time Messaging**: Chat system with auto-expiring messages
✅ **Security**: User can only access/modify their own data
✅ **Performance**: Database indexes for optimal query performance
✅ **Auto-cleanup**: Expired messages and requests are automatically removed
✅ **CORS**: Configured for both development and production

## Testing the Network Flow

1. **Register Users**: Create multiple user accounts through the frontend
2. **Complete Profiles**: Fill out user profiles with name, skills, college
3. **Browse Network**: View other users in the network page
4. **Send Requests**: Click "Connect" on user cards
5. **Accept/Reject**: Manage incoming requests in the sidebar
6. **Chat**: Message connected users

## Database Schema

### Users Collection
```javascript
{
  _id: "firebase_uid",
  uid: "firebase_uid",
  firstName: "John",
  lastName: "Doe",
  email: "john@example.com",
  profilePicture: "url",
  bio: "Student at XYZ University",
  college: "XYZ University",
  branch: "Computer Science",
  year: "2024",
  skills: ["JavaScript", "Python"],
  interests: ["AI", "Web Development"],
  // ... other fields
}
```

### Connections Collection
```javascript
{
  fromUid: "user1_uid",
  toUid: "user2_uid",
  createdAt: ISODate()
}
```

### Connection Requests Collection
```javascript
{
  from: "sender_uid",
  to: "receiver_uid",
  createdAt: ISODate() // Auto-expires after 24 hours
}
```

### Messages Collection
```javascript
{
  from: "sender_uid",
  to: "receiver_uid",
  text: "Message content",
  createdAt: ISODate() // Auto-expires after 24 hours
}
```

## Troubleshooting

1. **MongoDB Connection Issues**: Check your MONGO_URI and network access
2. **Firebase Authentication**: Verify your FIREBASE_ADMIN_KEY is correctly base64 encoded
3. **CORS Errors**: Ensure your frontend URL is in the allowed origins list
4. **Port Conflicts**: Change the port in app.py if 5001 is already in use

