# kubemgr    
A little console based tool for managing Kubernetes clusters.    
    
![Screenhost](screenshot.png?raw=true "Screenhost")    

## Features
* Allow connect to multiple clusters 
* Filters per view or global
* Add, view, edit and delete resources
* Customize view via Jinja templates
    
## Setup and install    
    
    sudo python3 setup.sh install    
    or
    python3 setup.sh install --prefix=[Installation path prefix, for example $HOME/.local]

### Dependencies
* cdtui: Requires install from sources from this location: https://github.com/Carlos-Descalzi/cdtui
* kubernetes>=11.0.0
* Jinja2==2.11.2

### Install
    sudo python3 setup.py install    
    or, for local setup:
    python3 setup.py install --prefix=$HOME/.local

## Configuration Files

The folder **$HOME/.kubemgr** is created the first time the program is executed with the following configuration files:

### kubemgr.ini
- editor: Absolute path to external editor program.
- viewer: Absolute path to external viewer program. If ommitted will use internal viewer.

### Tabs.
It is possible to customize visible resources by adding them as tabs.
Check the default configuration file for details.

### clusters.ini
This file configures the paths to kube config files of clusters.
The first execution will attempt to locate the current cluster configuration, by checking KUBECONFIG environment variable, or for the file $HOME/.kube/config

    [Cluster Name]
    configfile=/path/to/kube/config
    timeout=requests timeout in seconds.


### colors.ini
Allows customize the UI. On the first run the program will dump here the actual settings.

## User interface and Navigation

### Keys
* h : Shows help window.    
* tab : cycles focus across UI components.    
* esc : Closes popup if open, otherwise closes the application.    
* cursors up/down : move across items in different lists.    
* cursor left/right: switch across pods/cronjobs/jobs/etc.     
* for nodes, namespaces, pods, cronjobs, etc:    
  * v: Opens viewer to display resource as Yaml
  * e: Opens editor to edit resource as Yaml.    
  * d: Deletes de selected resource.
  * c: Creates/updates a kubernetes resource from a yaml file.
  * f: Edit filter for current view.
  * F: Edit global filter for all views.
* for clusters:
  * enter: set current cluster.
* for pods:           
  * l: View pod logs.    
* for nodes:          
  * l: view labels for node.    
* for namespaces:     
  * enter: toggle namespace filter, all other views will filter its item by selected namespace.

### Indications
#### Cluster Status
* (C) green: Cluster connected.
* <X> red: Error on connection. Pressing enter on marked cluster will show the error.
* ...: Connecting

#### Namespaces
* (F): The namespace is used for filtering views.

### Editing Files.
The application relies on an external editor for editing resource files. Check configuration section for more details.

### Filtering
Both filters and global filters use Jinja to write expressions for filtering resources.
The template files must always evaluate to "True" for a given resource to allow view it.
The resource being filtered is exposed in a variable called **item**, which contents match the structure of Yaml resource files.

For example, a global filter for resources with a given name prefix:

    {{ item.metadata.name[0:3] == 'id-' }}

Filters are persistent, so once you exit and launch again the application you will still see them.

### Resource list rendering.
How items in resource list are rendered can be also customized via Jinja.
In **$HOME/.kubemgr/item-templates** there will be all actual templates for resources.
To add a new resource template, the name must be the resource Kind + '.tpl'.

### Jinja utilities
Some helper functions are introduced in Jinja context:
* parse_mem(str): Parses a memory value and returns it as integer in bytes
* format_mem(int): Formats a given memory value into NNKB, NNMB, NNGB. This is actually more useful for item rendering than for filtering.
* ts_parse(str): Parses a string representation of a timestamp into a datetime object.
* age(str): Formats a given timestamp string into days and hours.
* str(v): Returns string representation as actual python str.
* int(str): Returns integer value from its string representation.


