require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const authenticate = require('../middleware/authenticate');

const app = express();

// Middleware
const allowedOrigins = [
  'http://localhost:8000',
  'https://studlyf.in',
];

app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);
    
    if (allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      console.log('Blocked origin:', origin);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '20kb' }));

// MongoDB Connection
const mongoUri = process.env.MONGO_URI;
if (!mongoose.connection.readyState) {
  mongoose.connect(mongoUri, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => console.log('✅ Connected to MongoDB'))
    .catch(err => console.error('❌ MongoDB connection error:', err));
}

// User Schema
const userSchema = new mongoose.Schema({
  _id: { type: String, required: true },
  uid: { type: String, required: true, unique: true }, // Firebase UID
  name: String,
  firstName: String,
  lastName: String,
  bio: String,
  branch: String,
  year: String,
  college: String,
  city: String,
  phoneNumber: String,
  linkedinUrl: String,
  githubUrl: String,
  portfolioUrl: String,
  profilePicture: String,
  skills: [String],
  interests: [String],
  careerGoals: String,
  dateOfBirth: String,
  resumeFiles: [String],
  projectFiles: [String],
  certificationFiles: [String],
  isOnline: Boolean,
  completedProfile: Boolean,
  createdAt: Date,
  updatedAt: Date,
  email: String,
  photoURL: String,
}, { timestamps: true, collection: 'users' });

userSchema.pre('save', function (next) {
  const docSize = Buffer.byteLength(JSON.stringify(this.toObject()));
  if (docSize > 100 * 1024) {
    return next(new Error('Profile data exceeds 100KB limit.'));
  }
  next();
});

const User = mongoose.models.User || mongoose.model('User', userSchema);

// Connection Schema
const connectionSchema = new mongoose.Schema({
  fromUid: { type: String, required: true },
  toUid: { type: String, required: true }
}, { timestamps: true });

const Connection = mongoose.models.Connection || mongoose.model('Connection', connectionSchema);

// Message Schema
const messageSchema = new mongoose.Schema({
  from: { type: String, required: true },
  to: { type: String, required: true },
  text: { type: String, required: true },
  createdAt: { type: Date, default: Date.now, expires: 86400 }
}, { collection: 'messages' });

const Message = mongoose.models.Message || mongoose.model('Message', messageSchema);

// Connection Request Schema
const connectionRequestSchema = new mongoose.Schema({
  from: { type: String, required: true },
  to: { type: String, required: true },
  createdAt: { type: Date, default: Date.now, expires: 86400 }
}, { collection: 'connection_requests' });

const ConnectionRequest = mongoose.models.ConnectionRequest || mongoose.model('ConnectionRequest', connectionRequestSchema);

// === Routes ===

