# It takes awhile to manually delete
import os
from options import Options

def delete(dir):
    for file in os.listdir(dir):
        file_dir = os.path.join(dir, file)
        print("Deleting {} in {}".format(file, dir))
        os.remove(file_dir)

def empty_dir_data(dir):
    delete(os.path.join(dir, "annotations"))
    delete(os.path.join(dir, "images"))

    crp_imgs_dir = os.path.join(dir, "cropped images")
    for folder in os.listdir(crp_imgs_dir):
        delete(os.path.join(crp_imgs_dir, folder))

if (__name__ == '__main__'):
    confirm = input("Are you sure you want to delete all of the data? (Y\\n) ")
    print(confirm)
    if (confirm.lower() == 'y'):
        empty_dir_data(os.path.join(Options.project_dir, "training data"))
        empty_dir_data(os.path.join(Options.project_dir, "testing data"))
        empty_dir_data(os.path.join(Options.project_dir, "validation data"))