#publicly available docker image "python" on docker hub will be pulled
FROM python:latest

#Workspace directory to hold the tools and scripts within the container
WORKDIR /workspace

#Directory to interface between host and container
VOLUME /datavol

# Copy the current directory contents into the container at /workspace
ADD . /workspace

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

#running CompuMethodGen.py in container
ENTRYPOINT ["python", "/workspace/CAN_config_validation_tool.py"]
