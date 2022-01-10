#!/bin/bash

if [ "$#" -lt 2 ]; then
  echo "./train_event.sh <model> <gpu_id>"
  exit 2
fi

bash event/finetune_graph2text_bart.sh ${1} ${2}







