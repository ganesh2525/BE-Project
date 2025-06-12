const mongoose = require('mongoose');

const videoSchema = new mongoose.Schema({
  video_url: String,
  email: String,
  hash: Array
});

module.exports = videoSchema;