from math import pi
import os
class Options:
    project_dir = 'C:\\Users\\jared\\Documents\\Lego Custom Dataset\\'
    ldraw_dir = 'C:\\Users\\jared\\Documents\\LDraw\\'
    image_dir = os.path.join(project_dir, 'images')
    parts_dir = os.path.join(ldraw_dir, 'parts')
    hdri_dir = os.path.join(project_dir, 'HDRIs')
    
    img_size = (256, 256, 3)

    location_mapping_range = 4
    scale_mapping_min = 40
    scale_mapping_max = 80

    mean_height_of_cam = 5.0 #inches
    height_var = 0.5
    mean_sensor_width = 3.68
    sensor_width_var = .4
    angle_var = 5.5 * pi / 180.0

    seconds_simulated = 6.0
    simulation_fps = 6