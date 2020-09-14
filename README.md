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

### colors.ini
Allows customize the UI. On the first run the program will dump here the actual settings.

## User interface Navigation

### Keys
* h : Show this help.    
* tab : cycles focus across UI components.    
* esc : Closes popup if open, otherwise closes the application.    
* cursors up/down : move across items in different lists.    
* cursor left/right: switch across pods/cronjobs/jobs/etc.     
* for nodes, namespaces, pods, cronjobs, etc:    
  * v: Opens viewer to display resource as Yaml
  * e: Opens editor to edit resource as Yaml.    
  * d: Deletes de selected resource.
  * c: Creates/updates a kubernetes resource from a yaml file.
* for pods:           
  * l: View pod logs.    
* for nodes:          
  * l: view labels for node.    
* for namespaces:     
  * enter: toggle namespace filter, all other views will filter its item by selected namespace.
