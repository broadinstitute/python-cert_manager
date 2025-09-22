# Changelog

## [2.4.0](https://github.com/broadinstitute/python-cert_manager/tree/2.4.0) (2024-01-29)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/2.3.1...2.4.0)

**Implemented enhancements:**

- feat: migrate Python linting to Ruff
  [\#201](https://github.com/broadinstitute/python-cert_manager/pull/201)
  ([coreone](https://github.com/coreone))
- Implementation of the Person API
  [\#194](https://github.com/broadinstitute/python-cert_manager/pull/194)
  ([joachimBurket](https://github.com/joachimBurket))

**Fixed bugs:**

- fix: default encoding to ascii if not set
  [\#212](https://github.com/broadinstitute/python-cert_manager/pull/212)
  ([coreone](https://github.com/coreone))

## [2.3.1](https://github.com/broadinstitute/python-cert_manager/tree/2.3.1) (2023-06-05)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/2.3.0...2.3.1)

**Implemented enhancements:**

- Release 2.3.1
  [\#181](https://github.com/broadinstitute/python-cert_manager/pull/181)
  ([coreone](https://github.com/coreone))
- Fix linting and unit test bugs
  [\#156](https://github.com/broadinstitute/python-cert_manager/pull/156)
  ([coreone](https://github.com/coreone))

**Fixed bugs:**

- Fix pagination for ACMEAccount.find\(\)
  [\#173](https://github.com/broadinstitute/python-cert_manager/pull/173)
  ([jzmp](https://github.com/jzmp))

**Closed issues:**

- New release to support pagination
  [\#178](https://github.com/broadinstitute/python-cert_manager/issues/178)
- Version Bump needed
  [\#105](https://github.com/broadinstitute/python-cert_manager/issues/105)

## [2.3.0](https://github.com/broadinstitute/python-cert_manager/tree/2.3.0) (2022-09-12)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/2.2.0...2.3.0)

**Implemented enhancements:**

- Ssl count
  [\#128](https://github.com/broadinstitute/python-cert_manager/pull/128)
  ([MoIn4096](https://github.com/MoIn4096))
- Add renew method to SMIME
  [\#104](https://github.com/broadinstitute/python-cert_manager/pull/104)
  ([coreone](https://github.com/coreone))
- Added the Report module to support the Sectigo /report endpoint
  [\#95](https://github.com/broadinstitute/python-cert_manager/pull/95)
  ([NateWerner](https://github.com/NateWerner))
- Add support for domains endpoint
  [\#93](https://github.com/broadinstitute/python-cert_manager/pull/93)
  ([FISHMANPET](https://github.com/FISHMANPET))

**Fixed bugs:**

- Fix certificate SANs
  [\#94](https://github.com/broadinstitute/python-cert_manager/pull/94)
  ([coreone](https://github.com/coreone))

**Closed issues:**

- SAN not being included in the cert
  [\#89](https://github.com/broadinstitute/python-cert_manager/issues/89)
- Getting error 400 with sample from README
  [\#28](https://github.com/broadinstitute/python-cert_manager/issues/28)

## [2.2.0](https://github.com/broadinstitute/python-cert_manager/tree/2.2.0) (2022-03-01)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/2.1.0...2.2.0)

**Implemented enhancements:**

- Add functionality to work with Admin endpoint
  [\#87](https://github.com/broadinstitute/python-cert_manager/pull/87)
  ([FISHMANPET](https://github.com/FISHMANPET))

## [2.1.0](https://github.com/broadinstitute/python-cert_manager/tree/2.1.0) (2021-12-06)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/2.0.0...2.1.0)

**Implemented enhancements:**

- Move to f-strings
  [\#56](https://github.com/broadinstitute/python-cert_manager/pull/56)
  ([coreone](https://github.com/coreone))
- First implementation of smime calls
  [\#39](https://github.com/broadinstitute/python-cert_manager/pull/39)
  ([joachimBurket](https://github.com/joachimBurket))

**Closed issues:**

- New release
  [\#61](https://github.com/broadinstitute/python-cert_manager/issues/61)
- PyPi outdated version?
  [\#30](https://github.com/broadinstitute/python-cert_manager/issues/30)

## [2.0.0](https://github.com/broadinstitute/python-cert_manager/tree/2.0.0) (2021-05-26)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/1.0.0...2.0.0)

**Breaking changes:**

- Remove Python 2 support
  [\#17](https://github.com/broadinstitute/python-cert_manager/pull/17)
  ([coreone](https://github.com/coreone))
- CircleCI update and remove support for Python 3.4
  [\#11](https://github.com/broadinstitute/python-cert_manager/pull/11)
  ([coreone](https://github.com/coreone))

**Implemented enhancements:**

- Add extra format types
  [\#29](https://github.com/broadinstitute/python-cert_manager/pull/29)
  ([matejzero](https://github.com/matejzero))
- Add custom_fields handling to Certificates.enroll method
  [\#25](https://github.com/broadinstitute/python-cert_manager/pull/25)
  ([alextremblay](https://github.com/alextremblay))
- Style cleanup, reduce to one paginate method, Python 3.9 testing
  [\#23](https://github.com/broadinstitute/python-cert_manager/pull/23)
  ([coreone](https://github.com/coreone))
- Migrate to Poetry and GitHub Actions
  [\#21](https://github.com/broadinstitute/python-cert_manager/pull/21)
  ([coreone](https://github.com/coreone))
- feat: Add external requester field
  [\#19](https://github.com/broadinstitute/python-cert_manager/pull/19)
  ([ravanapel](https://github.com/ravanapel))
- Add support for ACME endpoint\(s\)
  [\#16](https://github.com/broadinstitute/python-cert_manager/pull/16)
  ([zmousm](https://github.com/zmousm))
- Adding more features support in SSL certificates
  [\#15](https://github.com/broadinstitute/python-cert_manager/pull/15)
  ([trolldbois](https://github.com/trolldbois))
- Start using CircleCI orb, disable TravisCI
  [\#10](https://github.com/broadinstitute/python-cert_manager/pull/10)
  ([coreone](https://github.com/coreone))

**Fixed bugs:**

- Remove custom HttpError exception
  [\#6](https://github.com/broadinstitute/python-cert_manager/issues/6)
- Fix \#26, JSONDecodeError when receiving HTTP 204 empty response from API
  [\#27](https://github.com/broadinstitute/python-cert_manager/pull/27)
  ([alextremblay](https://github.com/alextremblay))

**Closed issues:**

- JSONDecodeError when using the SSL.revoke method
  [\#26](https://github.com/broadinstitute/python-cert_manager/issues/26)
- Add support for custom fields to Certificates.enroll
  [\#24](https://github.com/broadinstitute/python-cert_manager/issues/24)
- Unable to specify External Requester
  [\#18](https://github.com/broadinstitute/python-cert_manager/issues/18)

## [1.0.0](https://github.com/broadinstitute/python-cert_manager/tree/1.0.0) (2019-04-04)

[Full Changelog](https://github.com/broadinstitute/python-cert_manager/compare/d2c8e5d7000efe2afdd8fcec69d2ef4033ebdd3f...1.0.0)

**Implemented enhancements:**

- Fix versioning of the package
  [\#2](https://github.com/broadinstitute/python-cert_manager/issues/2)
- Convert to 2.1 CircleCI config
  [\#8](https://github.com/broadinstitute/python-cert_manager/pull/8)
  ([coreone](https://github.com/coreone))
- Replace custom exception
  [\#7](https://github.com/broadinstitute/python-cert_manager/pull/7)
  ([coreone](https://github.com/coreone))
- Fix install and versioning, add user-agent
  [\#5](https://github.com/broadinstitute/python-cert_manager/pull/5)
  ([coreone](https://github.com/coreone))

**Fixed bugs:**

- Bugfixes [\#4](https://github.com/broadinstitute/python-cert_manager/pull/4)
  ([coreone](https://github.com/coreone))

\* _This Changelog was automatically generated by
[github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)_
