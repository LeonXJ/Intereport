#!/bin/bash

thresholds=("65" "70" "75")

drop_rates=("0.0" "0.2" "0.4" "0.6" "0.8")
for drop_rate in ${drop_rates[*]}; do
    echo ./ir_sim_bug_evaluator.py "../data/gnome/bug_gnome_bidf_snowball.cfg" g "$1" "../log/gnome/test_bidf_snowball_$drop_rate" "$drop_rate"
    #./ir_sim_bug_evaluator.py "../data/gnome/bug_gnome_bidf_snowball.cfg" g "$1" "../log/gnome/test_bidf_snowball_$drop_rate" "$drop_rate"
done;

drop_rates=("0.0" "0.2" "0.4" "0.6" "0.8")
for threshold in ${thresholds[*]}; do
    echo "threshold $threshold" >> $2
    for drop_rate in ${drop_rates[*]}; do
        echo ./ir_sim_bug_evaluator.py "../data/gnome/bug_gnome_bidf_snowball_ratio$threshold.cfg" r "../log/gnome/test_bidf_snowball_$drop_rate" "../log/gnome/res_bidf_snowball_ws_ratio$drop_rate_$threshold"
        ./ir_sim_bug_evaluator.py "../data/gnome/bug_gnome_bidf_snowball_ratio$threshold.cfg" r "../log/gnome/test_bidf_snowball_$drop_rate" "../log/gnome/res_bidf_snowball_ratio$drop_rate_$threshold"
        tail -1 "../log/gnome/res_bidf_snowball_ratio$drop_rate_$threshold" >> $2
    done;
done;
