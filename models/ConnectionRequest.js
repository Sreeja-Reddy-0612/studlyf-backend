const mongoose = require("mongoose");

const connectionRequestSchema = new mongoose.Schema({
  from: { type: String, required: true },
  to: { type: String, required: true },
  createdAt: { type: Date, default: Date.now, expires: 86400 }
}, { collection: 'connection_requests' });

module.exports = mongoose.model("ConnectionRequest", connectionRequestSchema); 