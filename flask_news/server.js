import express from "express";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();
const app = express();

app.use(express.json());
app.use(cors({
  origin: "http://localhost:5173", // your frontend URL
  credentials: true,
}));

// --- Read admin emails from .env ---
const ADMIN_EMAILS = process.env.ADMIN_EMAILS
  ? process.env.ADMIN_EMAILS.split(",").map(e => e.trim())
  : [];

const PORT = process.env.PORT || 5001;

// ---------------------------------------------------------------------
// 🧩 1️⃣ ADMIN CHECK
// ---------------------------------------------------------------------
app.get("/is-admin", (req, res) => {
  const email = req.query.email;
  if (!email) return res.status(400).json({ isAdmin: false });
  const isAdmin = ADMIN_EMAILS.includes(email);
  res.json({ isAdmin });
});

// ---------------------------------------------------------------------
// 📅 2️⃣ EVENTS APIs
// ---------------------------------------------------------------------
let events = [
  {
    id: 1,
    title: "AI Hackathon 2025",
    date: "2025-11-20",
    location: "Hyderabad",
    description: "A hackathon for AI innovators.",
    image: "https://placehold.co/300x200",
  },
  {
    id: 2,
    title: "Tech Symposium",
    date: "2025-12-05",
    location: "GRIET College",
    description: "Discussing the latest in tech research.",
    image: "https://placehold.co/300x200",
  },
];

// ✅ Get all events
app.get("/events", (req, res) => {
  res.json({ events });
});

// ✅ Add event (admin only)
app.post("/events", (req, res) => {
  const { email, title, date, location, description, image } = req.body;
  if (!ADMIN_EMAILS.includes(email)) {
    return res.status(403).json({ error: "Not authorized" });
  }
  const newEvent = {
    id: events.length + 1,
    title,
    date,
    location,
    description,
    image,
  };
  events.push(newEvent);
  res.status(201).json({ message: "Event added", events });
});

// ✅ Delete event (admin only)
app.delete("/events/:id", (req, res) => {
  const { email } = req.query;
  const id = parseInt(req.params.id);
  if (!ADMIN_EMAILS.includes(email)) {
    return res.status(403).json({ error: "Not authorized" });
  }
  events = events.filter((e) => e.id !== id);
  res.json({ message: "Event deleted", events });
});

// ---------------------------------------------------------------------
// 🎓 3️⃣ FREE COURSES APIs
// ---------------------------------------------------------------------
let courseraCourses = [
  {
    id: 1,
    name: "Machine Learning Basics",
    description: "Introduction to ML concepts",
    tags: ["English", "AI"],
    image: "https://placehold.co/300x200",
    url: "https://coursera.org/learn/machine-learning",
  },
  {
    id: 2,
    name: "Data Science Fundamentals",
    description: "Learn data preprocessing and visualization",
    tags: ["Telugu", "Python"],
    image: "https://placehold.co/300x200",
    url: "https://coursera.org/learn/data-science",
  },
];

let youtubeCourses = [
  {
    id: 1,
    heading: "React Crash Course",
    description: "Learn React in one video",
    tags: ["JavaScript", "Frontend"],
    src_link: "https://www.youtube.com/embed/Dorf8i6lCuk",
  },
];

// ✅ Get Coursera courses
app.get("/free-courses", (req, res) => {
  res.json({ courses: courseraCourses });
});

// ✅ Get YouTube courses
app.get("/admin-courses", (req, res) => {
  res.json({ courses: youtubeCourses });
});

// ✅ Add YouTube course (admin only)
app.post("/admin-courses", (req, res) => {
  const { email, heading, description, tags, src_link } = req.body;
  if (!ADMIN_EMAILS.includes(email)) {
    return res.status(403).json({ error: "Not authorized" });
  }
  const newCourse = {
    id: youtubeCourses.length + 1,
    heading,
    description,
    tags,
    src_link,
  };
  youtubeCourses.push(newCourse);
  res.status(201).json({ message: "Course added", courses: youtubeCourses });
});

// ✅ Delete YouTube course (admin only)
app.delete("/admin-courses/:id", (req, res) => {
  const { email } = req.query;
  const id = parseInt(req.params.id);
  if (!ADMIN_EMAILS.includes(email)) {
    return res.status(403).json({ error: "Not authorized" });
  }
  youtubeCourses = youtubeCourses.filter((c) => c.id !== id);
  res.json({ message: "Course deleted", courses: youtubeCourses });
});

// ---------------------------------------------------------------------
// 🌐 4️⃣ STUDVERSE APIs (Example: Posts or Projects)
// ---------------------------------------------------------------------
let studversePosts = [
  {
    id: 1,
    author: "Sreeja Reddy",
    title: "AI Career Guide 2025",
    description: "Steps to achieve 70 LPA with Machine Learning mastery",
    category: "Career",
    date: "2025-10-10",
  },
  {
    id: 2,
    author: "Tech Student",
    title: "Building a Chat App with Flask & React",
    description: "Complete architecture and deployment guide",
    category: "Development",
    date: "2025-09-28",
  },
];

// ✅ Get all posts
app.get("/studverse", (req, res) => {
  res.json({ posts: studversePosts });
});

// ✅ Add new post (admin only)
app.post("/studverse", (req, res) => {
  const { email, author, title, description, category } = req.body;
  if (!ADMIN_EMAILS.includes(email)) {
    return res.status(403).json({ error: "Not authorized" });
  }
  const newPost = {
    id: studversePosts.length + 1,
    author,
    title,
    description,
    category,
    date: new Date().toISOString().split("T")[0],
  };
  studversePosts.push(newPost);
  res.status(201).json({ message: "Post added", posts: studversePosts });
});

// ✅ Delete post (admin only)
app.delete("/studverse/:id", (req, res) => {
  const { email } = req.query;
  const id = parseInt(req.params.id);
  if (!ADMIN_EMAILS.includes(email)) {
    return res.status(403).json({ error: "Not authorized" });
  }
  studversePosts = studversePosts.filter((p) => p.id !== id);
  res.json({ message: "Post deleted", posts: studversePosts });
});

// ---------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`✅ Server running on port ${PORT}`);
});
