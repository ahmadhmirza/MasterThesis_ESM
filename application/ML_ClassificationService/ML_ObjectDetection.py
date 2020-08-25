# -*- coding: utf-8 -*-
#############################################################################
#                                                                           #
#                            ROBERT BOSCH GMBH                              #
#                                STUTTGART                                  #
#                                                                           #
#              Alle Rechte vorbehalten - All rights reserved                #
#                                                                           #
#############################################################################
#                      ____   ____  _____  ______ __  __                    #
#                     / __ ) / __ \/ ___/ / ____// / / /                    #
#                    / __  |/ / / /\__ \ / /    / /_/ /                     #
#                   / /_/ // /_/ /___/ // /___ / __  /                      #
#                  /_____/ \____//____/ \____//_/ /_/                       #
#                                                                           #
#############################################################################
from flask import current_app as app
from flask import make_response,Blueprint
from flask import request

from datetime import datetime
import subprocess,os,shutil
import uuid
import json
from . import ML_constants as MLC


def isInitSuccessful():
    if API_KEY_DB == False:
        return False
    if REQ_HISTORY == False:
        return False   
    return True
    
############################### Init TensorFlow ##############################
try:
    #import tensorflow as tf
    import tensorflow.compat.v1 as tf
    tf.disable_v2_behavior()
    import numpy as np
    import os
    import six.moves.urllib as urllib
    import sys
    import tarfile
    import zipfile
    from distutils.version import StrictVersion
    from collections import defaultdict
    from io import StringIO
    from matplotlib import pyplot as plt
    from PIL import Image
    print("TF IMPORTS SUCCESSFUL")
except Exception as e:
    print(str(e))

# TensorFlow Object_Detection imports
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
# Local Imports
from .static.utils import file_handling as fh 
from . import ML_constants as MLC

OUTPUT_DIR = MLC.OUTPUT_DIR
############################### Model preperation ###############################
"""
This method and block can be used in case a base model is needed,
By default the model to be used is placed in static/assets/model,
This block is just here if needed in future implementation,
"""
def downloadModel():
    MODEL_FILE = MLC.MODEL_FILE
    URL_FOR_MODEL_DOWNLOAD = MLC.URL_FOR_MODEL_DOWNLOAD
    #Download the Model
    opener = urllib.request.URLopener()
    opener.retrieve(URL_FOR_MODEL_DOWNLOAD, MODEL_FILE)
    tar_file = tarfile.open(MODEL_FILE)
    for file in tar_file.getmembers():
        file_name = os.path.basename(file.name)
        if 'frozen_inference_graph.pb' in file_name:
            tar_file.extract(file, os.getcwd())
#################################################################################

################################## LOAD THE GRAPH ################################
def load_DetGraph_and_Map(PATH_TO_FROZEN_GRAPH,PATH_TO_LABELS):
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        try:
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
        except Exception as e:
            print(str(e))
    ### LOAD THE LABEL MAP
    category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)
    return detection_graph, category_index

############################## FUNCTIONS FOR DETECTION OPS########################
"""
Function to load image file into a numpy array for further processing
@param  : image
@return : numpy array
"""
def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)

"""
Perform detection on a image/frame,
@param: image(numpy array), frozen inference graph
@return: dict with detections.
"""
def run_inference_for_single_image(image, graph):
  with graph.as_default():
    with tf.Session() as sess:
      # Get handles to input and output tensors
      ops = tf.get_default_graph().get_operations()
      all_tensor_names = {output.name for op in ops for output in op.outputs}
      tensor_dict = {}
      for key in [
          'num_detections', 'detection_boxes', 'detection_scores',
          'detection_classes', 'detection_masks'
      ]:
        tensor_name = key + ':0'
        if tensor_name in all_tensor_names:
          tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
              tensor_name)
      if 'detection_masks' in tensor_dict:
        # The following processing is only for single image
        detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
        detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
        # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
        real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            detection_masks, detection_boxes, image.shape[0], image.shape[1])
        detection_masks_reframed = tf.cast(
            tf.greater(detection_masks_reframed, 0.5), tf.uint8)
        # Follow the convention by adding back the batch dimension
        tensor_dict['detection_masks'] = tf.expand_dims(
            detection_masks_reframed, 0)
      image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

      # Run inference
      output_dict = sess.run(tensor_dict,
                             feed_dict={image_tensor: np.expand_dims(image, 0)})

      # all outputs are float32 numpy arrays, so convert types as appropriate
      output_dict['num_detections'] = int(output_dict['num_detections'][0])
      output_dict['detection_classes'] = output_dict[
          'detection_classes'][0].astype(np.uint8)
      output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
      output_dict['detection_scores'] = output_dict['detection_scores'][0]
      if 'detection_masks' in output_dict:
        output_dict['detection_masks'] = output_dict['detection_masks'][0]
  return output_dict