// Add new user (auto on login) - PROTECTED
app.post('/api/user', authenticate, async (req, res) => {
  const { uid, name, email, photoURL } = req.body;
  try {
    // Ensure user can only create/update their own profile
    if (req.user.uid !== uid) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    let user = await User.findOne({ uid });
    if (!user) {
      user = new User({ uid, name, email, photoURL, _id: uid });
      await user.save();
    }
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get user profile (protected - only own profile)
app.get('/api/profile/:uid', authenticate, async (req, res) => {
  try {
    if (req.user.uid !== req.params.uid) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    const user = await User.findById(req.params.uid);
    if (!user) return res.status(404).json({ message: 'User not found' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Public: Get any user's profile (read-only, requires authentication)
app.get('/api/profile/:uid/public', authenticate, async (req, res) => {
  try {
    const user = await User.findById(req.params.uid);
    if (!user) return res.status(404).json({ message: 'User not found' });
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Create or update user profile (protected - only own profile)
app.post('/api/profile/:uid', authenticate, async (req, res) => {
  try {
    if (req.user.uid !== req.params.uid) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    const data = req.body;
    if (Buffer.byteLength(JSON.stringify(data)) > 100 * 1024) {
      return res.status(400).json({ error: 'Profile data exceeds 100KB limit.' });
    }
    data._id = req.params.uid;
    data.uid = req.params.uid; // Ensure uid is set
    const user = await User.findByIdAndUpdate(
      req.params.uid,
      { $set: data },
      { upsert: true, new: true, setDefaultsOnInsert: true }
    );
    res.json(user);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get all connections for a user (protected - only own connections)
app.get('/api/connections/:uid', authenticate, async (req, res) => {
  try {
    if (req.user.uid !== req.params.uid) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    const conns = await Connection.find({ 
      $or: [{ fromUid: req.params.uid }, { toUid: req.params.uid }] 
    });
    res.json(conns);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Send connection request (protected)
app.post('/api/connections/request', authenticate, async (req, res) => {
  try {
    const { from, to } = req.body;
    if (!from || !to) return res.status(400).json({ error: 'Missing from or to' });
    
    // Ensure user can only send requests from their own UID
    if (req.user.uid !== from) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    const exists = await ConnectionRequest.findOne({ from, to });
    if (exists) return res.status(409).json({ error: 'Request already sent' });
    
    const connected = await Connection.findOne({ 
      $or: [{ fromUid: from, toUid: to }, { fromUid: to, toUid: from }] 
    });
    if (connected) return res.status(409).json({ error: 'Already connected' });
    
    const reqDoc = await ConnectionRequest.create({ from, to });
    res.json(reqDoc);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Accept connection request (protected)
app.post('/api/connections/accept', authenticate, async (req, res) => {
  try {
    const { from, to } = req.body;
    if (!from || !to) return res.status(400).json({ error: 'Missing from or to' });
    
    // Ensure user can only accept requests sent to them
    if (req.user.uid !== to) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    await Connection.create({ fromUid: from, toUid: to });
    await ConnectionRequest.deleteOne({ from, to });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Reject connection request (protected)
app.post('/api/connections/reject', authenticate, async (req, res) => {
  try {
    const { from, to } = req.body;
    if (!from || !to) return res.status(400).json({ error: 'Missing from or to' });
    
    // Ensure user can only reject requests sent to them
    if (req.user.uid !== to) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    await ConnectionRequest.deleteOne({ from, to });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get connection requests for a user (protected - only own requests)
app.get('/api/connections/requests/:uid', authenticate, async (req, res) => {
  try {
    const { uid } = req.params;
    
    // Ensure user can only view their own requests
    if (req.user.uid !== uid) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    const requests = await ConnectionRequest.find({ to: uid });
    res.json(requests);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Send a message (protected)
app.post('/api/messages/send', authenticate, async (req, res) => {
  try {
    const { from, to, text } = req.body;
    if (!from || !to || !text) return res.status(400).json({ error: 'Missing from, to, or text' });
    
    // Ensure user can only send messages from their own UID
    if (req.user.uid !== from) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    const msg = await Message.create({ from, to, text });
    res.json(msg);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get messages between two users (protected - only if user is involved)
app.get('/api/messages/:uid1/:uid2', authenticate, async (req, res) => {
  try {
    const { uid1, uid2 } = req.params;
    
    // Ensure user can only view messages they're involved in
    if (req.user.uid !== uid1 && req.user.uid !== uid2) {
      return res.status(403).json({ error: 'Unauthorized access' });
    }
    
    const msgs = await Message.find({
      $or: [
        { from: uid1, to: uid2 },
        { from: uid2, to: uid1 }
      ]
    }).sort({ createdAt: 1 });
    res.json(msgs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Get all users (public - no authentication required)
app.get('/api/users', async (req, res) => {
  try {
    const users = await User.find({}, {
      _id: 1,
      firstName: 1,
      profilePicture: 1,
      bio: 1,
      skills: 1,
      interests: 1,
      college: 1,
      year: 1,
      branch: 1,
      city: 1,
      isOnline: 1
    });
    res.json(users);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

// Test routes (public)
app.get('/api', (req, res) => {
  res.send('StudLyf Backend API is running!');
});

app.get('/api/root', (req, res) => {
  res.send('StudLyf Backend API is running! (root endpoint)');
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🌐 CORS enabled for origins: ${allowedOrigins.join(', ')}`);
});

module.exports = app;