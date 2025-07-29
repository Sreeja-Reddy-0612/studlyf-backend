const mongoose = require("mongoose");

const connectionSchema = new mongoose.Schema({
  fromUid: { type: String, required: true },
  toUid: { type: String, required: true }
}, { timestamps: true });

module.exports = mongoose.model("Connection", connectionSchema); 