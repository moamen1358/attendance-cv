# import time
# from PIL import Image
# from vision_agent_tools.vision_agent_tools.models.owlv2 import Owlv2, OWLV2Config
# from vision_agent_tools.vision_agent_tools.shared_types import Device

# # Load image
# image = Image.open("/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png")
# # image = Image.open("/home/invisa/Desktop/my_grad_streamlit/download.jpeg")

# # Initialize the model with CPU
# model_config = OWLV2Config(device=Device.CPU)
# model = Owlv2(model_config=model_config)

# # Measure the start time
# start_time = time.time()

# # Run the model with the image and a text prompt
# detections = model(prompts=["student"], images=[image])

# # Measure the end time
# end_time = time.time()


# # Calculate the processing time
# processing_time = end_time - start_time

# # Print the number of detections and the processing time
# print(f"Number of detections: {len(detections[0])}")
# print(f"Processing time: {processing_time:.2f} seconds")
# print(detections)

# # import vision_agent.tools as T
# # import matplotlib.pyplot as plt

# # image = T.load_image("/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png")
# # dets = T.countgd_object_detection("person", image)
# # # visualize the countgd bounding boxes on the image
# # viz = T.overlay_bounding_boxes(image, dets)# save the visualization to a file
# # T.save_image(viz, "people_detected_2.png")

# # # display the visualization
# # plt.imshow(viz)
# # plt.show()

import vision_agent.tools as T
import matplotlib.pyplot as plt

image = T.load_image("/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png")
dets = T.countgd_object_detection("person", image)
# visualize the countgd bounding boxes on the image
viz = T.overlay_bounding_boxes(image, dets)# save the visualization to a file
T.save_image(viz, "people_detected_2.png")

# display the visualization
plt.imshow(viz)
plt.show()