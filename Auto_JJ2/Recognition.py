import numpy as np
import win32gui
import cv2
import os
import io

min_confidence = 0.3
nm_threshold = 0.1  # 数值越小精度越高
weightsPath = os.path.sep.join(['weights', "cards.weights"])
configPath = os.path.sep.join(['weights', "cards.cfg"])
LABELS = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2', 'X', 'D']

COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)


def yolo_detect(image):  # 0 检测所有,1:只检查牌,2:检查状态
    class_list = []
    cen_list = []
    c_list = []
    pos_list = []
    (H, W) = image.shape[:2]

    ln = net.getLayerNames()

    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
    # ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)
    boxes = []
    positions = []
    confidences = []
    classIDs = []

    for output in layerOutputs:

        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > min_confidence:
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    idxs = cv2.dnn.NMSBoxes(boxes, confidences, min_confidence, nm_threshold)

    if len(idxs) > 0:
        for i in idxs.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 3)
            position = [x + w / 2, y + h / 2]
            positions.append(position)
            text = "{}".format(LABELS[classIDs[i]])
            cv2.putText(image, text, (x, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            if LABELS[classIDs[i]] == '10':
                LABELS[classIDs[i]] = "T"

            class_list.append(LABELS[classIDs[i]])
            cen_list.append(position)
            c_list.append(position[0])
            pos_list.append([x, y, w, h])

    try:
        _, class_list, pos_list = (list(t) for t in zip(*sorted(zip(c_list, class_list, pos_list), reverse=False)))
        return image, class_list, pos_list
    except:
        return image, None, None