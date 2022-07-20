from __future__ import annotations

import sys
sys.path.append(r"C:\users\jared\appdata\local\programs\python\python310\lib\site-packages") # Only way I could find to use other libraries

import math
import bpy
import os
import random

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from PIL import Image

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import export_data
import scene_manager
import options
import ldraw_import

# Hacky way to import python files in blender
from importlib import reload
reload(ldraw_import)
reload(export_data)
reload(scene_manager)
reload(options)
    
from export_data import export_metadata
import scene_manager
from options import Options

scene = bpy.context.scene

def get_last_index(dir):
    files = [os.path.join(dir, f) for f in os.listdir(dir)]
    if (len(files) > 0):
        return int(max(files, key=os.path.getctime).split('\\')[-1].split('.')[0])
    else:
        return -1

def find_bounding_box(lego, count_outside_frame=True):
    w = Options.img_size[0]
    h = Options.img_size[1]
    bpy.context.view_layer.update()
    mat = lego.ob.matrix_world
    world_bb_vertices = [mat @ Vector(v) for v in lego.ob.bound_box]

    if world_bb_vertices[0].z > -0.5: # don't count objects that get flinged from poor spawn locations
        co_2d = [world_to_camera_view(scene, scene.camera, v) for v in world_bb_vertices]
        xs, ys, _ = zip(*co_2d) # reformat coords

        xmin = int(   min(xs)  * w)
        ymin = int((1-max(ys)) * h)
        xmax = int(   max(xs)  * w)
        ymax = int((1-min(ys)) * h)
        box = (xmin, ymin, xmax, ymax)

        if count_outside_frame:
            # check if the object is outside of the image frame
            outside_frame = False
            for i, p in enumerate(box): 
                if p < 0 or p > Options.img_size[i % 2]:
                    outside_frame = True
            
            if outside_frame is False:
                return box
        else:
           return box

def crop_image(image_path, box):
    pil_image = Image.open(image_path)
    return pil_image.crop(box)

def save_image(image, name, color, dir):
    output_dir = os.path.join(dir, color) # Save in folder called the correct color
    
    if not os.path.exists(output_dir): # Create folder if needed
        os.makedirs(output_dir)

    image.save(os.path.join(output_dir, name), optimize=True, quality=100)

def generate_data(legos_to_sample, total_images, legos_per_img, batch_size, output_dir, continue_training=False):
    image_output_dir = os.path.join(output_dir, "images")
    cropped_image_output_dir = os.path.join(output_dir, "cropped images")
    
    last_index = get_last_index(image_output_dir)+1 # Starts on next index
    print("There are already {} images".format(last_index))

    total_imgs_per_lego = total_images * legos_per_img / len(legos_to_sample)
    print("There will be about {} samples of each lego".format(total_imgs_per_lego))
    
    plane = scene_manager.setup_scene()
    env_node = scene_manager.setup_hdris()

    if (continue_training and total_images > last_index):
        # Generates upto the number of images needed, nothing more
        print("Generating {} more images".format(total_images-last_index))
    elif (continue_training and total_images <= last_index):
        print("No more images need to be generated")
        return
    else:
        print("Generating {} images".format(total_images))

    legos = []
    i = last_index
    while i < total_images:
        if ((i-last_index) % batch_size == 0):
            # Delete all current legos and spawn new ones
            scene_manager.delete_legos(legos)
            lego_ids = random.choices(legos_to_sample, k=legos_per_img)
            print("Importing legos: {}".format(lego_ids))
            legos = scene_manager.create_legos(lego_ids)

        # Randomize lego colors
        colors = scene_manager.randomize_lego_materials(legos)

        # Randomize lego position
        scene_manager.randomize_lego_positions(legos)
        
        # Randomize ground material
        scene_manager.set_ground_material(random.choice(scene_manager.mats), plane)
        scene_manager.randomize_ground_mapping(plane)

        # Randomize hdri
        scene_manager.set_hdri(random.choice(scene_manager.hdris), env_node)
        scene_manager.randomize_hdri_rotation()

        # Randomize camera position
        scene_manager.randomize_camera_position()

        # Render scene
        img_name = f'{i}.jpg'
        print("Rendering image {} to {}".format(i, image_output_dir))
        scene_manager.render(img_name, image_output_dir)
                
        # Find bounding boxes
        boxes = [find_bounding_box(lego) for lego in legos]

        # Save cropped images for color classification
        img_path = os.path.join(image_output_dir, img_name)
        cropped_imgs = [crop_image(img_path, box) for box in boxes]
        names = ["{}_{}.jpg".format(i, j) for j in range(len(boxes))]
        print("Saving cropped images {} to {}".format(names, cropped_image_output_dir))

        for img, name, color in zip(cropped_imgs, names, colors):
            save_image(img, name, color, cropped_image_output_dir)
                
        # Export metadata
        print("Exporting image {} metadata to {}".format(i, output_dir))
        export_metadata(lego_ids, boxes, colors, output_dir, img_name, img_dim=Options.img_size)

        i += 1
                

if (__name__ == '__main__'):
    training_data_dir = os.path.join(Options.project_dir, "training data")
    validation_data_dir = os.path.join(Options.project_dir, "validation data")
    testing_data_dir = os.path.join(Options.project_dir, "testing data")

    generate_data(["3023", "3024", "3004"], 400, 5, 5, training_data_dir, True)
    generate_data(["3023", "3024", "3004"], 100, 5, 3, validation_data_dir, True)
    generate_data(["3023", "3024", "3004"], 100, 5, 3, testing_data_dir, True)