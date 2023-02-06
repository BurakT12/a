#!/usr/bin/python3
##################################

import time,board,busio
import numpy as np
import adafruit_mlx90640
import datetime as dt
import cv2
from flask import Flask, render_template, Response

#flask
app = Flask(__name__)



i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) # setup I2C
mlx = adafruit_mlx90640.MLX90640(i2c) # begin MLX90640 with I2C comm
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ # 16Hz is noisy

mlx_shape = (24,32)
tframe = np.zeros((24*32,)) # setup array for storing all 768 temperatures

def td_to_img(f,tmax,tmin):
    norm = np.uint8((f - tmin)*255/(tmax-tmin))
    return norm

time.sleep(2)
t0 = time.time()

try:
    while True:
        # waiting for data frame
        mlx.getFrame(tframe) # read MLX temperatures into frame var
        t_img = (np.reshape(tframe,mlx_shape)) # reshape to 24x32
        tmax = tframe.max()
        tmin = tframe.min()
        ta_img = td_to_img(t_img, tmax, tmin)
        # np.fliplr(ta_img)

        # Image processing
        img = cv2.applyColorMap(ta_img, cv2.COLORMAP_JET)
        
        if has_cuda:
            # Use the CUDA
            img = cv2.cuda.resize(img, (640, 480), interpolation=cv2.INTER_CUBIC)
        else:
            # Use the CPU
            img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_CUBIC)
        # img = cv2.flip(img, 1)

        text = 'Tmin = {:+.1f} Tmax = {:+.1f} FPS = {:.2f}'.format(tmin, tmax, 1/(time.time() - t0))
        cv2.putText(img, text, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

        # stream on web
        ret, buffer = cv.imencode(.jpg ,img)
        frame = buffer.tobtes()
        cv.waitKey(1)

        # if 's' is pressed - saving of picture
       """ key = cv2.waitKey(1) & 0xFF
        if key == ord("s"):
            fname = 'pic_' + dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.jpg'
            cv2.imwrite(fname, img)
            print('Saving image ', fname)
        if key == ord("q"):
            break
        t0 = time.time()"""

except KeyboardInterrupt:
    # to terminate the cycle
    
    print(' Stopped')






@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(read_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
