
import cv2 as cv
from flask import Flask, render_template, Response

app = Flask(__name__)
def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=320,
    display_height=240,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def read_cam():
    cap = cv.VideoCapture(gstreamer_pipeline(flip_method=0), cv.CAP_GSTREAMER)

    w = cap.get(cv.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv.CAP_PROP_FPS)
    print('Src opened, %dx%d @ %d fps' % (w, h, fps))



    if cap.isOpened():
        while True:
            ret_val, img = cap.read()
            if not ret_val:
                break
            ret, buffer = cv.imencode('.jpg',img)
            frame = buffer.tobytes()
            cv.waitKey(1)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



    else:
        print("pipeline open failed")

    print("successfully exit")
    cap.release()



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(read_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
