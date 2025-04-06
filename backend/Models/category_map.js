const mongoose = require('mongoose');

const videoCategorySchema = new mongoose.Schema(
  {
    categories: {
      type: Map,
      of: [String]
    },
  },
  { timestamps: true }
);

const VideoCategory = mongoose.model('VideoCategory', videoCategorySchema);

module.exports = VideoCategory;