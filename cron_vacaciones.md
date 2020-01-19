# Install:
# (crontab -l ; cat ./cron_vacaciones.md) | crontab

33 18 * * * wget "http://192.168.1.50:1234/ZMF/thing/Livingroom Table Lamp/light_on"
36 22 * * * wget "http://192.168.1.50:1234/ZMF/thing/Livingroom Table Lamp/light_off"
43 18 * * * wget "http://192.168.1.50:1234/ZMF/thing/Pieza/light_on"
56 23 * * * wget "http://192.168.1.50:1234/ZMF/thing/Pieza/light_off"
16 06 * * * wget "http://192.168.1.50:1234/ZMF/thing/Pieza/light_on"
26 09 * * * wget "http://192.168.1.50:1234/ZMF/thing/Pieza/light_off"


