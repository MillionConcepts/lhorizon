This is a SPICE meta-kernel containing kernels to support lhorizon example usages.

File name                   	Contents
--------------------------  	-----------------------------
de440s.bsp						Planetary ephemeris
earth_latest_high_prec.bpc		Earth binary PCK
moon_080317.tf					Lunar FK
moon_pa_de421_1900-2050.bpc		Moon binary PCK
naif0012.tls                	Generic LSK
pck00010.tpc					generic NAIF kernel

\begindata

KERNELS_TO_LOAD = (
    'naif0012.tls'
    'moon_080317.tf'
    'de440s.bsp'
    'earth_latest_high_prec.bpc'
    'moon_pa_de421_1900-2050.bpc'
    'pck00010.tpc'
)

\begintext