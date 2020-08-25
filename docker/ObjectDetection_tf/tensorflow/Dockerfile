# Use Ubuntu image as base
FROM "ubuntu:20.04"
RUN apt-get update && yes | apt-get upgrade

# working directory
RUN mkdir -p /tensorflow/models

# install git
RUN apt-get install -y git python-pip
RUN pip install --upgrade pip

#Install tensor-flow and dependencies
RUN pip install tensorflow==1.15

RUN apt-get install -y protobuf-compiler python-pil python-lxml
RUN pip install tensorflow-object-detection-api
RUN pip install jupyter
RUN pip install pathlib
RUN pip install matplotlib
RUN pip install opencv-python
RUN pip install lxml
RUN pip install pillow
RUN pip install Cython
RUN pip install contextlib2
RUN pip install pandas
RUN pip install pycocotools
RUN pip install numpy==1.16

#copy tf-models
RUN git clone https://github.com/tensorflow/models.git /tensorflow/models

#changing working directory to /models/research
WORKDIR /tensorflow/models/research

#compiling protobuf libraries
RUN protoc object_detection/protos/*.proto --python_out=.

#adding /models/research and /slim to python path
RUN export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim


#configure jupyter notebook
RUN jupyter notebook --generate-config --allow-root
RUN echo "c.NotebookApp.password = u'sha1:6a3f528eec40:6e896b6e4828f525a6e20e5411cd1c8075d68619'" >> /root/.jupyter/jupyter_notebook_config.py


#expose port for external access
EXPOSE 8888

#run the main process
CMD ["jupyter", "notebook", "--allow-root", "--notebook-dir=/tensorflow/models/research/object_detection", "--ip=0.0.0.0", "--port=8888", "--no-browser"]



