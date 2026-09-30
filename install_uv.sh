#!/usr/bin/env bash
# install uv
case "$(uname)" in 
    Darwin | Linux) 
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ;; 
    *) 
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" 
        ;; 
esac