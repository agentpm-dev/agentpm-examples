#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 '<json-payload>'" >&2
  echo "   or: $0 --input-file <path>" >&2
  echo "   or: $0" >&2
}

if [[ "$#" -eq 0 ]]; then
  agentpm run @zack/slack-post-message
elif [[ "$#" -eq 1 ]]; then
  agentpm run @zack/slack-post-message --input "$1"
elif [[ "$#" -eq 2 && "$1" == "--input-file" ]]; then
  agentpm run @zack/slack-post-message --input-file "$2"
else
  usage
  exit 1
fi
