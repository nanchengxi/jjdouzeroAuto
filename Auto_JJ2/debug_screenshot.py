import GameHelper as gh
from GameHelper import GameHelper
import cv2
import numpy as np

helper = GameHelper()
# img = cv2.imread("2.png")
img = helper.Screenshot()
# img = cv2.cvtColor(np.asarray(img), cv2.COLOR_BGR2RGB)
img = gh.DrawRectWithText(img, (30, 460, 1200, 200), "test")

gh.ShowImg(img)


