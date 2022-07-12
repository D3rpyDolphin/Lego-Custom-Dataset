import bpy
import os
import random
import math
import random
import rebrick
import json

import ldraw_import
from options import Options

from dotenv import load_dotenv
load_dotenv() # loads env file, dont want to show API key lol

# TODO replace all bpy.ops
scene = bpy.context.scene

def setup_scene():
    # delete all objects
    objs = bpy.data.objects
    for obj in objs:
        objs.remove(obj, do_unlink=True)

    # Ldraw settings
    ldraw_import.isBlender28OrLater = True
    ldraw_import.Options.ldrawDirectory = Options.ldraw_dir
    ldraw_import.Options.scale = 0.04
    ldraw_import.Options.importCameras = False
    ldraw_import.Options.useLogoStuds = False
    ldraw_import.Options.useLSynthParts = False
    ldraw_import.Options.useUnofficialParts = False
    ldraw_import.Options.createInstances = False
    ldraw_import.Options.addWorldEnvironmentTexture = False   # Add an environment texture
    ldraw_import.Options.addGroundPlane = False               # Add a ground plane
    ldraw_import.Options.setRenderSettings = False            # Set render percentage, denoising
    ldraw_import.Options.positionCamera = False               # Position the camera where so we get the whole object in shot



    scene.rigidbody_world.enabled = True

    # create camera
    cam_data = bpy.data.cameras.new('camera')
    cam = bpy.data.objects.new('camera', cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera=cam

    # raspberry pi v2 cam specs
    cam.data.lens = 3.04
    cam.data.sensor_width = 3.68

    scene.render.resolution_x = Options.img_size[0]
    scene.render.resolution_y = Options.img_size[1]

    # create plane object and add physics
    bpy.ops.mesh.primitive_plane_add(size=30.0)
    plane = bpy.context.object
    bpy.ops.rigidbody.object_add()
    plane.rigid_body.type = 'PASSIVE'
    #plane.rigid_body.collisions_shape = 'MESH'
    plane.rigid_body.restitution = .5

    scene.render.fps = Options.simulation_fps
    bpy.context.scene.frame_set(0)

    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.render.image_settings.file_format = 'JPEG'
    scene.cycles.seed = 0
    return plane

def inches_to_meters(inches):
    return 0.0254 * inches * 100.0 # World is scaled times 100 

# HDRI
hdris = []
def setup_hdris():
    for hdri in os.listdir(Options.hdri_dir):
        if hdri.endswith(".hdr"):
            hdris.append(hdri)

    # Get the environment node tree of the current scene
    node_tree = scene.world.node_tree
    tree_nodes = node_tree.nodes

    # Clear all nodes
    tree_nodes.clear()

    # Texture nodes
    node_texture_coord = tree_nodes.new('ShaderNodeTexCoord')
    node_texture_coord.location = -700,0

    node_mapping = tree_nodes.new('ShaderNodeMapping')
    node_mapping.vector_type = 'TEXTURE'
    node_mapping.location = -500,0

    # Add Environment Texture node
    node_environment = tree_nodes.new('ShaderNodeTexEnvironment')
    node_environment.location = -300,0

    # Add Output node
    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')   
    node_output.location = 200,0

    # Link all nodes
    links = node_tree.links
    link = links.new(node_texture_coord.outputs["Object"], node_mapping.inputs["Vector"])
    link = links.new(node_mapping.outputs["Vector"], node_environment.inputs["Vector"])
    link = links.new(node_environment.outputs["Color"], node_output.inputs["Surface"])

    return node_environment
def set_hdri(hdri, node_environment):
    # TODO, reuse image if previously loaded
    node_environment.image = bpy.data.images.load(os.path.join(Options.hdri_dir, hdri)) # Relative path   
def randomize_hdri_rotation():
    node_tree = scene.world.node_tree
    tree_nodes = node_tree.nodes
    
    node_mapping = tree_nodes.get('Mapping')
    node_mapping.inputs['Rotation'].default_value = [random.uniform(0, 2*math.pi) for i in range(3)]
    
# Ground
mats = ["carpet", "paper", "tile1", "tile2", "wood"]
def set_ground_material(plane, mat_name): 
    mat = bpy.data.materials[mat_name] 
    if plane.data.materials:
        # assign to 1st material slot
        plane.data.materials[0] = mat
    else:
        # no slots
        plane.data.materials.append(mat)
def randomize_ground_mapping(mat_name):
    mat = bpy.data.materials[mat_name] 
    nodes = mat.node_tree.nodes
    map_node = nodes.get('Mapping')
    map_node.inputs['Location'].default_value = [random.uniform(-Options.location_mapping_range/2.0, Options.location_mapping_range/2.0) for i in range(3)] # Centered at (0,0,0)
    map_node.inputs['Rotation'].default_value.z = random.uniform(0, 2*math.pi)
    scale = random.uniform(Options.scale_mapping_min, Options.scale_mapping_max)
    map_node.inputs['Scale'].default_value = [scale for i in range(3)] # Proportional scaling
    
# Camera
def randomize_camera_position():
    cam = scene.camera
    # randomize sensor_width
    cam.data.sensor_width = Options.mean_sensor_width + random.uniform(-Options.sensor_width_var, Options.sensor_width_var)
    
    # randomize height
    z = Options.mean_height_of_cam + random.uniform(-Options.height_var, Options.height_var)
    cam.location = (0.0, 0.0, inches_to_meters(z))
    
    # slightly randomize angle
    cam.rotation_euler[0] = random.uniform(-Options.angle_var, Options.angle_var)

# Legos
def delete_legos(legos):
    objs = bpy.data.objects
    for lego in legos:
        objs.remove(lego.ob, do_unlink=True)
def create_legos(part_ids):
    legos = []
    for part_id in part_ids:
        path = os.path.join(ldraw_import.Options.ldrawDirectory, "parts", part_id + '.dat')
        lego = ldraw_import.loadFromFile(None, path, isFullFilepath=True)
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
        lego.ob.rigid_body.mass = .0025
    
    # Stop after sec seconds
    for i in range(0, total_frames+1):
        bpy.context.scene.frame_set(i)
    
    for lego in legos:
        lego.ob.select_set(True) 
        scene.rigidbody_world.collection.objects.unlink(lego.ob) 
    
    bpy.ops.object.visual_transform_apply() # TODO check if this is slow
    bpy.ops.object.select_all(action='DESELECT')
    
    bpy.context.scene.frame_set(0)
def generate_color_list(id, part_threshold=0):
    # Get color data from rebrickable
    # TODO some are invalid colors
    response = rebrick.lego.get_part_colors(id, api_key=os.environ.get("KEY"))
    results = json.loads(response.read())['results']
    return [str(r['color_id']) for r in results if r['num_set_parts'] > part_threshold]
color_cache = {} # cache stores list of possible colors for each lego piece
def get_color_list(id):
    if id in color_cache: # Check if we already have the color list
        return color_cache.get(id)
    else: # Generate list and add to cache
        color_list = generate_color_list(id)
        color_cache[id] = color_list
        return color_list

def randomize_lego_materials(legos): 
    colors = []
    for lego in legos:   
        # color = random.choice(get_color_list(lego.part_id))
        color = random.choice(['0', '15', '71', '72', '4', '14', '19', '70', '7', '2']) # 10 most popular colors as proof of concept
        lego.change_material(color)
        colors.append(color)
    return colors

# Render
def render(name, output_dir, debug_viewport=False):
    scene.cycles.seed += 1 # change seed to randomize rendering noise
    
    scene.render.filepath = os.path.join(output_dir, name)
    bpy.ops.render.render(write_still = True, use_viewport = debug_viewport) 

if __name__ == '__main__':
    print(generate_color_list('3004'))