###################################################################################

########################## FUNCTIONS RELEVANT TO THE SERVICE #######################
"""
This function renames the generated output file to a hashed value
and moves the file to downloads folder form where it can be served to user.
File is renamed to a generic hashed value to make the process simpler and
avoid unintentional overwriting of generated files.

TO BE NOTED: If cURL is used at customer side, then a desired file name should
be provided at client side with the -o option in cURL to save the file in the
local system with the desired name. 
"""  

def postProcessing(fileName, userFilesDir):
    OUTPUT_FILE_EXTENTION = ".png"
    try:
        fName = fileName.rsplit(".",1)[0]
    except Exception as e:
        print("ERROR: ML: " + str(e))
        fName = "xxx"
        
    fName = fName + OUTPUT_FILE_EXTENTION
    fName = os.path.join(OUTPUT_DIR,fName)
    newFileName = str(uuid.uuid4()) + OUTPUT_FILE_EXTENTION
    try:
        os.rename(fName,newFileName)
        fh.moveFile(newFileName,userFilesDir)
        md5Checksum = fh.generateMD5(os.path.join(userFilesDir,newFileName))
        return newFileName, md5Checksum
    except Exception as e:
        print("ERROR: ML: Post Processing of the results Failed!")
        print("ERROR: ML: " + str(e))
        return False,False

def analyseImage(image_path,detection_graph,category_index):
    image = Image.open(image_path)
    # the array based representation of the image will be used later in order to prepare the
    # result image with boxes and labels on it.
    image_np = load_image_into_numpy_array(image)
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    #image_np_expanded = np.expand_dims(image_np, axis=0)
    # Actual detection.
    output_dict = run_inference_for_single_image(image_np, detection_graph)
    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
    image_np,
    output_dict['detection_boxes'],
    output_dict['detection_classes'],
    output_dict['detection_scores'],
    category_index,
    instance_masks=output_dict.get('detection_masks'),
    use_normalized_coordinates=True,
    line_thickness=8)

    try:
        #TODO: Move Image name to constants
        plt.imsave(os.path.join(OUTPUT_DIR,"hyapi_ml_out_image.png"),image_np)
        return True
    except  Exception as e:
        print("ERROR: ML: " + str(e))
        return False
##############################################################################

def detectStopSign(imagePath,PATH_TO_FROZEN_GRAPH,PATH_TO_LABELS,outDirectory):

    detection_graph, category_index= load_DetGraph_and_Map(PATH_TO_FROZEN_GRAPH,PATH_TO_LABELS)

    if analyseImage(imagePath,detection_graph,category_index):
        fileName,md5 = postProcessing("hyapi_ml_out_image.png",outDirectory)
        if fileName != False:
            print("MD5 hash: " + str(md5))
            return fileName
        else:
            return False

def unitTest():
    # Change paths here relative to your system
    imagePath = r"/home/ahmad/Desktop/index.jpeg"
    PATH_TO_FROZEN_GRAPH = r"/home/ahmad/Desktop/EsmThesis/application/TrafficSignsClassificationService/static/assets/output_inference_graph_v3.pb/frozen_inference_graph.pb"
    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = r"/home/ahmad/Desktop/ObjectDetection/tensorflow/workspace/training/annotations/label_map.pbtxt"
    detection_graph, category_index= load_DetGraph_and_Map(PATH_TO_FROZEN_GRAPH,PATH_TO_LABELS)

    if analyseImage(imagePath,detection_graph,category_index):
        userFilesDir = r"/home/ahmad/Desktop/EsmThesis/application/Database/Workspaces/a1fd7f7a9d4598a64139c1e8032e6269/User_Files/"
        fileName,md5 = postProcessing("hyapi_ml_out_image.png",userFilesDir)
        if fileName != False:
            print("MD5 hash: " + str(md5))

if __name__ == '__main__':
   unitTest()

