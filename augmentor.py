import cv2
import numpy as np
import os
import random

class Augmentor:
    def __init__(self):
        self.augment_count = 10

    def augment_image(self, image_path, output_folder):
        img = cv2.imread(image_path)
        augmented_images = []
        
        for i in range(self.augment_count):
            aug_img = self.apply_random_transformation(img)
            aug_path = os.path.join(output_folder, f"{os.path.basename(image_path).split('.')[0]}_aug{i}.jpg")
            cv2.imwrite(aug_path, aug_img)
            augmented_images.append(aug_path)

        return augmented_images

    def apply_random_transformation(self, img):
        transformations = [
            self.rotate, self.add_noise, self.shift_perspective, self.adjust_hue
        ]
        return random.choice(transformations)(img)

    def rotate(self, img):
        angle = random.uniform(-25, 25)
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1)
        return cv2.warpAffine(img, M, (w, h))

    def add_noise(self, img):
        noise = np.random.randint(0, 50, img.shape, dtype=np.uint8)
        return cv2.add(img, noise)

    def shift_perspective(self, img):
        h, w = img.shape[:2]
        pts1 = np.float32([[0, 0], [w-1, 0], [0, h-1], [w-1, h-1]])
        shift = random.uniform(-20, 20)
        pts2 = np.float32([[shift, shift], [w-shift, shift], [shift, h-shift], [w-shift, h-shift]])
        M = cv2.getPerspectiveTransform(pts1, pts2)
        return cv2.warpPerspective(img, M, (w, h))

    def adjust_hue(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0] + random.randint(-10, 10)) % 180
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
