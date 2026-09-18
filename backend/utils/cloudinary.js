const cloudinary = require('cloudinary').v2;
require('dotenv').config();

cloudinary.config({
  cloud_name: process.env.CLOUD_NAME,
  api_key: process.env.CLOUD_API_KEY,
  api_secret: process.env.CLOUD_API_SECRET,
});

// Utility to extract public_id from Cloudinary URL
const getPublicIdFromUrl = (url) => {
  const urlObj = new URL(url);
  const parts = urlObj.pathname.split('/');
  const uploadIndex = parts.indexOf('upload');
  const publicIdParts = parts.slice(uploadIndex + 1); // e.g., ['v174...', 'folder', 'filename.ext']
  if (publicIdParts[0].startsWith('v')) publicIdParts.shift(); // remove version if present
  const filename = publicIdParts.pop().split('.')[0]; // remove extension
  return [...publicIdParts, filename].join('/');
};

// Delete video
const deleteVideoByUrl = async (videoUrl) => {
  const publicId = getPublicIdFromUrl(videoUrl);
  try {
    const result = await cloudinary.uploader.destroy(publicId, {
      resource_type: "video"
    });
    console.log("Deleted video:", result);
    return result;
  } catch (error) {
    console.error("Video deletion failed:", error);
    throw error;
  }
};

// Delete image
const deleteImageByUrl = async (imageUrl) => {
  const publicId = getPublicIdFromUrl(imageUrl);
  try {
    const result = await cloudinary.uploader.destroy(publicId, {
      resource_type: "image"
    });
    console.log("Deleted image:", result);
    return result;
  } catch (error) {
    console.error("Image deletion failed:", error);
    throw error;
  }
};

module.exports = {
  deleteVideoByUrl,
  deleteImageByUrl
};