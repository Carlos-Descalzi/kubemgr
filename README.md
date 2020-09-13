# kubemgr    
A little console based tool for managing Kubernetes clusters.    
    
![Screenhost](screenshot.png?raw=true "Screenhost")    
    
## Setup and install    
    
    python3 setup.sh install    

### Dependencies
    kubernetes>=11.0.0

## Configuration Files


The folder **$HOME/.kubemgr** is created the first time the program is executed with the following configuration files:

### kubemgr.ini
- editor: Absolute path to external editor program.
- viewer: Absolute path to external viewer program. If ommitted will use internal viewer.

### clusters.ini
This file configures the paths to kube config files of clusters.

    [Cluster Name]
    configfile=/path/to/kube/config
    timeout=requests timeout in seconds.

### colors.init
Allows customize the UI. On the first run the program will dump here the actual settings.
