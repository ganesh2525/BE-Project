import { initializeApp } from "firebase/app";
import { getStorage, ref, deleteObject } from "firebase/storage";
import { MongoClient } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

// Firebase Config
const firebaseConfig = {
  apiKey: "AIzaSyB9NomQPgAoQ6B1c64XhN3ahqN0U1Fe3YU",
  authDomain: "mern-df125.firebaseapp.com",
  projectId: "mern-df125",
  storageBucket: "mern-df125.appspot.com",
  messagingSenderId: "757150184874",
  appId: "1:757150184874:web:16b30a921277ea328527d3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const storage = getStorage(app);

// MongoDB Connection
const uri = "mongodb+srv://ganesh_93:ganesh93@mern.kq359yn.mongodb.net"; // Replace with your URI
const client = new MongoClient(uri);

const extractFirebasePath = (url) => {
  try {
    const decoded = decodeURIComponent(url);
    const match = decoded.match(/\/o\/(.+)\?alt/);
    return match ? match[1] : null;
  } catch {
    return null;
  }
};

const deleteImagesFromFirebase = async () => {
  try {
    await client.connect();
    const db = client.db("YouTube");
    const collection = db.collection("userdatas");

    const allDocs = await collection.find({}).toArray();

    for (const doc of allDocs) {
      const videos = doc.videos || [];
      for (const video of videos) {
        const firebasePath = extractFirebasePath(video.videoURL);
        if (firebasePath) {
          const fileRef = ref(storage, firebasePath);
          try {
            await deleteObject(fileRef);
            console.log(`✅ Deleted: ${firebasePath}`);
          } catch (err) {
            console.error(`❌ Error deleting ${firebasePath}:`, err.message);
          }
        }
      }
    }
  } catch (err) {
    console.error("MongoDB or Firebase error:", err);
  } finally {
    await client.close();
  }
};

deleteImagesFromFirebase();
