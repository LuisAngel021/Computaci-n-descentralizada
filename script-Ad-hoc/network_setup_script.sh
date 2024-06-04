#!/bin/bash

# Nombre de la red ad-hoc y dirección MAC de ejemplo
SSID="TLON-ADHOC"
MAC_AP="02:1B:55:11:22:33"

# Detener NetworkManager para evitar conflictos
sudo systemctl stop NetworkManager

# Cargar el módulo batman-adv
sudo modprobe batman-adv

# Bajar la interfaz inalámbrica, configurar en modo ad-hoc y subirla
sudo ifconfig wlo1 down
sleep 2  # Pequeña pausa para asegurar que la interfaz está completamente baja
sudo iwconfig wlo1 mode ad-hoc
sudo iwconfig wlo1 essid $SSID ap $MAC_AP
sudo ifconfig wlo1 mtu 1532
sudo ifconfig wlo1 up

# Asignar una dirección IP estática
sudo ifconfig wlo1 192.168.1.1/24 up

# Agregar la interfaz al batman-adv
#sudo batctl if add wlp1s0
#sudo ifconfig bat0 up

# Reiniciar NetworkManager si es necesario
#sudo systemctl start NetworkManager

echo "Configuración de red ad-hoc con Batman-adv completada."

