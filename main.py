from __future__ import annotations
import math
import bpy
import os
import random
import sys

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from PIL import Image

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import export_data
import scene_manager
import options

# Hacky way to import python files in blender
from importlib import reload
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

def find_bounding_boxes(legos, count_outside_frame=True):
    boxes = []
    w = Options.img_size[0]
    h = Options.img_size[1]
    for lego in legos:
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
                    boxes.append(box)
            else:
                boxes.append(box)
            
    return boxes

def crop_image(image_path, box):
    pil_image = Image.open(image_path)
    return pil_image.crop(box)

def save_images(images, names, colors, dir):
    for img, name, color in zip(images, names, colors):
        output_dir = os.path.join(dir, color) # Save in folder called the correct color
        
        if not os.path.exists(output_dir): # Create folder if needed
            os.makedirs(output_dir)

        img.save(os.path.join(output_dir, name))

def generate_data(legos_to_sample, total_imgs_per_lego, legos_per_img, img_per_loc, output_dir, continue_training=False):
    image_output_dir = os.path.join(output_dir, "images")
    cropped_image_output_dir = os.path.join(output_dir, "cropped images")
    
    i = get_last_index(image_output_dir)+1 # Starts on next index
    print("There are already {} images".format(i))

    total_images = total_imgs_per_lego * len(legos_to_sample) / legos_per_img
    
    plane = scene_manager.setup_scene()
    env_node = scene_manager.setup_hdris()

    if (continue_training and total_images > i):
        # Generates upto the number of images needed, nothing more
        print("Generating {} images".format(total_images-i))
        total_iter = math.ceil((total_images-i) / (len(scene_manager.mats) * len(scene_manager.hdris) * img_per_loc)) 
    elif (continue_training and total_images <= i):
        print("No more images need to be generated")
    else:
        print("Generating {} images".format(total_images))
        total_iter = math.ceil(total_images / (len(scene_manager.mats) * len(scene_manager.hdris) * img_per_loc))  
    
    legos = []

    for _ in range(total_iter):
        # Delete all current legos and spawn new ones
        scene_manager.delete_legos(legos)
        lego_ids = random.choices(legos_to_sample, k=legos_per_img)
        print("Importing legos: [{}]".format(lego_ids))
        legos = scene_manager.create_legos(lego_ids)
        
        random.shuffle(scene_manager.mats)
        for mat in scene_manager.mats:
            # Randomize ground material, camera position
            scene_manager.set_ground_material(plane, mat)
            scene_manager.randomize_camera_position()
            colors = scene_manager.randomize_lego_materials(legos)
            
            random.shuffle(scene_manager.hdris)
            for hdri in scene_manager.hdris:
                # Randomize hdri and ground mapping
                scene_manager.set_hdri(hdri, env_node)
                scene_manager.randomize_ground_mapping(mat)
                
                for _ in range(img_per_loc):
                    # Randomize hdri and lego orientation
                    scene_manager.randomize_hdri_rotation()
                    scene_manager.randomize_lego_positions(legos, scene.render.fps, Options.seconds_simulated)

                    # Render scene
                    img_name = f'{i}.jpg'
                    print("Rendering image {} to {}".format(i, image_output_dir))
                    scene_manager.render(img_name, image_output_dir)
                    
                    boxes = find_bounding_boxes(legos)

                    # Save cropped images for color classification
                    img_path = os.path.join(image_output_dir, img_name)
                    cropped_imgs = [crop_image(img_path, box) for box in boxes]
                    names = ["{}_{}.jpg".format(i, j) for j in range(len(boxes))]
                    print("Saving cropped images {} to {}".format(names, cropped_image_output_dir))
                    save_images(cropped_imgs, names, colors, cropped_image_output_dir)
                    
                    # Export data
                    print("Exporting image {} metadata to {}".format(i, output_dir))
                    export_metadata(lego_ids, boxes, colors, output_dir, img_name, img_dim=Options.img_size)
                    
                    i += 1
                    if (i == total_images):
                        return

training_data_dir = os.path.join(Options.project_dir, "training data")
validation_data_dir = os.path.join(Options.project_dir, "validation data")
testing_data_dir = os.path.join(Options.project_dir, "testing data")
generate_data(["3023", "3024", "3004"], 400, 3, 1, training_data_dir, True)
generate_data(["3023", "3024", "3004"], 50, 3, 1, validation_data_dir, True)
generate_data(["3023", "3024", "3004"], 50, 5, 1, testing_data_dir, True)