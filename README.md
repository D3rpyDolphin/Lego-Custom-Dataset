# Lego-Custom-Dataset

This program creates a dataset of legos using the Blender API and a slightly modified version of [Toby Nelson's ImportLDraw](https://github.com/TobyLobster/ImportLDraw). The environment is heavily randomized to help bridge the gap between simulated and real data. This includes the background lighting environment, floor material, lego color, and lego orientation (by doing a short gravity simulation dropping them).

For now, the dataset only includes 3 types of lego pieces but can very easily be expanded to any amount.

The images can be found [here](https://github.com/D3rpyDolphin/Lego-Custom-Dataset/tree/master/images).

The model training can be found [here](https://github.com/D3rpyDolphin/Lego-Custom-Dataset/blob/master/object_detection_model.ipynb). In the future, being able to visualize the model evaluations would be very useful to determine accuracy. Additionally, I plan to take the output bounding box, crop the input image, and pass it into an image classifier to determine the color of the legos.
