const mongoose = require("mongoose");

const messageSchema = new mongoose.Schema({
  from: { type: String, required: true },
  to: { type: String, required: true },
  text: { type: String },
  type: { type: String, enum: ['text', 'image'], default: 'text' },
  mediaUrl: { type: String },
  mediaType: { type: String },
  forwardOf: { type: String }, // original message id (optional)
  read: { type: Boolean, default: false },
  createdAt: { type: Date, default: Date.now, expires: 86400 }
}, { collection: 'messages' });

module.exports = mongoose.model("Message", messageSchema);