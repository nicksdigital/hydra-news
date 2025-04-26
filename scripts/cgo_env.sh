#!/bin/bash
# Environment settings for Hydra News CGO
export CGO_ENABLED=1 
export LD_LIBRARY_PATH="/home/ubuntu/hydra-news/c/lib:$LD_LIBRARY_PATH"
export CGO_CFLAGS="-I/home/ubuntu/hydra-news/c/include"
export CGO_LDFLAGS="-L/home/ubuntu/hydra-news/c/lib -lqzkp -lkyber -lfalcon -lcryptoadapter -lcrypto -lssl"
