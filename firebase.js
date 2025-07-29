const admin = require("firebase-admin");
const fs = require("fs");
require("dotenv").config({ path: require("path").join(__dirname, "api", ".env") });

// Read service account key from environment variable
const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

module.exports = admin;