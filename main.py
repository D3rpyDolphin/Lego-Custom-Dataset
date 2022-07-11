import math
import bpy
import os
import random
import sys

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

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
    
from export_data import export
import scene_manager
from options import Options

scene = bpy.context.scene

def get_last_index(dir):
    files = [os.path.join(dir, f) for f in os.listdir(dir)]
    if(len(files)>0):
        return int(max(files, key=os.path.getctime).split('\\')[-1].split('.')[0])
    else:
        return -1

def find_bounding_boxes(legos):
    boxes = []
    w = Options.img_size[0]
    h = Options.img_size[1]
    for lego in legos:
        bpy.context.view_layer.update()
        mat = lego.ob.matrix_world
        world_bb_vertices = [mat @ Vector(v) for v in lego.ob.bound_box]

        if world_bb_vertices[0].z > -0.5: # don't count objects that fall through the ground
            co_2d = [world_to_camera_view(scene, scene.camera, v) for v in world_bb_vertices]
            xs, ys, _ = zip(*co_2d) # reformat coords

            box = (int(min(xs) * w), int((1-max(ys)) * h), int(max(xs) * w), int((1-min(ys)) * h))

            outside_frame = False
            for i, p in enumerate(box): # check if the object is outside of the image frame
                if p < 0 or p > Options.img_size[i % 2]:
                    outside_frame = True
            
            if outside_frame is False:
                boxes.append(box)
            
    return boxes
    
def generate_data(legos_to_sample, total_imgs_per_lego, legos_per_img, img_per_loc, output_dir, continue_training=False):
    i = get_last_index(os.path.join(output_dir, "images"))+1 # Starts on next index
    print("There are already {} images".format(i))

    total_images = total_imgs_per_lego * len(legos_to_sample) / legos_per_img
    
    plane = scene_manager.setup_scene()
    env_node = scene_manager.setup_hdris()

    if (continue_training):
        # Generates upto the number of images needed, nothing more
        print("Generating {} images".format(total_images-i))
        total_iter = math.ceil((total_images-i) / (len(scene_manager.mats) * len(scene_manager.hdris) * img_per_loc)) 
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
                # Randomize hdri, lego material (?), and ground mapping
                scene_manager.set_hdri(hdri, env_node)
                scene_manager.randomize_ground_mapping(mat)
                
                for _ in range(img_per_loc):
                    # Randomize hdri, lego orientations (is this really needed every loop?)
                    scene_manager.randomize_hdri_rotation()
                    scene_manager.randomize_lego_positions(legos, scene.render.fps, Options.seconds_simulated)

                    # Render, find bounding boxes, then export
                    img_name = f'{i}.jpg'
                    print("Rendering image {} to {}".format(i, output_dir))
                    scene_manager.render(img_name, output_dir)
                    boxes = find_bounding_boxes(legos) #TODO add height check for boxes

                    print("Exporting image {} data to {}".format(i, output_dir))
                    export(lego_ids, boxes, colors, output_dir, img_name, img_dim=Options.img_size)
                    
                    i += 1
                    if (i > total_images):
                        return

generate_data(["3023", "3024", "3004"], 100, 3, 1, os.path.join(Options.project_dir, "training data"), True)
generate_data(["3023", "3024", "3004"], 50, 3, 1, os.path.join(Options.project_dir, "testing data"), True)