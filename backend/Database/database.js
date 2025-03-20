require("dotenv").config()
const mongoose = require("mongoose");

mongoose
  .connect(
    `mongodb+srv://${process.env.DB_user}:${process.env.DB_password}@mern.kq359yn.mongodb.net/${process.env.DB_name}?retryWrites=true&w=majority`,
    {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    }
  )
  .then(() => console.log("Connected")) //If connected to DB
  .catch((err) => console.log(err)); //If not connected to DB