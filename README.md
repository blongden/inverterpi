# Solis inverter to MQTT publisher (read/write)

This runs on a raspberrypi (I use a zero but any device with a RS458 device will work fine) connected to the data port of my solis solar inverter. It's used to read modbus registers from the inverter and publish them to MQTT,
in my case running on home assistant. It can also subscribe to mqtt messages and write the values from mqtt to a defined modbus register, currently to change the charge mode and maximum amp rate.

It also logs data to a sqlite database and allows you to visualise the solar generation for the day through nginx though this code is incredibly simple and only exists really as a PoC of where I could go next with this.
