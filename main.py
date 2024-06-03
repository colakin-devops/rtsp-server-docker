# #!/usr/bin/env python

# import os
# import gi

# gi.require_version('Gst', '1.0')
# gi.require_version('GstRtspServer', '1.0')
# from gi.repository import Gst, GstRtspServer, GObject, GLib

# loop = GLib.MainLoop()
# Gst.init(None)

# class TestRtspMediaFactory(GstRtspServer.RTSPMediaFactory):
#     def __init__(self):
#         GstRtspServer.RTSPMediaFactory.__init__(self)

#     def do_create_element(self, url):
#         # set mp4 file path to filesrc's location property
#         src_demux = "filesrc location=videos/{} ! qtdemux name=demux".format(src_file)
#         h264_transcode = "demux.video_0"
#         # uncomment following line if video transcoding is necessary
#         # h264_transcode = "demux.video_0 ! decodebin ! queue ! x264enc"
#         pipeline = "{} {} ! queue ! rtph264pay name=pay0 config-interval=1 pt=96".format(src_demux, h264_transcode)
#         print("Element created: " + pipeline)
#         return Gst.parse_launch(pipeline)

# class GstreamerRtspServer():
#     def __init__(self):
#         self.rtspServer = GstRtspServer.RTSPServer()
#         self.rtspServer.set_service("8554")  # Change port to 8554
#         factory = TestRtspMediaFactory()
#         factory.set_shared(True)
#         mountPoints = self.rtspServer.get_mount_points()
#         mountPoints.add_factory('/{}'.format(dst_stream), factory)
#         self.rtspServer.attach(None)
#         print("RTSP Server attached on port 8554")

# if __name__ == '__main__':
#     try:
#         src_file = os.environ['MP4_FILENAME']
#         dst_stream = os.environ['DST_STREAM']
#     except KeyError as e:
#         print(f"Environment variable {e} not set")
#         exit(1)

#     s = GstreamerRtspServer()
#     print(f"Streaming {src_file} to rtsp://localhost:8554/{dst_stream}")
#     loop.run()


#!/usr/bin/env python

import os
import gi
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject, GLib

loop = GLib.MainLoop()
Gst.init(None)

class TestRtspMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self):
        GstRtspServer.RTSPMediaFactory.__init__(self)

    def do_create_element(self, url):
        print("Received URL:", url)  # Print the received URL
        
        if isinstance(url, GstRtspServer.RTSPUrl):
            # Extract the path and query parameters from the RTSPUrl object
            path = url.get_request_uri()
            query_string = url.get_query()
        else:
            print("Error: Invalid URL object type")
            return None

        # Extract the src_file parameter from the query string
        query_params = query_string.split('&')
        src_file = None
        for param in query_params:
            key, value = param.split('=')
            if key == 'src_file':
                src_file = value
                break

        if src_file is None:
            print("Error: src_file parameter not found in the URL")
            return None

        # Set mp4 file path to filesrc's location property
        src_demux = f"filesrc location=videos/{src_file} ! qtdemux name=demux"
        h264_transcode = "demux.video_0"
        # Uncomment the following line if video transcoding is necessary
        # h264_transcode = "demux.video_0 ! decodebin ! queue ! x264enc"
        pipeline = f"{src_demux} {h264_transcode} ! queue ! rtph264pay name=pay0 config-interval=1 pt=96"
        print("Element created:", pipeline)
        return Gst.parse_launch(pipeline)

class GstreamerRtspServer():
    def __init__(self):
        self.rtspServer = GstRtspServer.RTSPServer()
        self.rtspServer.set_service("8554")  # Change port to 8554
        factory = TestRtspMediaFactory()
        factory.set_shared(True)
        mountPoints = self.rtspServer.get_mount_points()
        mountPoints.add_factory('/stream1', factory)  # Hardcoded mount point for now
        self.rtspServer.attach(None)
        print("RTSP Server attached on port 8554")

app = FastAPI()

class VideoRequest(BaseModel):
    video_name: str

@app.get("/stream/")
async def stream_video(video_req: VideoRequest):
    video_name = video_req.video_name
    print(f"Received request to stream video: {video_req}")
    video_path = f"videos/{video_name}"
    
    # Check if the video file exists
    if not os.path.isfile(video_path):
        raise HTTPException(status_code=404, detail=f"Video file '{video_name}' not found")

    # Create an RTSP URL for the requested video
    rtsp_url = create_rtsp_stream(video_name)
    
    return {"rtsp_url": rtsp_url}

def create_rtsp_stream(video_name: str) -> str:
    try:
        # Make a request to the RTSP server to create an RTSP stream for the requested video
        response = requests.post("http://localhost:8554/create_stream/", json={"video_name": video_name})
        response.raise_for_status()
        rtsp_url = response.json()["rtsp_url"]
        return rtsp_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create RTSP stream for '{video_name}': {e}")

if __name__ == '__main__':
    s = GstreamerRtspServer()
    print("RTSP server ready")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    print("HTTP server ready")
    loop.run()
