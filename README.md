## Documentation

Roamon-verify is a command line tool to show ROV results from BGP routes.
This tool uses routeviews archive as BGP routes and VRP (Validated ROA prefixes) from Routinator.
Roamon-verify is developed and maintained by JPNIC young dev team.

## Installation

### When putting into local directory

To clone from repository:
```
$ git clone https://github.com/taiji-k/roamon-verify.git
```

To install required packages:
```
$ pip3 install netaddr pyfiglet tqdm pyasn beautifulsoup4 requests
```

### When putting in Vagrant

To clone from repository:
```
$ git clone https://github.com/taiji-k/roamon-verify.git
```

To use in vagrant:
```
$ cd vagrant
$ vagrant up
$ vagrant ssh
>$ 
```

When works slow, increase resources allocated into VM. The parameter is in the middle of Vagrantfile.

### When putting in Docker

To clone from repository:
```
$ git clone https://github.com/taiji-k/roamon-verify.git
```

```
$ sudo docker build -t roamon ./docker
$ sudo docker run --rm -it roamon /bin/bash
>$ cd /roamon-verify
```

### Configurations

Specify a working directory and data directories in `config.ini`.

* `dir_path_data`: working directory used for putting downloaded files.
* `file_path_vrps`: VRP data (as pyasn readable format)
* `file_path_rib`: BGP data (as pyasn readable format)

## Usage

Note: In case of using `sudo`, $PATH value should be specified like `sudo env "PATH=$PATH" <your_command>`, to avoid error during execution. sudo does not path $PATH value with security reason.

### Fetch all data

You need to do at first.
It needs several minutes.
```
$ python3 roamon_verify_controller.py get --all
```

### VRPs and ROV

By comparing VRPs (Verified ROA Payloads) with BGP routes, difference will be checked as ROV (Route Origin Validation).

To see results:
* `VALID` means verified successfully.
* `INVALID` means error (different AS from ROA announced).
* `NOT_FOUND` means ROA is not created.
* `NOT_ADVERTISED` means no BGP routes.

### Verify all AS's prefix

Announced prefixes by all AS in VRPs are 'ROV'ed by default.

```
$ python3 roamon_verify_controller.py show

64511    192.168.1.0/24 VALID
64511    172.16.0.0/16 VALID
64510    10.0.0.0/8 INVALID
...
```

### Verify specified AS's annoucing prefix

Verify all prefixes annouced by specified AS(es).
64511 and 64510 as examples.
```
$ python3 roamon_verify_controller.py show -asn 64511 64510

64511    192.168.1.0/24 VALID
64510    10.0.0.0/8 INVALID
```

### Verify specified prefix(es)

Verify longest-matched prefix in BGP routes with specified prefix.
```
$ python3 roamon_verify_controller.py show -ip 192.168.1.0/24 10.0.0.0/8

192.168.1.0/24   VALID
10.0.0.0/8   INVALID
```

If shorter prefixes found from specified prefix(es) exist, it will be verified.
```
$ python3 roamon_verify_controller.py show -ip 172.16.1.0/20

172.16.1.0/15   NOT_ADVERTISED
```

Thanks

JPNIC roamon project is funded by Ministry of Internal Affairs and Communications, Japan (2019 Nov - 2020 Mar).
