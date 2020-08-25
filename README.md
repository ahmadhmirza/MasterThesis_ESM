## Design & Development of an Inter-Company Software Collaboration Platform Using S.O.A and RestAPIs <!-- omit in toc -->
### FROM MONOLITHIC ARCHITECTURE TO FLEXIBLE MICRO-SERVICES <!-- omit in toc -->
#### Development API Try outs: Provide Services instead of tools to the customer!  <!-- omit in toc -->

Master Thesis results wrt. REST APIs for embedded software development, simulation and test over company boundaries.
Most of the contents are to get really familar with the topics and provide proposals to professional implementation parties.

## Table of Contents  <!-- omit in toc -->

- [Getting Started](#getting-started)
- [Building and Testing](#building-and-testing)
- [Contribution Guidelines](#contribution-guidelines)
- [Configure Git and correct EOL handling](#configure-Git-and-correct-EOL-handling)
- [Feedback](#feedback)
- [About](#about)
  - [Maintainers](#maintainers)
  - [Contributors](#contributors)
  - [3rd Party Licenses](#3rd-party-licenses)
  - [Used Encryption](#used-encryption)
  - [Used AI](#used-AI)
  - [Country of origin](#origin-country)
  - [License](#license)

## Getting Started <a name="getting-started"></a>

The steps outlined below describe how the demo application can be setup on a PC. A working copy of python is required, it is assumed that you have the
virtual environment package also installed (pip install --user virtualenv), Anaconda prompt is recommended for running the application as it avoids any clashes 
arising because of multiple installations of python from toolbase.

- Download a copy of the repo to the local environment.
- Rightclick and open Anaconda prompt in the application directory
  - Alternativley you can open a windows command prompt, in this case please use the whole path of the python executable where ever "python" is refered to in this document
- Create a virtual environment in the application directory to install the dependencies:
  - virtualenv venv
- Activate the virtual environment by executing the script .\vEnv\Scripts\activate.bat in the terminal.
- Install the dependencies in the newly created virtual environment. The list of requirements is included in the requirements.txt file.
  - pip install -r requirements.txt
- Once the installation finishes the application is ready to run. The development server can be started using the following command:
  - python wsgi.py

#### Setting up Python Virtual Environment and dependencies
- Virtual environment package can be installed using pip or anaconda navigator.
- For installation using pip use the following command:
	- pip install virtualenv --user
- The --user flag installs the library for your window user. This is sometimes required when installing python packages on SI maintained PCs.
- If you used --user flag when installing the virtualenv package. If this has not already been done on your PC, you might need to add Anaconda's library to the Path environment variable.
- If this is the case, the path that is required to be added to the environment variables is shown once the package installation finishes.
  - Please copy the path from the terminal and add it to "Path" environment variable on your PC.
  - Once this is done you can proceed with the steps in the previous section.
#### Installing packages - Alternative to virtual environment.
- This method installs the packages in your base environment, although a different path is selected instead of the default installtion path so it would be easier to undo the changes.
- Running the pip command with --target flag and the desired path allows this behaviour
- In the installation directory of HyAPI, create a folder "libDependencies"
- Open a terminal in the newly created folder.
- Run the following command:
	- pip install --target=C:\_____\HyAPI\libDependencies -r requirments.txt
- In this case add the full path of the libDependencies to the environment variable "PYTHONPATH".

#### Setting up client-side cli:
- ClientSide scripts for demo purposes are provided in the directory ./HyAPI/ClientSide-CLI/Windows
- the "config" folder, contains all the necessary paths and URLs required for the scripts to work. These files need some tweeking as per your PC before the scripts could be run.
- For demo, base_url.cfg, cred_access_id.cfg and cred_encoding_key.cfg can be left as they are, but they can be configured if user specific changes are made in the backend.
- Please change the path in output_directory.cfg to a folder of your choice on your local PC.
- The file "python_path.cfg" must be updated with the path of the python installation on your PC.
- Once these changes have been done, the CLI scripts can be used as per the sample commands given in "Sample_Calls.txt" file.



## About <a name="about"></a>

### Maintainers <a name="maintainers"></a>
[Ahmad Hassan Mirza](mailto:ahmadhasanmirza@gmail.com)

### Contributors <a name="contributors"></a>
[Ahmad Hassan Mirza](mailto:ahmadhasanmirza@gmail.com)

### 3rd Party Licenses <a name="3rd-party-licenses"></a>

| Name | License | Type |
|------|---------|------|
| Flask| [BSD](https://flask.palletsprojects.com/en/1.1.x/license/) | Dependency
| TensorFlow| [Apache](https://github.com/tensorflow/tensorflow/blob/master/LICENSE)| Dependency
| XLRD | [LICENSE](https://xlrd.readthedocs.io/en/latest/licenses.html) | Dependency
| LXML | [BSD](https://lxml.de/index.html#license) | Dependency
| PlantUML| [GNU](https://plantuml.com/de/license) | Dependency
| Docker | [Apache2.0](https://www.docker.com/components-licenses-dtr-1-4-ucp-1-1) | Dependency

### Used Artificial Intelligence <a name="used-AI"></a>

Tensorflow is used for object detection and training Machinelearning models.
