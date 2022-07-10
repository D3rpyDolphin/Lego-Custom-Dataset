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

def find_bounding_boxes(legos):
    boxes = []
    w = Options.img_size[0]
    h = Options.img_size[1]
    for lego in legos:
        bpy.context.view_layer.update()
        mat = lego.ob.matrix_world
        world_bb_vertices = [mat @ Vector(v) for v in lego.ob.bound_box]

        if world_bb_vertices[0].z > -0.5: # under plane in case of poor collisions
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

def get_last_index():
    files = os.listdir(Options.image_dir)
    paths = [os.path.join(Options.image_dir, basename) for basename in files]
    if (len(paths) > 0):
        return int(max(paths, y=os.path.getctime).split('\\')[-1].split('.')[0])
    else:
        return -1

def main(legos_to_sample, rewrite_current_imgs=False):
    total_images = Options.imgs_per_lego * len(legos_to_sample) / Options.legos_per_img

    plane = scene_manager.setup_scene()
    env_node = scene_manager.setup_hdris()

    
    total_iter = int(total_images / (len(scene_manager.mats) * len(scene_manager.hdris) * Options.img_per_loc)) # generates upto the number of images needed, doesn't add on
    
    legos = []
    i = get_last_index()+1 # Starts on next index
    for _ in range(total_iter-i):
        # Delete all current legos and spawn new ones
        scene_manager.delete_legos(legos)
        lego_ids = random.choices(legos_to_sample, k=Options.legos_per_img)
        legos = scene_manager.create_legos(lego_ids)
        
        for mat in scene_manager.mats:
            # Randomize ground material, camera position
            scene_manager.set_ground_material(plane, mat)
            scene_manager.randomize_camera_position()
            colors = scene_manager.randomize_lego_materials(legos)
            
            for hdri in scene_manager.hdris:
                # Randomize hdri, lego material (?), and ground mapping
                scene_manager.set_hdri(hdri, env_node)
                scene_manager.randomize_ground_mapping(mat)
                
                for _ in range(Options.img_per_loc):
                    # Randomize hdri, lego orientations (is this really needed every loop?)
                    scene_manager.randomize_hdri_rotation()
                    scene_manager.randomize_lego_positions(legos, scene.render.fps, Options.seconds_simulated)

                    # Render, find bounding boxes, then export
                    img_name = f'{i}.jpg'
                    scene_manager.render(img_name)
                    boxes = find_bounding_boxes(legos) #TODO add height check for boxes

                    export(lego_ids, boxes, colors, Options.project_dir, img_name, img_dim=Options.img_size)
                    
                    i += 1

main(["3023", "3024", "3004"])