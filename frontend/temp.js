const cloudinary = require('cloudinary').v2;

cloudinary.config({
  cloud_name: 'dp3f23esu',
  api_key: '984276437213365',
  api_secret: 'YdX3GZz4GFBlIO4lfLywzDR9a6E',
});

const getPublicId = (url) => {
  const parts = url.split('/');
  const fileWithExt = parts[parts.length - 1];
  const publicId = fileWithExt.substring(0, fileWithExt.lastIndexOf('.'));
  return publicId;
};

const deleteFile = async (url) => {
  const publicId = getPublicId(url);
  try {
    const result = await cloudinary.uploader.destroy(publicId);
    console.log('Deleted:', result);
  } catch (error) {
    console.error('Error deleting file:', error);
  }
};

// Example usage
deleteFile();
