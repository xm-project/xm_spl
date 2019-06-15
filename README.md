# xm_spl
Speech location section for xm robot

## Description
科大讯飞的开发版在离线情况下可以借由唤醒操作（指令：小萌小萌）唤醒，并在唤醒的同时将唤醒人的方位（平面角度）通过串口发送到上位机，这个package主要
解析串口数据来得到说话人的方位。

## Use
rosrun xm_spl SplNode.py
