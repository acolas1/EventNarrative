#!/bin/bash

input_files=`ls $1*.json | sort -V`
output_dir=$2
for input_file in $input_files
do
    python modify_full_TEXT.py -input $input_file -output_dir $2
done