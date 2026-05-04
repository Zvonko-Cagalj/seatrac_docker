FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV WS=/ws

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    git \
    curl \
    wget \
    nano \
    vim \
    iputils-ping \
    net-tools \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    libboost-all-dev \
    ros-humble-cv-bridge \
    ros-humble-image-transport \
    ros-humble-camera-info-manager \
    ros-humble-tf2-ros \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init || true
RUN rosdep update || true

RUN python3 -m pip install --no-cache-dir \
    grpcio==1.44.0 \
    protobuf==3.17.3 \
    rospkg \
    opencv-python

RUN mkdir -p ${WS}/src

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc && \
    echo "[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash" >> /root/.bashrc

WORKDIR ${WS}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]