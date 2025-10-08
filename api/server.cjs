require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const http = require('http');
const { Server } = require('socket.io');
const authenticate = require('../middleware/authenticate');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const Message = require('../models/Message');

const app = express();

// Middleware
const allowedOrigins = [
  'http://localhost:8080',
  'http://localhost:5173',
  'http://127.0.0.1:8080',
  'http://127.0.0.1:5173',
  'https://studlyf.in',
  'https://www.studlyf.in',
];

app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);
    
    console.log('Request from origin:', origin);
    
    const localhostRegex = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;
    if (allowedOrigins.indexOf(origin) !== -1 || localhostRegex.test(origin)) {
      console.log('Origin allowed:', origin);
      callback(null, true);
    } else {
      console.log('Blocked origin:', origin);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With', 'Accept'],
  optionsSuccessStatus: 200
}));

app.use(express.json({ limit: '20kb' }));

// Handle preflight requests
app.options('*', cors());

// simple disk storage for images
const uploadDir = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
const certDir = path.join(uploadDir, 'certificates');
if (!fs.existsSync(certDir)) fs.mkdirSync(certDir, { recursive: true });
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname || '');
    const name = `${Date.now()}-${Math.random().toString(36).slice(2)}${ext}`;
    cb(null, name);
  }
});
const upload = multer({
  storage,
  limits: { fileSize: 15 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    // Accept common images and general files; basic sanity check
    const allowed = [
      'image/',
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'application/zip',
      'application/x-zip-compressed'
    ];
    if (file.mimetype.startsWith('image/') || allowed.includes(file.mimetype)) return cb(null, true);
    cb(null, true); // allow others by default
  }
});
// serve uploaded files
app.use('/uploads', express.static(uploadDir));

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
  projects: [{
    githubUrl: String,
    liveUrl: String,
    youtubeUrl: String,
    description: String,
  }],
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

const User = mongoose.models.Users || mongoose.model('User', userSchema);

// Connection Schema
const connectionSchema = new mongoose.Schema({
  fromUid: { type: String, required: true },
  toUid: { type: String, required: true }
}, { timestamps: true });

const Connection = mongoose.models.Connection || mongoose.model('Connection', connectionSchema);

