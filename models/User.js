const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
  _id: { type: String, required: true }, // Use Firebase UID as _id
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

module.exports = mongoose.model("User", userSchema); 