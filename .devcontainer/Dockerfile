FROM rocker/r-ver:latest

# Install system dependencies for R and Python
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgit2-dev \
    sudo \
    git \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN Rscript -e "install.packages(c('tidyverse', 'data.table', 'devtools'), repos = 'https://cloud.r-project.org/')"

# Install Python packages
RUN pip3 install numpy pandas matplotlib

# Clean up
RUN apt-get clean
