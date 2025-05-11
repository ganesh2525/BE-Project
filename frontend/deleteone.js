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

const extractFirebasePath = (url) => {
    try {
      const decoded = decodeURIComponent(url);
      const match = decoded.match(/\/o\/(.+)\?alt/);
      return match ? match[1] : null;
    } catch {
      return null;
    }
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const storage = getStorage(app);

const testDelete = async () => {
    const testUrl = "https://firebasestorage.googleapis.com/v0/b/mern-df125.appspot.com/o/profile%2FUCO_Statement.png?alt=media&token=118a53ab-249e-49b4-8de0-dbd2dd14b8f2";
    const firebasePath = extractFirebasePath(testUrl);
    if (firebasePath) {
      const fileRef = ref(storage, firebasePath);
      try {
        await deleteObject(fileRef);
        console.log(`✅ Deleted: ${firebasePath}`);
      } catch (err) {
        console.error(`❌ Error deleting ${firebasePath}:`, err.message);
      }
    }
  };
  
  testDelete();