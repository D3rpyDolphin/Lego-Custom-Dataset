import math
import bpy
import os
import random
import sys
import time

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)

import export_data
import import_legos
import ldraw_import

from importlib import reload
reload(export_data)
reload(import_legos)
reload(ldraw_import)
    
from export_data import export
from import_legos import delete_legos, create_legos, randomize_lego_positions, randomize_lego_materials

scene = bpy.context.scene

project_dir = 'C:\\Users\\jared\\Documents\\Lego Custom Dataset\\'

ldraw_dir = 'C:\\Users\\jared\\Documents\\LDraw\\'
def setup_import_settings():
    ldraw_import.isBlender28OrLater = True

    ldraw_import.Options.ldrawDirectory = ldraw_dir
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

img_size = (256, 256, 3)
def setup_scene():
    # delete all objects
    objs = bpy.data.objects
    for obj in objs:
        objs.remove(obj, do_unlink=True)

    setup_import_settings()

    scene.rigidbody_world.enabled = True

    cam_data = bpy.data.cameras.new('camera')
    cam = bpy.data.objects.new('camera', cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera=cam

    # raspberry pi v2 cam specs
    cam.data.lens = 3.04
    cam.data.sensor_width = 3.68

    scene.render.resolution_x = img_size[0]
    scene.render.resolution_y = img_size[1]

    bpy.ops.mesh.primitive_plane_add(size=30.0)
    plane = bpy.context.object
    bpy.ops.rigidbody.object_add()
    plane.rigid_body.type = 'PASSIVE'
    #plane.rigid_body.collisions_shape = 'MESH'
    plane.rigid_body.restitution = .5

    scene.render.fps = 6
    bpy.context.scene.frame_set(0)

    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.render.image_settings.file_format = 'JPEG'
    scene.cycles.seed = 0
    return plane

def ctm(inches):
    return 0.0254 * inches * 100.0

     

hdri_dir = os.path.join(project_dir, 'HDRIs')
hdris = []
for hdri in os.listdir(hdri_dir):
    if hdri.endswith(".hdr"):
        hdris.append(hdri)

def setup_hdris():
    # Setup hdri
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
    node_environment.image = bpy.data.images.load(os.path.join(hdri_dir, hdri)) # Relative path
    
    
def randomize_hdri_rotation():
    node_tree = scene.world.node_tree
    tree_nodes = node_tree.nodes
    
    node_mapping = tree_nodes.get('Mapping')
    node_mapping.inputs['Rotation'].default_value = [random.uniform(0, 2*math.pi) for i in range(3)]
    
    
mats = ["carpet", "paper", "tile1", "tile2", "wood"]
def set_ground_material(plane, mat_name): 
    mat = bpy.data.materials[mat_name] 
    if plane.data.materials:
        # assign to 1st material slot
        plane.data.materials[0] = mat
    else:
        # no slots
        plane.data.materials.append(mat)
        
location_mapping_range = 2
scale_mapping_min = 40
scale_mapping_max = 80
def randomize_ground_mapping(mat_name):
    mat = bpy.data.materials[mat_name] 
    nodes = mat.node_tree.nodes
    map_node = nodes.get('Mapping')
    map_node.inputs['Location'].default_value = [random.uniform(-location_mapping_range, location_mapping_range) for i in range(3)]
    map_node.inputs['Rotation'].default_value.z = random.uniform(0, 2*math.pi)
    scale = random.uniform(scale_mapping_min, scale_mapping_max)
    map_node.inputs['Scale'].default_value = [scale for i in range(3)]
    

mean_height_of_cam = 5.0 #inches
height_var = 0.5
sensor_width_var = .4
angle_var = 5.5 * math.pi / 180.0
def randomize_camera_position():
    cam = scene.camera
    # randomize sensor_width
    cam.data.sensor_width = 3.68 + random.uniform(-sensor_width_var, sensor_width_var)
    
    # randomize height
    z = mean_height_of_cam + random.uniform(-height_var, height_var)
    cam.location = (0.0, 0.0, ctm(z))
    
    # slightly randomize angle
    cam.rotation_euler[0] = random.uniform(-angle_var, angle_var)
    

image_dir = os.path.join(project_dir, 'images')
#TODO fix this
def render(name, dir=image_dir):
    scene.cycles.seed += 1 # change seed to randomize noise
    
    scene.render.filepath = os.path.join(dir, name)
    bpy.ops.render.render(write_still = True, use_viewport = True)

def find_bounding_boxes(legos):
    boxes = []
    w = img_size[0]
    h = img_size[1]
    for lego in legos:
        bpy.context.view_layer.update()
        mat = lego.ob.matrix_world
        world_bb_vertices = [mat @ Vector(v) for v in lego.ob.bound_box]

        if world_bb_vertices[0].z < -0.5: # under plane because of poor collisions
            continue 

        co_2d = [world_to_camera_view(scene, scene.camera, v) for v in world_bb_vertices]
        # reformat coords
        xs, ys, _ = zip(*co_2d)

        box = (int(min(xs) * w), int((1-max(ys)) * h), int(max(xs) * w), int((1-min(ys)) * h))

        is_outside = False
        for i, p in enumerate(box):
            if p < 0 or p > img_size[i % 2]:
                is_outside = True
        
        if is_outside is True:
            continue

        boxes.append(box)
    return boxes


parts_dir = os.path.join(ldraw_dir, 'parts')

legos_to_sample = ["3023", "3024", "3004"]
legos_per_img = 5
imgs_per_lego = 100 # Number should be greater than 200
img_per_loc = 1

total_images = imgs_per_lego * len(legos_to_sample) / legos_per_img # TODO check math this is wrong

def get_last_index():
    files = os.listdir(image_dir)
    paths = [os.path.join(image_dir, basename) for basename in files]
    if (len(paths) > 0):
        return int(max(paths, key=os.path.getctime).split('\\')[-1].split('.')[0])
    else:
        return -1


def main():
    plane = setup_scene()
    env_node = setup_hdris()

    i = get_last_index() + 1

    m = int(total_images / (len(mats) * len(hdris) * img_per_loc)) - i
    legos = []

    for _ in range(m):
        # Delete all current legos and spawn new ones
        delete_legos(legos)
        lego_ids = random.choices(legos_to_sample, k=legos_per_img)
        legos = create_legos(lego_ids)
        
        for mat in mats:
            # Randomize ground material, camera position
            set_ground_material(plane, mat)
            randomize_camera_position()
            colors = randomize_lego_materials(legos)
            
            for hdri in hdris:
                # Randomize hdri, lego material (?), and ground mapping
                set_hdri(hdri, env_node)
                randomize_ground_mapping(mat)
                
                for _ in range(img_per_loc):
                    # Randomize hdri, lego orientations (is this really needed every loop?)
                    randomize_hdri_rotation()
                    randomize_lego_positions(legos, scene.render.fps, 6.0)

                    # Render, find bounding boxes, then export
                    
                    img_name = f'{i}.jpeg'
                    render(img_name)
                    #TODO add height check for boxes
                    boxes = find_bounding_boxes(legos)
                    export(lego_ids, boxes, colors, project_dir, img_name, img_dim=img_size)
                    
                    i += 1

# start = time.time()
main()
# end = time.time()

# t = end-start

# print(t)