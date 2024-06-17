import cv2
import ffmpeg
import numpy as np
import subprocess
import time
from datetime import datetime
import time

def send_image_to_server(imgPath):
    try:
        subprocess.run(['scp', imgPath,'root@kattila.cafe:~/kahvikamera/static/images/'], capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f'An error occured: {str(e)}')

# Whitebalances outgoing image, writes image to 'kahvi.jpg'
def publication_postprocess(img):
    
    # Whitebalancing
    wb = cv2.xphoto.createSimpleWB()
    outboundImg = wb.balanceWhite(img)

    # Add timestamp
    font = cv2.FONT_HERSHEY_SIMPLEX
    t = time.strftime('%H:%M:%S')
    outboundImg = cv2.putText(outboundImg, t, (10,460), font, 2, (255,255,255), 5)

    # Lastly write to disk (outgoing file)
    cv2.imwrite('kahvi.jpg', outboundImg)


# Mean square error
def mse(img1, img2):
    s = time.time()
    h, w = img1.shape
    diff = img1 - img2
    err = np.sum(diff**2)
    ops = 3*h*w
    mse = err/(float(h*w))
    t = time.time() - s
    print(ops, t, ops/t*10**12)
    return mse


def capture_camera():
    # TODO capture longer exposed image for less noise (all my homies hate noise)
    # Ehdotettu yhdistää useamman capturen keskiarvo joka kyllä denoisee sen
    try:
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            raise IOError("Cannot open webcam")

        ret, capImg = cap.read()

    finally:
        cap.release()

    return capImg


def retrieve_old_img(path):
    img = cv2.imread(path)
    return img

def cv_preprocess(raw):
    cvImg = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    return cvImg

def preprocess_capture(img):
    cv2.xphoto.dctDenoising(img, img, 8.0)
    return img


def main():
    while True:
        try:
            newImg = preprocess_capture(capture_camera())
            oldImg = retrieve_old_img("kahvi-local.jpg")

            cvNew = cv_preprocess(newImg)
            cvOld = cv_preprocess(oldImg)

            difference = mse(cvNew, cvOld)

            print(f'MSE: {difference}')
            if (difference > 5):
                print("MSE yli 5, Kahvin tila muuttunut! Laitetaan uusi kuva.")
                cv2.imwrite('kahvi-local.jpg', newImg)
                publication_postprocess(newImg)
                send_image_to_server('kahvi.jpg')
            else:
                print("Kahvin tila ei muuttunut. ei tehdä mitään.")

        except Exception as ex:
            print(ex)

        finally:
            time.sleep(5)

if __name__ == '__main__':
    main()