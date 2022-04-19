import random
import rebrick
import json
import os
import bpy
import math
from ldraw_import import loadFromFile, Options

def delete_legos(legos):
    objs = bpy.data.objects
    for lego in legos:
        objs.remove(lego.ob, do_unlink=True)

def create_legos(part_ids):
    legos = []
    for part_id in part_ids:
        path = os.path.join(Options.ldrawDirectory, "parts", part_id + '.dat')
        lego = loadFromFile(None, path, isFullFilepath=True)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
        legos.append(lego)
    return legos

def randomize_lego_orientations(lego, spawn_dist = 2.5, height_avg = 8, height_var=5.0):
    lego.ob.location[0] = random.uniform(-spawn_dist, spawn_dist)
    lego.ob.location[1] = random.uniform(-spawn_dist, spawn_dist)
    lego.ob.location[2] = height_avg + random.uniform(-height_var, height_var) # TODO height spawn based on size
    lego.ob.rotation_euler = [random.uniform(-math.pi, math.pi) for _ in range(3)]

def randomize_lego_positions(legos, fps, seconds):
    scene = bpy.context.scene
    total_frames = int(fps * seconds)

    for lego in legos:
        randomize_lego_orientations(lego)
        
        if (scene.rigidbody_world.collection.objects.find(lego.ob.name) == -1):
            scene.rigidbody_world.collection.objects.link(lego.ob) 
        lego.ob.rigid_body.mass = .0025 # TODO do it based on volume
    
    # Stop after sec seconds
    for i in range(0, total_frames+1):
        bpy.context.scene.frame_set(i)
    
    for lego in legos:
        lego.ob.select_set(True) 
        scene.rigidbody_world.collection.objects.unlink(lego.ob) 
    
    bpy.ops.object.visual_transform_apply() # TODO check if this is slow
    bpy.ops.object.select_all(action='DESELECT')
    
    bpy.context.scene.frame_set(0)
    
# Get color data from rebrickable
def generate_color_list(id, part_threshold=0):
    #TODO some are invalid colors
    response = rebrick.lego.get_part_colors(id, api_key="7afc8ac7cd618889dc5f080232e96ad2")
    results = json.loads(response.read())['results']
    return [str(r['color_id']) for r in results if r['num_set_parts'] > part_threshold]

color_cache = {}
def get_color_list(id):
    # Check if we already have the color list
    if id in color_cache:
        return color_cache.get(id)

    # Generate list and add to cache
    color_list = generate_color_list(id)
    color_cache[id] = color_list
    return color_list

def randomize_lego_materials(legos): 
    colors = []
    for lego in legos:   
        color = random.choice(get_color_list(lego.part_id))
        lego.change_material(color)
        colors.append(color)
    return colors