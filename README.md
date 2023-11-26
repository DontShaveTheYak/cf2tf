<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Python][python-shield]][pypi-url]
[![Latest][version-shield]][pypi-url]
[![Tests][test-shield]][test-url]
[![Coverage][codecov-shield]][codecov-url]
[![License][license-shield]][license-url]
<!-- [![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url] -->

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <!-- <a href="https://github.com/DontShaveTheYak/cf2tf">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a> -->

  <h3 align="center">Cloudformation 2 Terraform</h3>

  <p align="center">
    Convert your Cloudformation templates to Terraform.
    <!-- <br />
    <a href="https://github.com/DontShaveTheYak/cf2tf"><strong>Explore the docs »</strong></a>
    <br /> -->
    <br />
    <!-- <a href="https://github.com/DontShaveTheYak/cf2tf">View Demo</a>
    · -->
    <a href="https://github.com/DontShaveTheYak/cf2tf/issues">Report Bug</a>
    ·
    <a href="https://github.com/DontShaveTheYak/cf2tf/issues">Request Feature</a>
    ·
    <!-- <a href="https://la-tech.co/post/hypermodern-cloudformation/getting-started/">Guide</a> -->
  </p>
</p>



<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <!-- <li><a href="#license">License</a></li> -->
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>

## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

`cf2tf` is a CLI tool that attempts to convert Cloudformation to Terraform. We say attempt because it's not really possible to make the conversion with 100% accuracy (currently) because of several reasons mostly around converting a Map value in Cloudformation to the [correct value in HCL](https://github.com/hashicorp/hcl/issues/294#issuecomment-446388342).

## Getting Started

### Prerequisites

Cloudformation 2 Terraform requires python >= 3.8

### Installation

cf2tf is available as an easy to install pip package.
```sh
pip install cf2tf
```

If you are a [Homebrew](https://brew.sh/) user, can you install via brew:

```
$ brew install cf2tf
```

## Usage

To convert a template to terraform.
```sh
cf2tf my_template.yaml
```

This above command will dump all the terraform resources to stdout. You might want to save the results:
```sh
cf2tf my_template.yaml > main.tf
```

If you prefer to have each resource in its own file then:
```sh
cf2tf my_template.yaml -o some_dir
```
If `some_dir` doesn't exist, then it will be created for you. Then each resource type will be saved to a specific file (variables.tf, outputs.tf etc.).

## Roadmap

- Better conversion of Cloudformation Maps to Terraform (Maps, Block and json)
- Allow overides for specific resources
- Handle more advanced Cloudformation parameter types like SSM/Secrets manager
- Better handling of Recources/Properties that failed conversion
- Only download files needed, not entire terraform source code (200MB)

See the [open issues](https://github.com/DontShaveTheYak/cf2tf/issues) for a list of proposed features (and known issues).

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.



This project uses poetry to manage dependencies and pre-commit to run formatting, linting and tests. You will need to have both installed to your system as well as python 3.11.

1. Fork the Project
2. Setup the environment.
   This project uses vscode devcontainer to provide a completly configured development environment. If you are using vscode and have the remote container extension installed, you should be asked to use the devcontainer when you open this project inside of vscode.

   If you are not using devcontainers then you will need to have python installed. Install the `poetry`, `nox`, `nox_poetry` and `pre-commit` packages. Then run `poetry install` and `pre-commit install` commands.

   Most of the steps can be found in the [Dockerfile](.devcontainer/Dockerfile).
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- ## License

Distributed under the Apache-2.0 License. See [LICENSE.txt](./LICENSE.txt) for more information. -->

## Contact

Levi - [@shady_cuz](https://twitter.com/shady_cuz)

<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements
* [Cloud-Radar](https://github.com/DontShaveTheYak/cloud-radar) - A unit/functional testing framework for Cloudformation templates.
* [cfn_tools from cfn-flip](https://github.com/awslabs/aws-cfn-template-flip) - Used to convert template from yml to python dict.
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template) - The name says it all.

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[python-shield]: https://img.shields.io/pypi/pyversions/cf2tf?style=for-the-badge
[version-shield]: https://img.shields.io/pypi/v/cf2tf?label=latest&style=for-the-badge
[pypi-url]: https://pypi.org/project/cf2tf/
[test-shield]: https://img.shields.io/github/actions/workflow/status/DontShaveTheYak/cf2tf/test.yml?label=Tests&style=for-the-badge
[test-url]: https://github.com/DontShaveTheYak/cf2tf/actions?query=workflow%3ATests+branch%3Amaster
[codecov-shield]: https://img.shields.io/codecov/c/gh/DontShaveTheYak/cf2tf/master?color=green&style=for-the-badge&token=bfF18q99Fl
[codecov-url]: https://codecov.io/gh/DontShaveTheYak/cf2tf
[contributors-shield]: https://img.shields.io/github/contributors/DontShaveTheYak/cf2tf.svg?style=for-the-badge
[contributors-url]: https://github.com/DontShaveTheYak/cf2tf/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/DontShaveTheYak/cf2tf.svg?style=for-the-badge
[forks-url]: https://github.com/DontShaveTheYak/cf2tf/network/members
[stars-shield]: https://img.shields.io/github/stars/DontShaveTheYak/cf2tf.svg?style=for-the-badge
[stars-url]: https://github.com/DontShaveTheYak/cf2tf/stargazers
[issues-shield]: https://img.shields.io/github/issues/DontShaveTheYak/cf2tf.svg?style=for-the-badge
[issues-url]: https://github.com/DontShaveTheYak/cf2tf/issues
[license-shield]: https://img.shields.io/github/license/DontShaveTheYak/cf2tf.svg?style=for-the-badge
[license-url]: https://github.com/DontShaveTheYak/cf2tf/blob/master/LICENSE.txt
[product-screenshot]: images/screenshot.png