// Use centralized Message model (with type/read/media fields)
const MessageModel = Message;

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
      user = new User({ 
        uid, 
        name, 
        email, 
        photoURL, 
        _id: uid,
        createdAt: new Date(),
        updatedAt: new Date()
      });
      await user.save();
    }
    res.json(user);
  } catch (err) {
    console.error('Error creating user:', err);
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
    
    const msg = await MessageModel.create({ from, to, text, type: 'text', read: false });
    // emit socket events to recipient and sender
    try {
      if (io) {
        io.to(to).emit('message:new', {
          _id: String(msg._id),
          from,
          to,
          text,
          read: false,
          createdAt: msg.createdAt,
        });
        io.to(from).emit('message:sent', {
          _id: String(msg._id),
          from,
          to,
          text,
          read: false,
          createdAt: msg.createdAt,
        });
      }
    } catch (e) {
      // best-effort emit
    }
    res.json(msg);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Send an image message (protected)
app.post('/api/messages/send-image', authenticate, upload.single('image'), async (req, res) => {
  try {
    const { from, to } = req.body;
    if (!from || !to) return res.status(400).json({ error: 'Missing from or to' });
    if (req.user.uid !== from) return res.status(403).json({ error: 'Unauthorized access' });
    if (!req.file) return res.status(400).json({ error: 'No image uploaded' });
    const base = `${req.protocol}://${req.get('host')}`;
    const mediaUrl = `${base}/uploads/${req.file.filename}`;
    const msg = await MessageModel.create({ from, to, type: 'image', mediaUrl, mediaType: req.file.mimetype, read: false });
    try {
      if (io) {
        io.to(to).emit('message:new', { _id: String(msg._id), from, to, type: 'image', mediaUrl, mediaType: req.file.mimetype, read: false, createdAt: msg.createdAt });
        io.to(from).emit('message:sent', { _id: String(msg._id), from, to, type: 'image', mediaUrl, mediaType: req.file.mimetype, read: false, createdAt: msg.createdAt });
      }
    } catch (e) {}
    res.json(msg);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Send a generic file message (protected)
app.post('/api/messages/send-file', authenticate, upload.single('file'), async (req, res) => {
  try {
    const { from, to } = req.body;
    if (!from || !to) return res.status(400).json({ error: 'Missing from or to' });
    if (req.user.uid !== from) return res.status(403).json({ error: 'Unauthorized access' });
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' });
    const base = `${req.protocol}://${req.get('host')}`;
    const mediaUrl = `${base}/uploads/${req.file.filename}`;
    const payload = {
      from,
      to,
      type: 'file',
      mediaUrl,
      mediaType: req.file.mimetype,
      fileName: req.file.originalname || req.file.filename,
      fileSize: req.file.size,
      read: false
    };
    const msg = await MessageModel.create(payload);
    try {
      if (io) {
        const emitPayload = { _id: String(msg._id), ...payload, createdAt: msg.createdAt };
        io.to(to).emit('message:new', emitPayload);
        io.to(from).emit('message:sent', emitPayload);
      }
    } catch (e) {}
    res.json(msg);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Forward message (protected)
app.post('/api/messages/forward', authenticate, async (req, res) => {
  try {
    const { from, to, messageId } = req.body;
    if (!from || !to || !messageId) return res.status(400).json({ error: 'Missing from, to, or messageId' });
    if (req.user.uid !== from) return res.status(403).json({ error: 'Unauthorized access' });
    const original = await MessageModel.findById(messageId);
    if (!original) return res.status(404).json({ error: 'Original message not found' });
    const payload = {
      from,
      to,
      type: original.type,
      text: original.type === 'text' ? original.text : undefined,
      mediaUrl: original.type === 'image' ? original.mediaUrl : undefined,
      mediaType: original.type === 'image' ? original.mediaType : undefined,
      forwardOf: String(original._id),
      read: false,
    };
    const msg = await MessageModel.create(payload);
    try {
      if (io) {
        io.to(to).emit('message:new', { ...payload, _id: String(msg._id), createdAt: msg.createdAt });
        io.to(from).emit('message:sent', { ...payload, _id: String(msg._id), createdAt: msg.createdAt });
      }
    } catch (e) {}
    res.json(msg);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Upload a certificate image for profile (protected)
app.post('/api/profile/certificates/upload', authenticate, upload.single('image'), async (req, res) => {
  try {
    const { uid } = req.user;
    if (!req.file) return res.status(400).json({ error: 'No image uploaded' });
    const base = `${req.protocol}://${req.get('host')}`;
    const mediaUrl = `${base}/uploads/${req.file.filename}`;
    res.json({ url: mediaUrl, name: req.file.originalname || 'certificate' });
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
    
    const msgs = await MessageModel.find({
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

// Get unread counts grouped by peer for current user (protected)
app.get('/api/messages/unread-counts/:uid', authenticate, async (req, res) => {
  try {
    const { uid } = req.params;
    if (req.user.uid !== uid) return res.status(403).json({ error: 'Unauthorized access' });
    const pipeline = [
      { $match: { to: uid, read: false } },
      { $group: { _id: '$from', count: { $sum: 1 } } }
    ];
    const agg = await MessageModel.aggregate(pipeline);
    const counts = {};
    agg.forEach(doc => { counts[doc._id] = doc.count; });
    res.json(counts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Mark messages from peer as read for current user (protected)
app.patch('/api/messages/:peerId/read', authenticate, async (req, res) => {
  try {
    const peerId = req.params.peerId;
    const currentUid = req.user.uid;
    const result = await MessageModel.updateMany({ from: peerId, to: currentUid, read: false }, { $set: { read: true } });
    // notify peer and current user
    try {
      if (io) {
        io.to(peerId).emit('message:read', { by: currentUid, peer: peerId });
        io.to(currentUid).emit('message:read', { by: currentUid, peer: peerId });
      }
    } catch (e) {}
    res.json({ modified: result.modifiedCount || 0 });
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

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    cors: {
      allowedOrigins: allowedOrigins
    }
  });
});

// Socket.IO setup (only when running as a standalone server)
let io = null;
let server = null;
if (!process.env.VERCEL) {
  server = http.createServer(app);
  io = new Server(server, {
    cors: { origin: allowedOrigins, credentials: true }
  });

  // Simple auth: client provides uid via query; join personal room
  io.on('connection', (socket) => {
    const uid = socket.handshake.auth?.uid || socket.handshake.query?.uid;
    if (uid) {
      socket.join(String(uid));
    }
    socket.on('disconnect', () => {});
  });

  const PORT = process.env.PORT || 3000;
  server.listen(PORT, () => {
    console.log(`Server running in the port ${PORT}`);
    console.log(`CORS enabled for origins: ${allowedOrigins.join(', ')}`);
  });
}

module.exports = app;