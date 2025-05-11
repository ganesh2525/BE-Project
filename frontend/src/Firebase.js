import { initializeApp } from "firebase/app";
import { getStorage} from 'firebase/storage';
import {getFirestore} from "firebase/firestore"

// const firebaseConfig = {
//   apiKey: "AIzaSyB9NomQPgAoQ6B1c64XhN3ahqN0U1Fe3YU",
//   authDomain: "mern-df125.firebaseapp.com",
//   projectId: "mern-df125",
//   storageBucket: "mern-df125.appspot.com",
//   messagingSenderId: "757150184874",
//   appId: "1:757150184874:web:16b30a921277ea328527d3"
// };

const firebaseConfig = {
  apiKey: "AIzaSyA-SUWV5CECPMFLCcJ9esPjX3_B12t7WFU",
  authDomain: "chatapp-d6e38.firebaseapp.com",
  projectId: "chatapp-d6e38",
  storageBucket: "chatapp-d6e38.firebasestorage.app",
  messagingSenderId: "64164417705",
  appId: "1:64164417705:web:09ff2f056150c13a6b19b8",
  measurementId: "G-T3H71MMQNF"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const storage = getStorage(app)
export const db = getFirestore(app)


