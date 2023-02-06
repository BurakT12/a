
import cv2 as cv
from flask import Flask, render_template, Response



net = cv.dnn.readNet("yolov4-tiny-custom_best.weights", "yolov4-tiny-custom.cfg")
net.setPreferableBackend(cv.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CUDA)
classes = []
with open("obj.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))





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
            font1 = cv.FONT_HERSHEY_SIMPLEX
            cv.putText(fps, "FPS: {:.2f}".format(fps), (10, 30), font1, 1, (255, 255, 255), 2, cv.LINE_AA)
            ##########################
            img = cv.resize(img, None, fx=1, fy=1)
            height, width, channels = img.shape
            blob = cv.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            net.setInput(blob)
            outs = net.forward(output_layers)
            class_ids = []
            confidences = []
            boxes = []
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    if confidence > 0.5:
                        # Object detected
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        # Rectangle coordinates
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
                        class_ids.append(class_id)
            
            indexes = cv.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            font = cv.FONT_HERSHEY_PLAIN
            for i in range(len(boxes)):
                if i in indexes:
                    x, y, w, h = boxes[i]
                    label = str(classes[class_ids[i]])
                    color = colors[0]
                    cv.rectangle(img, (x, y), (x + w, y + h), color, 2)
                    cv.putText(img, label, (x, y + 30), font, 3, color, 3)
            ########################
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



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
