#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ge 2 && "$1" == "--input-file" ]]; then
  agentpm run @zack/slack-post-message --input-file "$2"
elif [[ $# -ge 1 ]]; then
  agentpm run @zack/slack-post-message --input "$1"
else
  agentpm run @zack/slack-post-message
fi
