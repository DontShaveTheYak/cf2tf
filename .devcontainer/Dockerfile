FROM ubuntu:24.04

ARG USERNAME=ubuntu

# Ensure apt is in non-interactive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

# Install dependencies.
# uv downloads prebuilt Python binaries, so no compiler toolchain is needed.
RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get -y install --no-install-recommends \
    curl ca-certificates apt-utils locales git openssh-client && \
    locale-gen en_US.UTF-8

ENV DEBIAN_FRONTEND=dialog

USER $USERNAME

# Install uv to manage Python installations and tools
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/home/${USERNAME}/.local/bin:$PATH"

# Projects default python version
RUN uv python install 3.13

# Install poetry to manage our python project
RUN uv tool install poetry && uv tool install nox --with nox-poetry && uv tool install pre-commit
