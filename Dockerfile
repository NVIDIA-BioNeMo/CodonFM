# To build a production image:
# docker build -t <image_name> --target production .
#
# To build a development image:
# docker build -t <image_name> --target development --build-arg USERNAME=$(whoami) --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g) .

ARG FROM_IMAGE_NAME=nvcr.io/nvidia/pytorch:26.09-py3@sha256:6e8ccc607fc2a51e3741667b86316a0889418ba8b78ed0ba96e8d282b648a7a6
FROM ${FROM_IMAGE_NAME} AS base

ENV CUDA_HOME=/usr/local/cuda
ENV PATH=$CUDA_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

WORKDIR /workspace/

# Copy the package metadata and source for installation.
COPY ./pyproject.toml ./README.md ./
COPY ./src ./src

# Install dependencies
RUN XFORMERS_SPEC="$(python -c 'import pathlib, tomllib; config = tomllib.loads(pathlib.Path("pyproject.toml").read_text()); pathlib.Path("/tmp/codonfm-ngc-constraints.txt").write_text("\n".join(config["tool"]["codonfm"]["ngc"]["constraints"]) + "\n"); print(next(dependency for dependency in config["project"]["dependencies"] if dependency.startswith("xformers==")))')" \
    && pip install --no-cache-dir --no-deps --index-url \
        https://download.pytorch.org/whl/cu130 "$XFORMERS_SPEC" \
    && PYGMENTS_SPEC="$(python -c 'import pathlib, tomllib; print(next(dependency for dependency in tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["dependencies"] if dependency.startswith("pygments==")))')" \
    && pip install --no-cache-dir --no-deps --ignore-installed "$PYGMENTS_SPEC" \
    && pip install --no-cache-dir --constraint /tmp/codonfm-ngc-constraints.txt . \
    && rm /tmp/codonfm-ngc-constraints.txt \
    && python -c "from importlib.metadata import version; assert version('torch') == '2.14.0a0+b2c75dd062.nv26.9.68203377'; assert version('torchvision') == '0.29.0a0+0fba2e84.nv26.9.68203377'; import xformers._cpp_lib as cpp; assert cpp._cpp_library_load_exception is None, cpp._cpp_library_load_exception"

# ----------------- Production Stage -----------------
FROM base AS production

WORKDIR /workspace/
COPY . .
# Add a CMD for production if you have a main script to run
# e.g., CMD ["python", "app.py"]


# ----------------- Development Stage -----------------
FROM base AS development

WORKDIR /workspace/

# Install development utilities.
RUN apt-get update \
    && apt-get install -y --no-install-recommends htop \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for development
ARG USERNAME
ARG USER_UID
ARG USER_GID

# Ensure build arguments are provided for development builds
RUN if [ -z "$USERNAME" ] || [ -z "$USER_UID" ] || [ -z "$USER_GID" ]; then \
        echo "Error: For development builds, you must provide USERNAME, USER_UID, and USER_GID build arguments." >&2; \
        exit 1; \
    fi

RUN groupadd --gid "$USER_GID" "$USERNAME" \
    && useradd -l --uid "$USER_UID" --gid "$USER_GID" -m "$USERNAME" \
    && chown -R "$USER_UID:$USER_GID" /workspace

# Switch to the non-root user
ENV HOME="/home/$USERNAME"
USER $USER_UID:$USER_GID
