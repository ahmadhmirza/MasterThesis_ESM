FROM python:3.7

# install build utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get -y upgrade

#Create a datavolume as external interface
VOLUME /datavol

#Copy contents of the current directory into the image
ADD . /WorkingDir

# install git
RUN apt-get update
RUN apt-get install -y git 
#RUN apt-get install -y python-pip
RUN pip install --upgrade pip

#Install tensor-flow and dependencies
RUN pip install tensorflow==1.15

RUN apt-get install -y protobuf-compiler python-pil python-lxml
RUN pip install tensorflow-object-detection-api
RUN pip install pathlib
RUN pip install pillow
RUN pip install Cython
RUN pip install contextlib2
RUN pip install pandas
RUN pip install numpy==1.16

#Clone tf-models from git
RUN git clone https://github.com/tensorflow/models.git /WorkingDir/models

#compile protobuf libraries
RUN cd /WorkingDir/models/research && \
    protoc object_detection/protos/*.proto --python_out=.


#Add /models/research and /slim to python path
ENV PYTHONPATH=$PYTHONPATH:/WorkingDir/models/research/object_detection
ENV PYTHONPATH=$PYTHONPATH:/WorkingDir/models/research/slim
ENV PYTHONPATH=$PYTHONPATH:/WorkingDir/models/research


#Change working directory to workspace
WORKDIR /WorkingDir/workspace/

#Define entry point to be the model training script
ENTRYPOINT ["python", "export_inference_graph.py", "--input_type=image_tensor", "--pipeline_config_path=/datavol/pipeline.config", "--output_directory=/datavol/trained-inference-graphs/inference_graph.pb"]

# missing parameter to be passed when invoking the container image : --trained_checkpoint_prefix training/model.ckpt-6000