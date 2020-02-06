FROM ubuntu

#ARG github-username=""
#ARG github-password=""

RUN apt update
RUN apt install -y git python3 python3-pip wget curl
RUN pip3 install netaddr pyfiglet tqdm pyasn beautifulsoup4 requests

# Install docker
#RUN apt install -y \
#    apt-transport-https \
#    ca-certificates \
#    curl \
#    software-properties-common
#RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
#RUN add-apt-repository \
#   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
#   $(lsb_release -cs) \
#   stable"
#RUN apt update
#RUN apt install -y docker-ce

# Install routinator

RUN apt update
RUN apt install -y rsync build-essential
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
#RUN ls -a ~/
#RUN ls -a ~/.cargo
#RUN which source
#RUN source ~/.cargo/env
RUN /bin/bash -c "source ~/.cargo/env ; cargo install routinator"
RUN /bin/bash -c "source ~/.cargo/env ; routinator init --accept-arin-rpa"


######
## YOU SHOULD CHANGE THIS VAL!
######
RUN git clone "https://USERNAME:PASSWORD@github.com/taiji-k/roamon.git"
