import docker
from sys import exit
from . import ML_constants as MLC


#For Windows
#client = docker.APIClient(base_url='npipe:////./pipe/docker_engine')
#For Linux
client = docker.APIClient(base_url='unix://var/run/docker.sock')

#hostVolume="/home/ahmad/Desktop/containerMount/MLC_Service_Docker_Interface"
containerVolume     = MLC.containerVolume
trainingDockerImage = MLC.trainingDockerImage
exportDockerImage   = MLC.exportModelDockerImage
def isImageAvailable(imageName):
    try:
        dockerImage = client.images(name=imageName)
        if dockerImage != []:
            print("Image validated.")
            return True
        else:
            print("Image does not exist.")
            return False
    except Exception as e:
        print(str(e))
        return False

#Function to create the container for Model Training
def createTrainingContainer(dockerImage,containerName,hostVolume,containerVolume):
    try:
        volumes= [hostVolume]
        volume_bindings = {
                            hostVolume: {
                                'bind': containerVolume,
                                'mode': 'rw',
                            },
        }

        host_config = client.create_host_config(
                            binds=volume_bindings
        )

        container = client.create_container(
                            image=dockerImage,
                            name=containerName,
                            command='/bin/sh',
                            volumes=volumes,
                            host_config=host_config,
        ) 
        return container
    except Exception as e:
        print(str(e))
        return False


# Function to create container for exporting the trained model
def createExportContainer(dockerImage,containerName,hostVolume,containerVolume):
    try:
        volumes= [hostVolume]
        volume_bindings = {
                            hostVolume: {
                                'bind': containerVolume,
                                'mode': 'rw',
                            },
        }

        host_config = client.create_host_config(
                            binds=volume_bindings
        )

        container = client.create_container(
                            image=dockerImage,
                            name=containerName,
                            #TODO: changet this to a parameter or user input
                            command='--trained_checkpoint_prefix=/datavol/training/model.ckpt-500',
                            volumes=volumes,
                            host_config=host_config,
        ) 
        return container
    except Exception as e:
        print(str(e))
        return False

def getContainerID(container):
    clientStatus = client.inspect_container(container)
    containerID = clientStatus["Id"]
    return containerID

def checkContainerStatus(container):
    clientStatus = client.inspect_container(container)
    containerStatus = clientStatus["State"]["Status"]
    return containerStatus

def getContainerExitCode(container):
    clientStatus = client.inspect_container(container)
    containerState = clientStatus["State"]
    exitCode = containerState["ExitCode"]
    return exitCode

#Function starts the container for training the model
def startModelTraining(containerName, hostVolume):
    try:    
        if isImageAvailable(trainingDockerImage):
            container = createTrainingContainer(trainingDockerImage,containerName,hostVolume,containerVolume)
            logger = client.attach(container=container.get('Id'),stdout=True, stderr=True, stream=True, logs=True, demux=False)
            response = client.start(container=container.get('Id'))

            containerStatus = checkContainerStatus(container)
            #for line in logger:
            #    print(line)
            #exitCode = getContainerExitCode(container)
            print("Container: " + container.get('Id')+ ",Execution status: " + str(containerStatus))
            return container.get('Id')
        else:
            return False  
    except Exception as e:
        print(str(e))
        return False

# Function starts the container for exporting the trained model
def exportGraph(containerName, hostVolume):
    try:    
        if isImageAvailable(exportDockerImage):
            container = createExportContainer(exportDockerImage,containerName,hostVolume,containerVolume)
            logger = client.attach(container=container.get('Id'),stdout=True, stderr=True, stream=True, logs=True, demux=False)
            response = client.start(container=container.get('Id'))
            containerStatus = checkContainerStatus(container)
            print("Container: " + container.get('Id')+ ",Execution status: " + str(containerStatus))
            return container.get('Id')
        else:
            return False  
    except Exception as e:
        print(str(e))
        return False

# def main():
#     if isImageAvailable(trainingDockerImage):
#         container = createTrainingContainer(trainingDockerImage,"tf-training-container",hostVolume,containerVolume)
#         logger = client.attach(container=container.get('Id'),stdout=True, stderr=True, stream=True, logs=True, demux=False)
#         response = client.start(container=container.get('Id'))

#         containerStatus = checkContainerStatus(container)
#         while(containerStatus != "exited"):
#             containerStatus = checkContainerStatus(container)
#             print(containerStatus)
#         exitCode = getContainerExitCode(container)
#         print("Container execution status: " + str(exitCode))
#         return True
#     else:
#         return False

#if __name__ == "__main__":
#    main()
