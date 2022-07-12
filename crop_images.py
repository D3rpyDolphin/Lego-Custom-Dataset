# I messed up the folder hierarchy for image classification

from options import Options
import xml.etree.ElementTree as ET
import shutil
import os
import re

def get_image_colors(dir, img_name):
    name = os.path.join(dir, "annotations", '{}.xml'.format(img_name))
    tree = ET.parse(name)
    root = tree.getroot()
    return [obj[1].text for obj in root.findall('object')]

def move_cropped_images(dir):
    image_dir = os.path.join(dir, "images")
    cropped_image_output_dir = os.path.join(dir, "cropped images")

    # Go through images and move them to correct subfolder
    name_format = re.compile(r'(\d+)_(\d).jpg') # Current format is image-name_i.jpg
    for cropped_image in os.listdir(cropped_image_output_dir):
        if (name_format.match(cropped_image)):
            prev_dir = os.path.join(cropped_image_output_dir, cropped_image)

            search_results = name_format.search(cropped_image)
            orig_img_name = search_results.group(1)
            colors = get_image_colors(dir, orig_img_name)
            index = int(search_results.group(2))
            color = colors[index] 

            end_dir = os.path.join(cropped_image_output_dir, color) # Move to folder named by color

            print("Moving lego {} with color {} from {} to {}".format(orig_img_name, color, prev_dir, end_dir))

            if not os.path.exists(end_dir):
                os.makedirs(end_dir)
            os.rename(prev_dir, os.path.join(end_dir, cropped_image))

move_cropped_images(os.path.join(Options.project_dir, "training data"))
move_cropped_images(os.path.join(Options.project_dir, "testing data"))