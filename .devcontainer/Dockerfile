FROM ubuntu:24.04

ARG USERNAME=ubuntu

# Ensure apt is in non-interactive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

# Install dependencies.
RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get -y install --no-install-recommends \
    build-essential make libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev curl llvm libncursesw5-dev \
    xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    wget ca-certificates apt-utils locales git openssh-client && \
    locale-gen en_US.UTF-8

ENV DEBIAN_FRONTEND=dialog

USER $USERNAME

# Install pyenv to manage multiple python installations
RUN curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash && \
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init --path)"' >> ~/.bashrc && \
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# Not sure this is needed
SHELL ["/bin/bash","--login", "-c"]

# Stuff needed to make pyenv work correctly since the login shell
# above doesnt seem to run bachrc
ENV PYENV_ROOT="/home/${USERNAME}/.pyenv"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH


# Install the required python versions (this takes a bit usually) so we do lots of cacheing
RUN --mount=type=cache,target=/home/${USERNAME}/.pyenv/cache,uid=1000 \
    pyenv install -s 3.9.20 && \
    pyenv install -s 3.10.15 && \
    pyenv install -s 3.11.10 && \
    pyenv install -s 3.12.7 && \
    pyenv install -s 3.13.0 && \
    pyenv global 3.12.7 3.13.0 3.11.10 3.10.15 3.9.20 && \
    pyenv rehash

# Install poetry to manage our python project
RUN curl -sSL https://install.python-poetry.org | python3 -

# Install nox and pre-commit to automate CI stuff
RUN pip install --user --upgrade nox nox_poetry pre-commit
RUN git config --global --add safe.directory /workspaces/cf2tf
