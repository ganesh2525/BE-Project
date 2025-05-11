Studio.post("/deletevideo/:videoId", async (req, res) => {
  try {
    const videoId = req.params.videoId;
    console.log(videoId);

    const refreshToken = req.cookies?.refreshToken;
    const accessToken = req.cookies?.accessToken;
    if (!refreshToken) {
      return res.status(401).json({
        message: "Unauthorized access, please login again",
      });
    }
    if (!accessToken) {
      const userID = verifyRefreshToken(refreshToken);
      const userData = { id: userID };
      const accessToken = generateAccessToken(userData);
      res.cookie("accessToken", accessToken, {
        httpOnly: false,
        sameSite: "None",
        secure: true,
        maxAge: 24 * 60 * 60 * 1000,
      });
    }
    
    const video = await videodata.findOne({ "VideoData._id": videoId });
    if (!video) {
      return res.status(404).json({ error: "Video not found" })
    }    

    const foundVideo = video.VideoData.find(v => v._id.toString() === videoId);
    if (!foundVideo) {
      return res.status(404).json({ message: "Video not found" });  
    }
    console.log(JSON.stringify(foundVideo, null, 2));
    const video_url = foundVideo.videoURL;
    const video_thumnail = foundVideo.imageURL;

    console.log(video_url)
    console.log(video_thumnail)

    await videodata.updateOne(
      { "VideoData._id": videoId },
      { $pull: { VideoData: { _id: videoId } } }
    );

    await TrendingData.deleteOne({ videoid: videoId });

    await userData.updateMany(
      { "thumbnails.imageURL": video_thumnail },
      { $pull: { thumbnails: { imageURL: video_thumnail } } }
    )

    await userData.updateMany(
      { "videos.videoURL": video_url },
      { $pull: { videos: { videoURL: video_url } } }
    )

    await userData.updateMany(
      { "likedVideos.likedVideoID": videoId },
      { $pull: { likedVideos: { likedVideoID: videoId } } }
    );

    await userData.updateMany(
      { "watchLater.savedVideoID": videoId },
      { $pull: { watchLater: { savedVideoID: videoId } } }
    );

    await userData.updateMany(
      { "Playlists.playlist_videos.videoID": videoId },
      { $pull: { "Playlists.$.playlist_videos": { videoID: videoId } } }
    );

    res.status(200).json({ message: "Video deleted successfully" });
  } catch (error) {
    console.error("Error deleting video:", error);  
    res.status(500).json({ error: "Internal server error" });
  }
});