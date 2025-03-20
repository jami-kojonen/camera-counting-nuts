import pydobot, serial                              # Tuo pydobot ja serial kirjastot

device = pydobot.Dobot(port='COM18')                 # Yhdistä Dobot Magician -laitteeseen, korvaa 'COM8' oikealla portilla jonka helpoiten löydät DobotStudio-ohjelmalta

# Määritä kohdeasento
x, y, z, r = 100, 0, -30, 0                         # Alustaa muuttujat x, y, z ja r

start_z = 0                                         # Alkuperäinen Z-asennon arvo
delta_z = 67                                        # Z-asennon muutos kalibrointia varten

nopeus = 300                                        # Alustetaan nopeus
kiihtyvyys = 500                                    # Alustetaan kiihtyvyys
device.speed(nopeus, kiihtyvyys)                    # Aseta liikkeen nopeus ja kiihtyvyys


def vacuum_on():                                    # Funktio imupumpun kytkemiseksi päälle
    device.suck(True)                               # Kytkee imupumpun päälle


def vacuum_off():                                   # Funktio imupumpun kytkemiseksi pois
    device.suck(False)                              # Kytkee imupumpun pois päältä


def wait(ms):                                       # Funktio odottamiseen
    device.wait(ms)                                 # Odottaa määritetyn ajan millisekunteina


def center():                                       # Liikuttaa Dobotin keskiasentoon
    wait = True                                     # Odotus asetetaan todeksi
    device.move_to(219, 0, start_z, r, wait=wait)   # Liikuttaa Dobotin keskiasentoon


def left45():                                       # Liikuttaa Dobotin 45 astetta vasemmalle
    wait = True                                     # Odotus asetetaan todeksi
    device.move_to(150, 147, start_z, r, wait=wait) # Liikuttaa Dobotin vasemmalle


def right45():                                      # Liikuttaa Dobotin 45 astetta oikealle
    wait = True                                     # Odotus asetetaan todeksi
    device.move_to(144, -153, start_z, r, wait=wait)# Liikuttaa Dobotin oikealle


def down():                                         # Liikuttaa Dobotin ala-asentoon
    wait = True                                     # Odotus asetetaan todeksi
    (x1, y1, z1, r, j1, j2, j3, j4) = device.pose() # Hakee Dobotin nykyisen asennon
    device.move_to(x1, y1, start_z - delta_z, r, wait=wait)  # Liikuttaa Dobotin alas


def almost_down():                                  # Liikuttaa Dobotia lähes ala-asentoon
    delta = 10                                      # Vähennettävä arvo Z-asennosta
    wait = True                                     # Odotus asetetaan todeksi
    (x1, y1, z1, r, j1, j2, j3, j4) = device.pose() # Hakee Dobotin nykyisen asennon
    device.move_to(x1, y1, start_z - delta_z + delta, r, wait=wait)  # Liikuttaa Dobotin melkein alas


def up():                                           # Liikuttaa Dobotin ylä-asentoon
    wait = True                                     # Odotus asetetaan todeksi
    (x1, y1, z1, r, j1, j2, j3, j4) = device.pose() # Hakee Dobotin nykyisen asennon
    device.move_to(x1, y1, start_z, r, wait=wait)   # Liikuttaa Dobotin ylös


def main():                                         # Pääfunktio, joka suorittaa liikesarjan
    left45()                                        # Suorittaa vasemmalle käännön
    right45()                                       # Suorittaa oikealle käännön
    center()                                        # Siirtää Dobotin keskelle
    almost_down()                                   # Siirtää Dobotin melkein alas
    vacuum_on()                                     # Kytkee imupumpun päälle
    down()                                          # Siirtää Dobotin alas
    wait(500)                                       # Odottaa 500 millisekuntia
    up()                                            # Siirtää Dobotin ylös
    vacuum_off()                                    # Kytkee imupumpun pois



if __name__ == "__main__":                          # Jos skriptiä ajetaan suoraan, suorita main-funktio
    main()                                          # Suorita pääfunktio
