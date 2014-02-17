#!/bin/bash

while read genre; do
	echo "Start fetching $genre..."
	python fetcher.py $genre &> logs/fetcher-${genre// /_} &
	disown
done
