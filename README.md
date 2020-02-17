Roamon-verify is developed and maintained by JPNIC.

## Documentation

Roamon-verify is a command line tool to show ROV results from BGP routes.
This tool uses routeviews archive as BGP routes and VRP (Validated ROA prefixes) from Routinator.

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
$ python3 roamon_verify_controller.py check

2200    192.93.148.0/24 INVALID
2200    194.57.0.0/16   VALID
2200    192.54.175.0/24 INVALID
2200    156.28.0.0/16   INVALID
...
```

### Verify specified AS's annoucing prefix

Verify all prefixes annouced by specified AS(es).
5745 and 63987 as examples.
```
$ python3 roamon_verify_controller.py check -asns 5745 63987

5745     192.93.148.0/24 VALID
63987    194.57.0.0/16   VALID
63987    192.54.175.0/24 INVALID
63987    156.28.0.0/16   INVALID
```

### Verify specified prefix(es)

Verify longest-matched prefix in BGP routes with specified prefix.
```
$ python3 roamon_verify_controller.py check -ips  194.57.0.0/16 192.93.148.0/24

194.57.0.0/16   VALID
192.93.148.0/24 INVALID
```

If shorter prefixes found from specified prefix(es) exist, it will be verified.
```
$ python3 roamon_verify_controller.py check -ips  194.57.0.0/20

194.56.0.0/15   NOT_ADVERTISED
```

Thanks

JPNIC roamon project is funded by Ministry of Internal Affairs and Communications, Japan (2019 Nov - 2020 Mar).
