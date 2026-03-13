# python-cert_manager

This library provides a [Python][1] interface to the [Sectigo][2] Certificate
Manager REST API. python-cert_manager is open sourced under the
[BSD 3-Clause license](LICENSE.txt).

![checks](https://github.com/broadinstitute/python-cert_manager/workflows/checks/badge.svg?branch=main)

## Basics

`cert_manager` runs on [Python][1] >= 3.9

## Features

There are many API endpoints under Certificate Manager, and this library
currently supports a subset of those endpoints. The current list of written and
tested endpoint classes includes:

- Public ACME Accounts (/acme/v2/accounts)
- Administrators (/admin)
- Domain Control Validation (/dcv)
- Domain (/domain)
- Organization (/organization)
- Persons (/person)
- Reports (/report)
- Client Certificates (/smime)
- SSL Certificates (/ssl)

## Installing

You can use pip to install cert_manager:

```shell
pip install cert_manager
```

## Authentication

Originally, Certificate Manager only allowed username and password, or client
certificate and key as methods of authenticating to the REST API. However,
OAuth2 is now supported via a completely different URL structure. This new model
can be used by setting the `client_id` and `client_secret` parameters to the
`Client` constructor. The Client ID and Client Secret are created via the UI in
[Sectigo][2]. Information on how to create the Client ID and Client Secret can
be found on
[How Do You Implement OAuth 2.0 for SCM](https://www.sectigo.com/knowledge-base/detail/implement-oauth-2-0-for-scm)
page.

**NOTE** When using OAuth2 authentication with the new API URLs, pay particular
attention to the version of the API you are using for each class. Typically the
version is `v1`, but there isn't a consistent version across all endpoints. You
may need to add `api_version` to many of the object instantiations for the API
to work correctly. A complete API reference can be found on the
[SCM DevX](https://scm.devx.sectigo.com/reference/) site. This, for example, is
the first code snippet in [Examples](#examples) rewritten for the new API
infrastructure:

## Examples

This is a simple example that just shows initializing the `Client` object to use
username and password authentication and then using it to query the
`Organization` and `SSL` endpoints:

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

The same basic code can be used with OAuth2 authentication parameters.

```python
from cert_manager import Organization
from cert_manager import Client
from cert_manager import SSL

client = Client(
  client_id="client-id-from-sectigo",
  client_secret="client-secret-from-sectigo",
)

org = Organization(client=client)
ssl = SSL(client=client, api_version="v2")

print(ssl.types)
print(org.all())
```

The most common process you would do, however, is enroll and then collect a
certificate you want to order from the Certificate Manager. This example uses
the parameters to authenticate using certificate (client) authentication:

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
with open("host.csr", "r") as filep:
    csr = filep.read()

result = ssl.enroll(cert_type_name="InCommon SSL (SHA-2)", csr=csr, term=365, org_id=cert_org[0]["id"])

# This is just for demonstration purposes.
# Doing a wait loop like this to poll for the certificate is not the best way to go about this.
while(True):
    # Collect the certificate from Sectigo
    try:
        cert_pem = ssl.collect(cert_id=result["sslId"], cert_format="x509CO")
        print(cert_pem)
        break
    except PendingError:
        print("Certificate is still pending...sleeping for 60s")
        sleep(60)
        continue
    except Exception:
        # For some unexpected exception, exit
        break
```

## Contributing

Pull requests to add functionality and fix bugs are always welcome. Please check
the CONTRIBUTING.md for specifics on contributions.

### Testing

We try to have a high level of test coverage on the code. Therefore, when adding
anything to the repo, tests should be written to test a new feature or to test a
bug fix so that there won't be a regression. This library is setup to be pretty
simple to build a working development environment using [Docker][4],
[Podman][7], or [Mise][8]. Therefore, it is suggested that you have [Docker][4]
[Podman][7], or [Mise][8] installed where you clone this repository to make
development easier.

To start a containerized development environment, you should be able to just run
the `dev.bash` script. This script will use the `Containerfile` in this
repository to build a container image with all the dependencies for development
installed using [Poetry][3].

```shell
./dev.bash
```

The first time you run the script, it should build the container image and then
drop you into the container's shell. The directory where you cloned this
repository should be volume mounted in to `/working`, which should also be the
current working directory. From there, you can make changes as you see fit.
Tests can be run from the `/working` directory by simply typing `pytest` as
[pytest][5] has been setup to with the correct parameters.

If you want to use [Mise][8], you should be able to set up the environment
simply with:

```shell
mise install
```

## Changelog

Going forward, the Changelog will be visible in the GitHub releases for this
repository. Changes for before version 3.0.0 can be found in the
[CHANGELOG.md](CHANGELOG.md) file within this repository.

## Releases

Version updates to the codebase are typically done using the [bump2version][6]
tool. This tool takes care of updating the version in all necessary files and
updating its own configuration. To bump the version a patch level, one would run
the command:

```shell
bump2version --verbose --no-commit --no-tag patch
```

Releases are now done through the GitHub
[Release](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
system. The easiest way to create a new release draft is using the GitHub CLI
(`gh`). For example, to create a new draft release for version `3.0.0` with
autogenerated notes:

```shell
gh release create 3.0.0 --draft --generate-notes --title 3.0.0
```

[1]: https://www.python.org/ "Python"
[2]: https://sectigo.com/ "Sectigo"
[3]: https://python-poetry.org/ "Poetry"
[4]: https://www.docker.com/ "Docker"
[5]: https://docs.pytest.org/en/stable/ "pytest"
[6]: https://pypi.org/project/bump2version/ "bump2version"
[7]: https://podman.io/ "Podman"
[8]: https://mise.jdx.dev/ "Mise"
