const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "api", ".env") });

const admin = require("firebase-admin");

const serviceAccount = JSON.parse(
  Buffer.from(process.env.FIREBASE_SERVICE_ACCOUNT_BASE64, "base64").toString("utf8")
);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

module.exports = admin;
