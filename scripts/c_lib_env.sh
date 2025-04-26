#!/bin/bash
# Environment settings for Hydra News C libraries
export LD_LIBRARY_PATH="/home/ubuntu/hydra-news/c/lib:$LD_LIBRARY_PATH"
export CGO_CFLAGS="-I/home/ubuntu/hydra-news/c/include"
export CGO_LDFLAGS="-L/home/ubuntu/hydra-news/c/lib -lqzkp -lkyber -lfalcon -lcryptoadapter"
