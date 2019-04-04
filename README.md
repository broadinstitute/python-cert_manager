# python-cert_manager

This library provides a [Python][1] interface to the [Sectigo][2] Certificate Manager REST API.  python-cert_manager is open sourced under the [BSD 3-Clause license](LICENSE.txt).

[![CircleCI](https://circleci.com/gh/broadinstitute/python-cert_manager/tree/master.svg?style=svg)](https://circleci.com/gh/broadinstitute/python-cert_manager/tree/master)
[![codecov](https://codecov.io/gh/broadinstitute/python-cert_manager/branch/master/graph/badge.svg)](https://codecov.io/gh/broadinstitute/python-cert_manager)

## Basics

cert_manager still runs on Python 2.7, and Python >= 3.4

## Features

There are many API endpoints under Certificate Manager, and this library currently supports a subset of those endpoints.  The current list of written and tested endpoint classes includes:

* Organization (/organization)
* Person (/person)
* SSL (/ssl)

Other endpoints we hope to add in the near future:

* Client Administrator (/admin)
* Code Signing Certificates (/csod)
* Custom Fields (/customField)
* Domain Control Validation (/dcv)
* Device Certificates (/device)
* Discovery (/discovery)
* Domain (/domain)
* SMIME (/smime)

## Installing

You can use pip to install cert_manager:

```sh
pipenv install cert_manager
```

## Examples

This is a simple example that just shows initializing the `Client` object and using it to query the `Organization` and `SSL` endpoints:

```python
from cert_manager import Organization
from cert_manager import Client
from cert_manager import SSL

client = Client(
    base_url="https://cert-manager.com/api",
    login_uri="SomeOrg",
    username="your_username",
    password="your_password",
)

org = Organization(client=client)
ssl = SSL(client=client)

print(ssl.types)
print(org.all())
```

The most common process you would do, however, is enroll and then collect a certificate you want to order from the Certificate Manager:

```python
from time import sleep

from cert_manager import Organization
from cert_manager import Client
from cert_manager import SSL

client = Client(
    base_url="https://cert-manager.com/api",
    login_uri="SomeOrg",
    username="your_username",
    password="your_password",
)

# We need to enroll the certificate under an organization, so we will need to query the API for that
org = Organization(client=client)
# We need the SSL module to enroll the certificate
ssl = SSL(client=client)

cert_org = org.find(dept_name="MyDept")

result = ssl.enroll(cert_type_name="InCommon SSL (SHA-2)", csr="host.csr", term=365, org_id=cert_org[0]["id"])

# This is just for demonstration purposes.
# Doing a wait loop like this to poll for the certificate is not the best way to go about this.
while(True):
    # Collect the certificate from Sectigo
    try:
        cert_pem = ssl.collect(cert_id=result["sslId"], cert_format="x509CO")
        print(cert_pem)
        break
    except Pending:
        print("Certificate is still pending...sleeping for 60s")
        sleep(60)
        continue
    except Exception:
        # For some unexpected exception, exit
        break
```

## Contributing

Pull requests to add functionality and fix bugs are always welcome.  Please check the CONTRIBUTING.md for specifics on contributions.

### Testing

We try to have a high level of test coverage on the code.  Therefore, when adding anything to the repo, tests should be written to test a new feature or to test a bug fix so that there won't be a regression.  This library is setup to be pretty simple to build a working development environment using [Docker][4].  Therefore, it is suggested that you have [Docker][4] installed where you clone this repository to make development easier.

To start a development environment, you should be able to just run the `dev.sh` script.  This script will use the `Dockerfile` in this repository to build a [Docker][4] container with all the dependencies for development installed using [Pipenv][3].

```sh
./dev.sh
```

The first time you run the script, it should build the [Docker][4] image and then drop you into the container's shell.  The directory where you cloned this repository should be volume mounted in to `/usr/src`, which should also be the current working directory.  From there, you can make changes as you see fit.  Tests can be run from the `/usr/src` directory by simply typing `green` as [green][5] has been setup to with the correct parameters.

## Releases

Releases to the codebase are typically done using the [bump2version][6] tool.  This tool takes care of updating the version in all necessary files, updating its own configuration, and making a GitHub commit and tag.  We typically do version bumps as part of a PR, so you don't want to have [bump2version][6] tag the version at the same time it does the commit as commit hashes may change.  Therefore, to bump the version a patch level, one would run the command:

```sh
bump2version --verbose --no-tag patch
```

Once the PR is merged, you can then checkout the new master branch and tag it using the new version number that is now in `.bumpversion.cfg`:

```sh
git checkout master
git pull --rebase
git tag 1.0.0 -m 'Bump version: 0.1.0 → 1.0.0'
git push --tags
```

[1]: https://www.python.org/ "Python"
[2]: https://sectigo.com/ "Sectigo"
[3]: https://pipenv.readthedocs.io/en/latest/ "Pipenv"
[4]: https://www.docker.com/ "Docker"
[5]: https://github.com/CleanCut/green "green"
[6]: https://pypi.org/project/bump2version/ "bump2version"
