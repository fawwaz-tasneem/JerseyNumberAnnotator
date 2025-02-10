import os

class ImageLoader:
    def __init__(self):
        self.image_list = []
        self.index = 0

    def load_images(self, folder):
        self.image_list = sorted([os.path.join(folder, img) for img in os.listdir(folder) if img.endswith(('.png', '.jpg', '.jpeg'))])
        self.index = 0

    def get_current_image(self):
        if self.image_list:
            return self.image_list[self.index]
        return None

    def next_image(self):
        if self.image_list and self.index < len(self.image_list) - 1:
            self.index += 1

    def prev_image(self):
        if self.image_list and self.index > 0:
            self.index -= 1
