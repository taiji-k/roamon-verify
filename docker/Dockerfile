FROM ubuntu

######
## YOU SHOULD CHANGE THIS VAL!
######
ARG github-username="YOUR_ACCOUNT_NAME"
ARG github-password="YOUR_PASSWORD"


RUN apt update
RUN apt install -y git python3 python3-pip
RUN pip3 install netaddr pyfiglet tqdm
RUN apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
RUN apt update
RUN apt install -y docker-ce
RUN git clone https://${github-username}:${github-password}@github.com/taiji-k/roamon.git
