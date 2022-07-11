import xml.etree.cElementTree as ET
import os

# image name should include.png
def export(labels, boxes, colors, output_dir, img_name: str, img_dim=(256,256,3)):
    annotations_folder_name = "annotations"
    image_folder = os.path.join(output_dir, "images")

    annotation = ET.Element('annotation')
    ET.SubElement(annotation, 'folder').text = str(annotations_folder_name)
    ET.SubElement(annotation, 'filename').text = str(img_name)
    ET.SubElement(annotation, 'path').text = os.path.join(image_folder, img_name)

    source = ET.SubElement(annotation, 'source')
    ET.SubElement(source, 'database').text = 'Unknown'

    size = ET.SubElement(annotation, 'size')
    ET.SubElement(size, 'width').text = str (img_dim[0])
    ET.SubElement(size, 'height').text = str(img_dim[1])
    ET.SubElement(size, 'depth').text = str(img_dim[2])

    ET.SubElement(annotation, 'segmented').text = '0'

    for box, label, color in zip(boxes, labels, colors):
        object = ET.SubElement(annotation, 'object')
        ET.SubElement(object, 'name').text = label
        ET.SubElement(object, 'color').text = color
        ET.SubElement(object, 'pose').text = 'Unspecified'
        ET.SubElement(object, 'truncated').text = '0'
        ET.SubElement(object, 'difficult').text = '0'

        bndbox = ET.SubElement(object, 'bndbox')
        ET.SubElement(bndbox, 'xmin').text = str(box[0]) 
        ET.SubElement(bndbox, 'ymin').text = str(box[1])
        ET.SubElement(bndbox, 'xmax').text = str(box[2])
        ET.SubElement(bndbox, 'ymax').text = str(box[3])
    
    export_name = img_name.split('.')[0]
    xml_file_name = os.path.join(output_dir, annotations_folder_name, f'{export_name}.xml')
    
    tree = ET.ElementTree(annotation)
    ET.indent(tree, space="\t", level=0)
    tree.write(xml_file_name, encoding="utf-8")

if __name__ == '__main__':
    export(['3004'], [(0, 0, 20, 20)], ['pink'], f'C:\\Users\\jared\\Documents\\Lego Custom Dataset\\', 'test.png')