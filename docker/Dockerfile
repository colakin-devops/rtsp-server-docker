FROM python:3

WORKDIR /rtsp-server/

RUN apt update && \
    apt -y install \
    libgirepository1.0-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gir1.2-gst-rtsp-server-1.0

RUN pip install pycairo PyGObject requests fastapi uvicorn

COPY . .

EXPOSE 8000 8554

ENV MP4_FILENAME=workout.mp4
ENV DST_STREAM=stream1

CMD ["python", "main.py"]
