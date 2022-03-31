#!/bin/bash

if [ "$#" -lt 2 ]; then
  echo "./train_event_t5.sh <model> <gpu_id>"
  exit 2
fi

bash event/finetune_graph2text_t5.sh ${1} ${2}







