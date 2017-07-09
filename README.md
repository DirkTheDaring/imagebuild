# imagebuild

imagebuild creates a fresh installation from a fedora/centos repository in a target directory.
If you also have docker available, it uploads this as a fresh docker image to your local docker repo.
This way you can get a quick base installation, without having a dependency on the slowly 
updated images from fedora or centos.

# How to install

it works with python / python3. Default is python.

On some distributions you need to install pyyaml first.
Here are your "options". For installing _one_ package  

CENTOS
-------
    # For python 
    yum install PyYAML
    #For python3 
    yum install python3-PyYAML

FEDORA
------
    # For python 
    dnf install PyYAML
    #For python3 
    dnf install python3-PyYAML


PIP
---
    # python 
    pip install pyyaml
    # python3
    pip3 install pyyaml



# How to run

If you run the script on Fedora or Centos, the script tries to figure out which version you are using and will create this as default image

    ./imagebuild.py    # This will build a fedora/centos image of the same version as your host and put it /var/lib/build/<os-name>-<os-version>

If you want to create a different version / distribution, you need to use yaml configuration.

    ./imagebuild.py fedora-26-full.yaml   # will build a version configured in the yaml file


# Open issues /cleanup

The directory where the distribution will be build, will not be cleaned up automatically, therefore a manual removal is necessary if you want to do a fresh build.
therwise, subsequent builds whill just update the image in the directory.

    rm -rf /var/lib/build/<os-name>-<os-version>    



