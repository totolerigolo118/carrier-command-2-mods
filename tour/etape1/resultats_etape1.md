# Etape 1 : empreintes dans carrier_command.exe (resultat brut du script)

Script : `tour/outils/etape1_empreintes.py` (lecture seule). Fichier lu : copie de sauvegarde.

- sha256 : `1C9A01C3007CB2BEC2A04D716812CF9F24C87EFA11056395C89DDD7D2C341026`
- taille fichier : 11353600 ; ImageBase 0x400000 ; horodatage PE 0x6a36c177

| section | adresse | taille virtuelle | taille fichier | exec |
|---|---|---|---|---|
| .text | 0x00401000 | 0x8d4adb | 0x8d4c00 | oui |
| .rdata | 0x00cd6000 | 0x146968 | 0x146a00 |  |
| .data | 0x00e1d000 | 0x3b87c | 0x1be00 |  |
| _RDATA | 0x00e59000 | 0x2608 | 0x2800 |  |
| .rsrc | 0x00e5c000 | 0x4aae0 | 0x4ac00 |  |
| .reloc | 0x00ea7000 | 0x4f1c4 | 0x4f200 |  |

## 1. Constantes flottantes : ou elles sont rangees, combien de lectures dans le code

| valeur | bits | copies en donnees | lectures dans le code (total) |
|---|---|---|---|
| 0.4 | 0x3ECCCCCD | 4 | 49 |
| 0.8 | 0x3F4CCCCD | 10 | 50 |
| 0.6 | 0x3F19999A | 4 | 28 |
| 0.2 | 0x3E4CCCCD | 5 | 217 |
| 0.025 | 0x3CCCCCCD | 1 | 55 |
| -0.025 | 0xBCCCCCCD | 1 | 2 |
| 0.001 | 0x3A83126F | 6 | 772 |
| 1/6 | 0x3E2AAAAB | 2 | 8 |
| -1/6 | 0xBE2AAAAB | 17 | 3 |
| 1/30 | 0x3D088889 | 1 | 32 |
| -1/30 | 0xBD088889 | 1 | 4 |
| 0.04 | 0x3D23D70A | 4 | 14 |
| -0.04 | 0xBD23D70A | 1 | 3 |
| 0.05 | 0x3D4CCCCD | 4 | 145 |
| 2.5 | 0x40200000 | 11 | 17 |
| 11.0 | 0x41300000 | 6 | 2 |
| 12.0 | 0x41400000 | 6 | 30 |
| 30.0 | 0x41F00000 | 3 | 72 |
| 0.01 | 0x3C23D70A | 3 | 137 |
| 0.1 | 0x3DCCCCCD | 6 | 212 |
| 0.5 | 0x3F000000 | 95 | 1533 |
| 48 | 0x42400000 | 1 | 2 |
| 72 | 0x42900000 | 2 | 1 |
| 144 | 0x43100000 | 1 | 1 |
| 600 | 0x44160000 | 1 | 9 |
| 1800 | 0x44E10000 | 0 | 0 |
| -1800 | 0xC4E10000 | 1 | 2 |
| 80 | 0x42A00000 | 1 | 6 |
| 1200 | 0x44960000 | 3 | 7 |
| 1000 | 0x447A0000 | 5 | 66 |
| -1000 | 0xC47A0000 | 1 | 2 |
| 50 | 0x42480000 | 3 | 23 |
| 100 | 0x42C80000 | 1 | 91 |
| 120 | 0x42F00000 | 1 | 33 |
| 20 | 0x41A00000 | 1 | 32 |
| 70 | 0x428C0000 | 2 | 2 |
| 23.5 | 0x41BC0000 | 0 | 0 |
| -2.0 | 0xC0000000 | 105 | 41 |

## 2. Detail des lectures (limite a 60 par constante)

### 0.4 (copies en donnees : 0x00db72a4, 0x00db845c, 0x00db8604, 0x00db8834)
- 0x00457b1c [.text] mulss xmm1  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 0d a4 72 db 00`
- 0x0046ec35 [.text] movss xmm2  (constante 0x00db72a4)  octets : `59 c2 f3 0f 10 15 a4 72 db 00`
- 0x00479245 [.text] mulss xmm4  (constante 0x00db72a4)  octets : `00 50 f3 0f 59 25 a4 72 db 00`
- 0x00487377 [.text] mulss xmm5  (constante 0x00db72a4)  octets : `24 48 f3 0f 59 2d a4 72 db 00`
- 0x00487e35 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `28 c6 f3 0f 59 05 a4 72 db 00`
- 0x004e9d70 [.text] movss xmm3  (constante 0x00db72a4)  octets : `24 68 f3 0f 10 1d a4 72 db 00`
- 0x004eb7ba [.text] movss xmm3  (constante 0x00db72a4)  octets : `00 00 f3 0f 10 1d a4 72 db 00`
- 0x004ecd04 [.text] movss xmm3  (constante 0x00db72a4)  octets : `f4 ff f3 0f 10 1d a4 72 db 00`
- 0x004ef63b [.text] mulss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 05 a4 72 db 00`
- 0x0058b71c [.text] mulss xmm1  (constante 0x00db72a4)  octets : `ff ff f3 0f 59 0d a4 72 db 00`
- 0x0058cc33 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `7e 14 f3 0f 59 05 a4 72 db 00`
- 0x0058cd03 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 05 a4 72 db 00`
- 0x0058d073 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `00 00 f3 0f 59 05 a4 72 db 00`
- 0x0058d382 [.text] addss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 58 05 a4 72 db 00`
- 0x0058d53c [.text] mulss xmm0  (constante 0x00db72a4)  octets : `00 00 f3 0f 59 05 a4 72 db 00`
- 0x0058d602 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 05 a4 72 db 00`
- 0x0058d6bd [.text] mulss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 05 a4 72 db 00`
- 0x0058d72c [.text] mulss xmm0  (constante 0x00db72a4)  octets : `45 0c f3 0f 59 05 a4 72 db 00`
- 0x0058e61d [.text] mulss xmm1  (constante 0x00db72a4)  octets : `4d ec f3 0f 59 0d a4 72 db 00`
- 0x0058e65f [.text] mulss xmm1  (constante 0x00db72a4)  octets : `00 00 f3 0f 59 0d a4 72 db 00`
- 0x005e625d [.text] subss xmm1  (constante 0x00db72a4)  octets : `28 c8 f3 0f 5c 0d a4 72 db 00`
- 0x00629a12 [.text] mulss xmm7  (constante 0x00db72a4)  octets : `42 ca f3 0f 59 3d a4 72 db 00`
- 0x006308b2 [.text] mulss xmm2  (constante 0x00db72a4)  octets : `5b c9 f3 0f 59 15 a4 72 db 00`
- 0x0065ba74 [.text] addss xmm0  (constante 0x00db72a4)  octets : `00 00 f3 0f 58 05 a4 72 db 00`
- 0x00683e58 [.text] mulss xmm2  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 15 a4 72 db 00`
- 0x0068a346 [.text] mulss xmm2  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 15 a4 72 db 00`
- 0x0071ae7c [.text] comiss xmm0  (constante 0x00db72a4)  octets : `04 00 00 0f 2f 05 a4 72 db 00`
- 0x0071de81 [.text] mulss xmm7  (constante 0x00db72a4)  octets : `00 00 f3 0f 59 3d a4 72 db 00`
- 0x0071f164 [.text] mulss xmm1  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 0d a4 72 db 00`
- 0x00723a42 [.text] comiss xmm0  (constante 0x00db72a4)  octets : `73 ce ff 0f 2f 05 a4 72 db 00`
- 0x00724c92 [.text] minss xmm1  (constante 0x00db72a4)  octets : `db 00 f3 0f 5d 0d a4 72 db 00`
- 0x00725e9b [.text] addss xmm0  (constante 0x00db72a4)  octets : `75 10 f3 0f 58 05 a4 72 db 00`
- 0x0072888b [.text] addss xmm0  (constante 0x00db72a4)  octets : `75 10 f3 0f 58 05 a4 72 db 00`
- 0x00749dd0 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 05 a4 72 db 00`
- 0x0074a3f2 [.text] mulss xmm0  (constante 0x00db72a4)  octets : `c4 08 f3 0f 59 05 a4 72 db 00`
- 0x00765b9a [.text] movss xmm0  (constante 0x00db72a4)  octets : `8b f0 f3 0f 10 05 a4 72 db 00`
- 0x00765d7e [.text] movss xmm0  (constante 0x00db72a4)  octets : `ff ff f3 0f 10 05 a4 72 db 00`
- 0x007ebca7 [.text] addss xmm0  (constante 0x00db72a4)  octets : `cc 3d f3 0f 58 05 a4 72 db 00`
- 0x00830383 [.text] mulss xmm3  (constante 0x00db72a4)  octets : `00 00 f3 0f 59 1d a4 72 db 00`
- 0x0083038b [.text] mulss xmm0  (constante 0x00db72a4)  octets : `db 00 f3 0f 59 05 a4 72 db 00`
- 0x0086bd38 [.text] movss xmm3  (constante 0x00db72a4)  octets : `14 c3 f3 0f 10 1d a4 72 db 00`
- 0x008f02c0 [.text] movss xmm3  (constante 0x00db72a4)  octets : `ec 3c f3 0f 10 1d a4 72 db 00`
- 0x008f31d2 [.text] mulss xmm5  (constante 0x00db72a4)  octets : `00 00 f3 0f 59 2d a4 72 db 00`
- 0x008f3221 [.text] mulss xmm2  (constante 0x00db72a4)  octets : `28 d9 f3 0f 59 15 a4 72 db 00`
- 0x00c14fac [.text] mulss xmm2  (constante 0x00db72a4)  octets : `59 d0 f3 0f 59 15 a4 72 db 00`
- 0x00c1523c [.text] mulss xmm1  (constante 0x00db72a4)  octets : `41 30 f3 0f 59 0d a4 72 db 00`
- 0x00c156a7 [.text] movss xmm0  (constante 0x00db72a4)  octets : `eb 08 f3 0f 10 05 a4 72 db 00`
- 0x00c1571f [.text] mulss xmm1  (constante 0x00db72a4)  octets : `4e 30 f3 0f 59 0d a4 72 db 00`
- 0x00c1683e [.text] mulss xmm2  (constante 0x00db72a4)  octets : `59 d0 f3 0f 59 15 a4 72 db 00`

### 0.8 (copies en donnees : 0x00ce70a0, 0x00db73a4, 0x00db83e0, 0x00db83e4, 0x00db83e8, 0x00db8420)
- 0x00462edb [.text] mulss xmm7  (constante 0x00db73a4)  octets : `28 c7 f3 0f 59 3d a4 73 db 00`
- 0x00462efc [.text] mulss xmm1  (constante 0x00db73a4)  octets : `58 fc f3 0f 59 0d a4 73 db 00`
- 0x0046381e [.text] movss xmm0  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 05 a4 73 db 00`
- 0x004638f9 [.text] mulss xmm3  (constante 0x00db73a4)  octets : `00 00 f3 0f 59 1d a4 73 db 00`
- 0x0046eae1 [.text] movss xmm4  (constante 0x00db73a4)  octets : `db 00 f3 0f 10 25 a4 73 db 00`
- 0x0046edd9 [.text] movaps xmm0  (constante 0x00db83e0)  octets : `03 00 00 0f 28 05 e0 83 db 00`
- 0x0046ede7 [.text] movaps xmm0  (constante 0x00db8420)  octets : `03 00 00 0f 28 05 20 84 db 00`
- 0x00480073 [.text] movss xmm0  (constante 0x00db73a4)  octets : `7f 00 f3 0f 10 05 a4 73 db 00`
- 0x0058769d [.text] movss xmm2  (constante 0x00db73a4)  octets : `ff ff f3 0f 10 15 a4 73 db 00`
- 0x0058b06d [.text] movss xmm0  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 05 a4 73 db 00`
- 0x0058ce28 [.text] addss xmm0  (constante 0x00db73a4)  octets : `db 00 f3 0f 58 05 a4 73 db 00`
- 0x0058d6f4 [.text] addss xmm0  (constante 0x00db73a4)  octets : `db 00 f3 0f 58 05 a4 73 db 00`
- 0x005d80f8 [.text] mulss xmm3  (constante 0x00db73a4)  octets : `42 ca f3 0f 59 1d a4 73 db 00`
- 0x006559ad [.text] movss xmm3  (constante 0x00db73a4)  octets : `55 ec f3 0f 10 1d a4 73 db 00`
- 0x0065e9b0 [.text] comiss xmm0  (constante 0x00db73a4)  octets : `0f 58 c2 0f 2f 05 a4 73 db 00`
- 0x006b449b [.text] comiss xmm2  (constante 0x00db73a4)  octets : `0f 58 d1 0f 2f 15 a4 73 db 00`
- 0x006b550b [.text] comiss xmm2  (constante 0x00db73a4)  octets : `0f 58 d1 0f 2f 15 a4 73 db 00`
- 0x006b6bef [.text] comiss xmm2  (constante 0x00db73a4)  octets : `0f 58 d1 0f 2f 15 a4 73 db 00`
- 0x0071b255 [.text] movss xmm1  (constante 0x00db73a4)  octets : `ff ff f3 0f 10 0d a4 73 db 00`
- 0x0072038d [.text] maxss xmm0  (constante 0x00db73a4)  octets : `45 1c f3 0f 5f 05 a4 73 db 00`
- 0x00724d34 [.text] minss xmm0  (constante 0x00db73a4)  octets : `00 00 f3 0f 5d 05 a4 73 db 00`
- 0x0072c773 [.text] mulss xmm0  (constante 0x00db73a4)  octets : `5d c4 f3 0f 59 05 a4 73 db 00`
- 0x0072d71a [.text] minss xmm0  (constante 0x00db73a4)  octets : `5f c5 f3 0f 5d 05 a4 73 db 00`
- 0x0073d0d2 [.text] movss xmm1  (constante 0x00db73a4)  octets : `ff ff f3 0f 10 0d a4 73 db 00`
- 0x0073d23d [.text] movss xmm1  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 0d a4 73 db 00`
- 0x0073d341 [.text] movss xmm2  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 15 a4 73 db 00`
- 0x0073d4b2 [.text] movss xmm2  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 15 a4 73 db 00`
- 0x0073dec8 [.text] movss xmm2  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 15 a4 73 db 00`
- 0x00763255 [.text] mulss xmm2  (constante 0x00db73a4)  octets : `c4 0c f3 0f 59 15 a4 73 db 00`
- 0x00763642 [.text] movss xmm2  (constante 0x00db73a4)  octets : `ff ff f3 0f 10 15 a4 73 db 00`
- 0x00765922 [.text] mulss xmm2  (constante 0x00db73a4)  octets : `c4 08 f3 0f 59 15 a4 73 db 00`
- 0x00765d26 [.text] movss xmm0  (constante 0x00db73a4)  octets : `db 00 f3 0f 10 05 a4 73 db 00`
- 0x00869caa [.text] movss xmm4  (constante 0x00db73a4)  octets : `db 00 f3 0f 10 25 a4 73 db 00`
- 0x0086b84f [.text] movss xmm4  (constante 0x00db73a4)  octets : `db 00 f3 0f 10 25 a4 73 db 00`
- 0x008f2af7 [.text] movss xmm4  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 25 a4 73 db 00`
- 0x00a0e9b7 [.text] movss xmm1  (constante 0x00db73a4)  octets : `45 40 f3 0f 10 0d a4 73 db 00`
- 0x00a16c7a [.text] movss xmm1  (constante 0x00db73a4)  octets : `14 d9 f3 0f 10 0d a4 73 db 00`
- 0x00a35a9f [.text] movss xmm2  (constante 0x00db73a4)  octets : `14 ca f3 0f 10 15 a4 73 db 00`
- 0x00a97229 [.text] movss xmm2  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 15 a4 73 db 00`
- 0x00a98d32 [.text] movss xmm0  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 05 a4 73 db 00`
- 0x00a9ee42 [.text] movss xmm1  (constante 0x00db73a4)  octets : `55 08 f3 0f 10 0d a4 73 db 00`
- 0x00abcd38 [.text] movss xmm1  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 0d a4 73 db 00`
- 0x00ac8dc9 [.text] movss xmm0  (constante 0x00db73a4)  octets : `45 10 f3 0f 10 05 a4 73 db 00`
- 0x00acac57 [.text] movss xmm0  (constante 0x00db73a4)  octets : `00 00 f3 0f 10 05 a4 73 db 00`
- 0x00b05fb0 [.text] movss xmm0  (constante 0x00db73a4)  octets : `58 da f3 0f 10 05 a4 73 db 00`
- 0x00b12043 [.text] movss xmm0  (constante 0x00db73a4)  octets : `5d d0 f3 0f 10 05 a4 73 db 00`
- 0x00b141d8 [.text] movss xmm0  (constante 0x00db73a4)  octets : `5d d8 f3 0f 10 05 a4 73 db 00`
- 0x00b17dfd [.text] movss xmm0  (constante 0x00db73a4)  octets : `5d c8 f3 0f 10 05 a4 73 db 00`
- 0x00b1c4e5 [.text] movss xmm5  (constante 0x00db73a4)  octets : `5d cd f3 0f 10 2d a4 73 db 00`
- 0x00bf8bc0 [.text] ?   (constante 0x00ce70a0)  octets : `14 f3 0f 10 04 8d a0 70 ce 00`

### 0.6 (copies en donnees : 0x00ce70a8, 0x00db731c, 0x00db86c4, 0x00db8818)
- 0x00461bfd [.text] mulss xmm0  (constante 0x00db731c)  octets : `00 00 f3 0f 59 05 1c 73 db 00`
- 0x0046eba2 [.text] movss xmm2  (constante 0x00db731c)  octets : `00 00 f3 0f 10 15 1c 73 db 00`
- 0x0047fc4f [.text] movss xmm1  (constante 0x00db731c)  octets : `eb 08 f3 0f 10 0d 1c 73 db 00`
- 0x004c6e2d [.text] mulss xmm0  (constante 0x00db731c)  octets : `db 00 f3 0f 59 05 1c 73 db 00`
- 0x00583dd2 [.text] movss xmm2  (constante 0x00db731c)  octets : `8b d1 f3 0f 10 15 1c 73 db 00`
- 0x005e6380 [.text] addss xmm1  (constante 0x00db731c)  octets : `5a c0 f3 0f 58 0d 1c 73 db 00`
- 0x005f72eb [.text] divss xmm1  (constante 0x00db731c)  octets : `57 c0 f3 0f 5e 0d 1c 73 db 00`
- 0x00629ed9 [.text] movss xmm0  (constante 0x00db731c)  octets : `74 12 f3 0f 10 05 1c 73 db 00`
- 0x006ff288 [.text] movss xmm1  (constante 0x00db731c)  octets : `74 12 f3 0f 10 0d 1c 73 db 00`
- 0x0071ae9b [.text] movss xmm1  (constante 0x00db731c)  octets : `00 00 f3 0f 10 0d 1c 73 db 00`
- 0x0071de39 [.text] minss xmm0  (constante 0x00db731c)  octets : `ff ff f3 0f 5d 05 1c 73 db 00`
- 0x00724abb [.text] mulss xmm1  (constante 0x00db731c)  octets : `5a c9 f3 0f 59 0d 1c 73 db 00`
- 0x00724aeb [.text] mulss xmm1  (constante 0x00db731c)  octets : `84 52 f3 0f 59 0d 1c 73 db 00`
- 0x00749dc8 [.text] fmul dword   (constante 0x00db731c)  octets : `ff 83 c4 08 d8 0d 1c 73 db 00`
- 0x0074a414 [.text] mulss xmm1  (constante 0x00db731c)  octets : `ff ff f3 0f 59 0d 1c 73 db 00`
- 0x0076323c [.text] fmul dword   (constante 0x00db731c)  octets : `06 7c ca ff d8 0d 1c 73 db 00`
- 0x007633cb [.text] movss xmm2  (constante 0x00db731c)  octets : `8b f0 f3 0f 10 15 1c 73 db 00`
- 0x00763577 [.text] movss xmm2  (constante 0x00db731c)  octets : `ff ff f3 0f 10 15 1c 73 db 00`
- 0x00765909 [.text] fmul dword   (constante 0x00db731c)  octets : `39 55 ca ff d8 0d 1c 73 db 00`
- 0x007fe8b3 [.text] movss xmm1  (constante 0x00db731c)  octets : `c1 ff f3 0f 10 0d 1c 73 db 00`
- 0x007fe8d9 [.text] movss xmm1  (constante 0x00db731c)  octets : `c1 ff f3 0f 10 0d 1c 73 db 00`
- 0x0082eb57 [.text] mulss xmm0  (constante 0x00db731c)  octets : `ff ff f3 0f 59 05 1c 73 db 00`
- 0x0082f735 [.text] mulss xmm0  (constante 0x00db731c)  octets : `d2 00 f3 0f 59 05 1c 73 db 00`
- 0x0086b7ee [.text] movss xmm0  (constante 0x00db731c)  octets : `d3 00 f3 0f 10 05 1c 73 db 00`
- 0x0086bb62 [.text] movss xmm0  (constante 0x00db731c)  octets : `d3 00 f3 0f 10 05 1c 73 db 00`
- 0x0086ca89 [.text] movss xmm6  (constante 0x00db731c)  octets : `00 00 f3 0f 10 35 1c 73 db 00`
- 0x00b0a1e3 [.text] movss xmm0  (constante 0x00db731c)  octets : `58 da f3 0f 10 05 1c 73 db 00`
- 0x00b735cd [.text] mulss xmm1  (constante 0x00db731c)  octets : `76 1d f3 0f 59 0d 1c 73 db 00`

### 0.2 (copies en donnees : 0x00cee4a0, 0x00db7244, 0x00db83ec, 0x00db83fc, 0x00e1ea04)
- 0x004446af [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x00444994 [.text] addss xmm1  (constante 0x00db7244)  octets : `c4 04 f3 0f 58 0d 44 72 db 00`
- 0x0045cd64 [.text] mulss xmm2  (constante 0x00db7244)  octets : `db 00 f3 0f 59 15 44 72 db 00`
- 0x0045f606 [.text] mulss xmm1  (constante 0x00db7244)  octets : `28 c1 f3 0f 59 0d 44 72 db 00`
- 0x00462ed0 [.text] mulss xmm2  (constante 0x00db7244)  octets : `55 f4 f3 0f 59 15 44 72 db 00`
- 0x00462ee3 [.text] mulss xmm0  (constante 0x00db7244)  octets : `db 00 f3 0f 59 05 44 72 db 00`
- 0x0046512b [.text] movss xmm1  (constante 0x00db7244)  octets : `8b d8 f3 0f 10 0d 44 72 db 00`
- 0x0046521b [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x004655c1 [.text] mulss xmm1  (constante 0x00db7244)  octets : `28 d3 f3 0f 59 0d 44 72 db 00`
- 0x004655d5 [.text] mulss xmm2  (constante 0x00db7244)  octets : `00 10 f3 0f 59 15 44 72 db 00`
- 0x004818b1 [.text] mulss xmm0  (constante 0x00db7244)  octets : `28 c4 f3 0f 59 05 44 72 db 00`
- 0x0048578c [.text] mulss xmm2  (constante 0x00db7244)  octets : `24 60 f3 0f 59 15 44 72 db 00`
- 0x004e8d63 [.text] mulss xmm0  (constante 0x00db7244)  octets : `40 04 f3 0f 59 05 44 72 db 00`
- 0x004f6e42 [.text] ?   (constante 0x00e1ea04)  octets : `00 00 8d 55 b4 68 04 ea e1 00`
- 0x0054071b [.text] maxss xmm0  (constante 0x00db7244)  octets : `00 00 f3 0f 5f 05 44 72 db 00`
- 0x00540737 [.text] maxss xmm0  (constante 0x00db7244)  octets : `00 00 f3 0f 5f 05 44 72 db 00`
- 0x0054a172 [.text] comiss xmm0  (constante 0x00db7244)  octets : `0b ec ff 0f 2f 05 44 72 db 00`
- 0x00585282 [.text] minss xmm7  (constante 0x00db7244)  octets : `76 0c f3 0f 5d 3d 44 72 db 00`
- 0x00585297 [.text] minss xmm6  (constante 0x00db7244)  octets : `7e 10 f3 0f 5d 35 44 72 db 00`
- 0x005876a7 [.text] movss xmm3  (constante 0x00db7244)  octets : `33 c0 f3 0f 10 1d 44 72 db 00`
- 0x0058cd0b [.text] subss xmm0  (constante 0x00db7244)  octets : `db 00 f3 0f 5c 05 44 72 db 00`
- 0x0058cdd8 [.text] mulss xmm0  (constante 0x00db7244)  octets : `db 00 f3 0f 59 05 44 72 db 00`
- 0x0058ce69 [.text] mulss xmm0  (constante 0x00db7244)  octets : `59 cb f3 0f 59 05 44 72 db 00`
- 0x0058d60a [.text] subss xmm0  (constante 0x00db7244)  octets : `db 00 f3 0f 5c 05 44 72 db 00`
- 0x0058d6c5 [.text] subss xmm0  (constante 0x00db7244)  octets : `db 00 f3 0f 5c 05 44 72 db 00`
- 0x0058d742 [.text] subss xmm0  (constante 0x00db7244)  octets : `24 0c f3 0f 5c 05 44 72 db 00`
- 0x00590a76 [.text] mulss xmm0  (constante 0x00db7244)  octets : `5a c0 f3 0f 59 05 44 72 db 00`
- 0x0059bfe4 [.text] movss xmm0  (constante 0x00e1ea04)  octets : `00 c3 f3 0f 10 05 04 ea e1 00`
- 0x005b9484 [.text] movss xmm1  (constante 0x00db7244)  octets : `db 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9568 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b95bb [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b96b2 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b9705 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b97fc [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b984f [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9946 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b9999 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9a90 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b9ae3 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9bda [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b9c2d [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9d27 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b9d7a [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9e74 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005b9ec7 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005b9fc1 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba014 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005ba10e [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba161 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005ba25b [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba2ae [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005ba3a8 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba3fb [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005ba4f5 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba548 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005ba642 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba695 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- 0x005ba78f [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba8c2 [.text] movss xmm1  (constante 0x00db7244)  octets : `4d 3c f3 0f 10 0d 44 72 db 00`
- 0x005ba915 [.text] movss xmm1  (constante 0x00db7244)  octets : `00 00 f3 0f 10 0d 44 72 db 00`
- ... 157 de plus

### 0.025 (copies en donnees : 0x00db71b0)
- 0x005f865e [.text] addss xmm0  (constante 0x00db71b0)  octets : `5a c0 f3 0f 58 05 b0 71 db 00`
- 0x005f8677 [.text] addss xmm0  (constante 0x00db71b0)  octets : `5a c0 f3 0f 58 05 b0 71 db 00`
- 0x006ecadc [.text] movss xmm4  (constante 0x00db71b0)  octets : `2f c3 f3 0f 10 25 b0 71 db 00`
- 0x007038d4 [.text] movss xmm1  (constante 0x00db71b0)  octets : `d0 ff f3 0f 10 0d b0 71 db 00`
- 0x00705c14 [.text] movss xmm3  (constante 0x00db71b0)  octets : `8b d1 f3 0f 10 1d b0 71 db 00`
- 0x0070a36f [.text] movss xmm0  (constante 0x00db71b0)  octets : `77 1e f3 0f 10 05 b0 71 db 00`
- 0x007120de [.text] movss xmm1  (constante 0x00db71b0)  octets : `cf ff f3 0f 10 0d b0 71 db 00`
- 0x00714718 [.text] movss xmm3  (constante 0x00db71b0)  octets : `00 00 f3 0f 10 1d b0 71 db 00`
- 0x00715727 [.text] subss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 5c 0d b0 71 db 00`
- 0x00716595 [.text] subss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 5c 0d b0 71 db 00`
- 0x0071781d [.text] subss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 5c 0d b0 71 db 00`
- 0x00718a37 [.text] subss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 5c 0d b0 71 db 00`
- 0x0072c075 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `5c c8 f3 0f 59 0d b0 71 db 00`
- 0x0072c646 [.text] movss xmm0  (constante 0x00db71b0)  octets : `00 00 f3 0f 10 05 b0 71 db 00`
- 0x0072ce57 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `5c c8 f3 0f 59 0d b0 71 db 00`
- 0x0072d577 [.text] movss xmm0  (constante 0x00db71b0)  octets : `00 00 f3 0f 10 05 b0 71 db 00`
- 0x007ebc3f [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x007ebc5f [.text] subss xmm1  (constante 0x00db71b0)  octets : `00 00 f3 0f 5c 0d b0 71 db 00`
- 0x0086c16e [.text] movss xmm1  (constante 0x00db71b0)  octets : `14 c1 f3 0f 10 0d b0 71 db 00`
- 0x008e0ae9 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `4d 08 f3 0f 59 0d b0 71 db 00`
- 0x008e0c90 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `4d 08 f3 0f 59 0d b0 71 db 00`
- 0x008e0f34 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `4d 08 f3 0f 59 0d b0 71 db 00`
- 0x009e9246 [.text] mulss xmm0  (constante 0x00db71b0)  octets : `10 02 f3 0f 59 05 b0 71 db 00`
- 0x00a3911a [.text] addss xmm5  (constante 0x00db71b0)  octets : `59 c2 f3 0f 58 2d b0 71 db 00`
- 0x00a40db8 [.text] addss xmm1  (constante 0x00db71b0)  octets : `24 30 f3 0f 58 0d b0 71 db 00`
- 0x00a669df [.text] addss xmm0  (constante 0x00db71b0)  octets : `24 4c f3 0f 58 05 b0 71 db 00`
- 0x00ad2284 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00ad2692 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00ad629d [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00ad6bc7 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00ad72af [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00aea60f [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b05086 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b09335 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `28 c1 f3 0f 59 0d b0 71 db 00`
- 0x00b0d7ad [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b133bf [.text] mulss xmm1  (constante 0x00db71b0)  octets : `00 00 f3 0f 59 0d b0 71 db 00`
- 0x00b18411 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b1cb6e [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b1cfec [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b3ba28 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b3c067 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `28 c1 f3 0f 59 0d b0 71 db 00`
- 0x00b3c4e4 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b3c981 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b3cfd7 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b66e78 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b7708b [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b780da [.text] mulss xmm1  (constante 0x00db71b0)  octets : `28 c1 f3 0f 59 0d b0 71 db 00`
- 0x00b78cc6 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b7a124 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b7a5ad [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b7e1d7 [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00b872ba [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00bcd13a [.text] mulss xmm1  (constante 0x00db71b0)  octets : `48 00 f3 0f 59 0d b0 71 db 00`
- 0x00bce4bd [.text] mulss xmm1  (constante 0x00db71b0)  octets : `db 00 f3 0f 59 0d b0 71 db 00`
- 0x00c26bb0 [.text] mulss xmm0  (constante 0x00db71b0)  octets : `10 06 f3 0f 59 05 b0 71 db 00`

### -0.025 (copies en donnees : 0x00db7be0)
- 0x00705c3e [.text] maxss xmm1  (constante 0x00db7be0)  octets : `00 00 f3 0f 5f 0d e0 7b db 00`
- 0x0086a0e1 [.text] movss xmm2  (constante 0x00db7be0)  octets : `24 10 f3 0f 10 15 e0 7b db 00`

### 0.001 (copies en donnees : 0x00cd9dc0, 0x00cd9dc4, 0x00cd9dc8, 0x00d36914, 0x00db715c, 0x00db7ed0)
- 0x00401b94 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401bb3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401bc4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00401c34 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401c53 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401c64 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00401cd4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401cf3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401d04 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00401d74 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401d93 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401da4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00401e14 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401e33 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401e44 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00401eb4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401ed3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401ee4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00401f54 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00401f73 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00401f84 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402004 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402023 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402034 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x004020a4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x004020c3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x004020d4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402144 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402163 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402174 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x004021e4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402203 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402214 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402284 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x004022a3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x004022b4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402324 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402343 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402354 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x004023c4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x004023e3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x004023f4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402464 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402483 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402494 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402504 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402523 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402534 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x004025a4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x004025c3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x004025d4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402644 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402663 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402674 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x004026e4 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x00402703 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x00402714 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- 0x00402784 [.text] movss xmm0  (constante 0x00db715c)  octets : `cc cc f3 0f 10 05 5c 71 db 00`
- 0x004027a3 [.text] movaps xmm0  (constante 0x00cd9dc0)  octets : `cc cc cc 0f 28 05 c0 9d cd 00`
- 0x004027b4 [.text] movss xmm0  (constante 0x00db715c)  octets : `c3 cc f3 0f 10 05 5c 71 db 00`
- ... 712 de plus

### 1/6 (copies en donnees : 0x00ceed48, 0x00db7224)
- 0x00456cfd [.text] divss xmm1  (constante 0x00db7224)  octets : `24 08 f3 0f 5e 0d 24 72 db 00`
- 0x00700f26 [.text] movss xmm2  (constante 0x00db7224)  octets : `d0 ff f3 0f 10 15 24 72 db 00`
- 0x00701035 [.text] movss xmm2  (constante 0x00db7224)  octets : `d0 ff f3 0f 10 15 24 72 db 00`
- 0x00bfe2d0 [.text] movss xmm0  (constante 0x00db7224)  octets : `00 00 f3 0f 10 05 24 72 db 00`
- 0x00c5e075 [.text] movss xmm7  (constante 0x00ceed48)  octets : `5c c2 f3 0f 10 3d 48 ed ce 00`
- 0x00c5e172 [.text] movss xmm5  (constante 0x00ceed48)  octets : `58 de f3 0f 10 2d 48 ed ce 00`
- 0x00c5e1e9 [.text] mulss xmm1  (constante 0x00ceed48)  octets : `10 d1 f3 0f 59 0d 48 ed ce 00`
- 0x00c5e2aa [.text] mulss xmm2  (constante 0x00ceed48)  octets : `5c e3 f3 0f 59 15 48 ed ce 00`

### -1/6 (copies en donnees : 0x00db7c14, 0x00e5b1c0, 0x00e5b1c4, 0x00e5b1c8, 0x00e5b1cc, 0x00e5b1d0)
- 0x00700f31 [.text] movss xmm1  (constante 0x00db7c14)  octets : `c4 04 f3 0f 10 0d 14 7c db 00`
- 0x00701040 [.text] movss xmm1  (constante 0x00db7c14)  octets : `c4 04 f3 0f 10 0d 14 7c db 00`
- 0x00c41333 [.text] addps xmm0  (constante 0x00e5b1c0)  octets : `0f 59 fa 0f 58 05 c0 b1 e5 00`

### 1/30 (copies en donnees : 0x00db71bc)
- 0x0058970d [.text] mulss xmm1  (constante 0x00db71bc)  octets : `00 00 f3 0f 59 0d bc 71 db 00`
- 0x005e48ed [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x005e4901 [.text] subss xmm1  (constante 0x00db71bc)  octets : `5f ce f3 0f 5c 0d bc 71 db 00`
- 0x00659fb1 [.text] addss xmm0  (constante 0x00db71bc)  octets : `00 00 f3 0f 58 05 bc 71 db 00`
- 0x0065a596 [.text] addss xmm0  (constante 0x00db71bc)  octets : `00 00 f3 0f 58 05 bc 71 db 00`
- 0x0066349b [.text] movss xmm1  (constante 0x00db71bc)  octets : `5e d1 f3 0f 10 0d bc 71 db 00`
- 0x006634b5 [.text] subss xmm1  (constante 0x00db71bc)  octets : `db 00 f3 0f 5c 0d bc 71 db 00`
- 0x00668da6 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x00668dd4 [.text] subss xmm1  (constante 0x00db71bc)  octets : `24 0c f3 0f 5c 0d bc 71 db 00`
- 0x0066f208 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x0066f236 [.text] subss xmm1  (constante 0x00db71bc)  octets : `24 10 f3 0f 5c 0d bc 71 db 00`
- 0x006724a7 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x006724d5 [.text] subss xmm1  (constante 0x00db71bc)  octets : `24 0c f3 0f 5c 0d bc 71 db 00`
- 0x0067ec32 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5e d1 f3 0f 10 0d bc 71 db 00`
- 0x0067ec3e [.text] subss xmm1  (constante 0x00db71bc)  octets : `5f ca f3 0f 5c 0d bc 71 db 00`
- 0x006876d7 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x006876f9 [.text] subss xmm1  (constante 0x00db71bc)  octets : `5f ce f3 0f 5c 0d bc 71 db 00`
- 0x00687b94 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x00687bc2 [.text] subss xmm1  (constante 0x00db71bc)  octets : `24 1c f3 0f 5c 0d bc 71 db 00`
- 0x0068f292 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x0068f2b4 [.text] subss xmm1  (constante 0x00db71bc)  octets : `5f ce f3 0f 5c 0d bc 71 db 00`
- 0x0068f762 [.text] movss xmm1  (constante 0x00db71bc)  octets : `5a c1 f3 0f 10 0d bc 71 db 00`
- 0x0068f790 [.text] subss xmm1  (constante 0x00db71bc)  octets : `24 24 f3 0f 5c 0d bc 71 db 00`
- 0x00700f9a [.text] movss xmm2  (constante 0x00db71bc)  octets : `5e e2 f3 0f 10 15 bc 71 db 00`
- 0x007010a6 [.text] movss xmm2  (constante 0x00db71bc)  octets : `5e e2 f3 0f 10 15 bc 71 db 00`
- 0x00701124 [.text] movss xmm2  (constante 0x00db71bc)  octets : `00 00 f3 0f 10 15 bc 71 db 00`
- 0x007011b6 [.text] movss xmm2  (constante 0x00db71bc)  octets : `00 00 f3 0f 10 15 bc 71 db 00`
- 0x007402e2 [.text] movss xmm1  (constante 0x00db71bc)  octets : `d0 ff f3 0f 10 0d bc 71 db 00`
- 0x00758a0d [.text] movss xmm1  (constante 0x00db71bc)  octets : `cf ff f3 0f 10 0d bc 71 db 00`
- 0x007816af [.text] movss xmm1  (constante 0x00db71bc)  octets : `cc ff f3 0f 10 0d bc 71 db 00`
- 0x0078bb4b [.text] movss xmm1  (constante 0x00db71bc)  octets : `5e d1 f3 0f 10 0d bc 71 db 00`
- 0x0078bb57 [.text] subss xmm1  (constante 0x00db71bc)  octets : `5f ca f3 0f 5c 0d bc 71 db 00`

### -1/30 (copies en donnees : 0x00db7be4)
- 0x00700f82 [.text] movss xmm1  (constante 0x00db7be4)  octets : `28 e1 f3 0f 10 0d e4 7b db 00`
- 0x00701083 [.text] movss xmm1  (constante 0x00db7be4)  octets : `d0 ff f3 0f 10 0d e4 7b db 00`
- 0x0070112c [.text] movss xmm1  (constante 0x00db7be4)  octets : `db 00 f3 0f 10 0d e4 7b db 00`
- 0x007011be [.text] movss xmm1  (constante 0x00db7be4)  octets : `db 00 f3 0f 10 0d e4 7b db 00`

### 0.04 (copies en donnees : 0x00db71c4, 0x00db8710, 0x00db8714, 0x00db8718)
- 0x0045d1b8 [.text] comiss xmm0  (constante 0x00db71c4)  octets : `19 00 00 0f 2f 05 c4 71 db 00`
- 0x0046e9dd [.text] movaps xmm0  (constante 0x00db8710)  octets : `01 00 00 0f 28 05 10 87 db 00`
- 0x004e8d77 [.text] mulss xmm0  (constante 0x00db71c4)  octets : `10 00 f3 0f 59 05 c4 71 db 00`
- 0x004e8d8b [.text] mulss xmm0  (constante 0x00db71c4)  octets : `10 00 f3 0f 59 05 c4 71 db 00`
- 0x00669040 [.text] minss xmm2  (constante 0x00db71c4)  octets : `24 0c f3 0f 5d 15 c4 71 db 00`
- 0x00669125 [.text] minss xmm1  (constante 0x00db71c4)  octets : `db 00 f3 0f 5d 0d c4 71 db 00`
- 0x006693e7 [.text] movss xmm1  (constante 0x00db71c4)  octets : `5c c1 f3 0f 10 0d c4 71 db 00`
- 0x0066a135 [.text] movss xmm4  (constante 0x00db71c4)  octets : `76 10 f3 0f 10 25 c4 71 db 00`
- 0x0066a1d2 [.text] movss xmm4  (constante 0x00db71c4)  octets : `76 10 f3 0f 10 25 c4 71 db 00`
- 0x006b0b3b [.text] fld dword   (constante 0x00db71c4)  octets : `00 00 76 07 d9 05 c4 71 db 00`
- 0x00701219 [.text] movss xmm2  (constante 0x00db71c4)  octets : `00 00 f3 0f 10 15 c4 71 db 00`
- 0x00724c82 [.text] mulss xmm1  (constante 0x00db71c4)  octets : `5c cf f3 0f 59 0d c4 71 db 00`
- 0x007634fc [.text] mulss xmm0  (constante 0x00db71c4)  octets : `de ff f3 0f 59 05 c4 71 db 00`
- 0x0086ae39 [.text] movss xmm1  (constante 0x00db71c4)  octets : `24 10 f3 0f 10 0d c4 71 db 00`

### -0.04 (copies en donnees : 0x00db7bec)
- 0x00669032 [.text] maxss xmm2  (constante 0x00db7bec)  octets : `57 d3 f3 0f 5f 15 ec 7b db 00`
- 0x0066911d [.text] maxss xmm1  (constante 0x00db7bec)  octets : `5c c8 f3 0f 5f 0d ec 7b db 00`
- 0x00701225 [.text] movss xmm1  (constante 0x00db7bec)  octets : `5c c3 f3 0f 10 0d ec 7b db 00`

### 0.05 (copies en donnees : 0x00db71d0, 0x00db8720, 0x00db8724, 0x00db8728)
- 0x00465133 [.text] movss xmm2  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 15 d0 71 db 00`
- 0x00465223 [.text] movss xmm2  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 15 d0 71 db 00`
- 0x005853da [.text] movss xmm2  (constante 0x00db71d0)  octets : `46 66 f3 0f 10 15 d0 71 db 00`
- 0x00585445 [.text] minss xmm1  (constante 0x00db71d0)  octets : `db 00 f3 0f 5d 0d d0 71 db 00`
- 0x00585534 [.text] movss xmm2  (constante 0x00db71d0)  octets : `c2 66 f3 0f 10 15 d0 71 db 00`
- 0x00585620 [.text] minss xmm1  (constante 0x00db71d0)  octets : `45 20 f3 0f 5d 0d d0 71 db 00`
- 0x005b843b [.text] movss xmm1  (constante 0x00db71d0)  octets : `5e c1 f3 0f 10 0d d0 71 db 00`
- 0x005f4d90 [.text] addss xmm3  (constante 0x00db71d0)  octets : `76 1b f3 0f 58 1d d0 71 db 00`
- 0x005f4dab [.text] subss xmm3  (constante 0x00db71d0)  octets : `eb 11 f3 0f 5c 1d d0 71 db 00`
- 0x005f6243 [.text] addss xmm3  (constante 0x00db71d0)  octets : `76 1b f3 0f 58 1d d0 71 db 00`
- 0x005f625e [.text] subss xmm3  (constante 0x00db71d0)  octets : `eb 11 f3 0f 5c 1d d0 71 db 00`
- 0x005fb087 [.text] movss xmm5  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 2d d0 71 db 00`
- 0x00642bff [.text] minss xmm0  (constante 0x00db71d0)  octets : `00 00 f3 0f 5d 05 d0 71 db 00`
- 0x0065d1e3 [.text] minss xmm0  (constante 0x00db71d0)  octets : `db 00 f3 0f 5d 05 d0 71 db 00`
- 0x00664cea [.text] minss xmm2  (constante 0x00db71d0)  octets : `db 00 f3 0f 5d 15 d0 71 db 00`
- 0x006c5c71 [.text] fmul dword   (constante 0x00db71d0)  octets : `d1 51 d4 ff d8 0d d0 71 db 00`
- 0x006c618e [.text] movss xmm0  (constante 0x00db71d0)  octets : `4d ac f3 0f 10 05 d0 71 db 00`
- 0x006e2b39 [.text] mulss xmm1  (constante 0x00db71d0)  octets : `60 40 f3 0f 59 0d d0 71 db 00`
- 0x006f9845 [.text] addss xmm0  (constante 0x00db71d0)  octets : `5c cc f3 0f 58 05 d0 71 db 00`
- 0x006fb2ce [.text] addss xmm0  (constante 0x00db71d0)  octets : `47 60 f3 0f 58 05 d0 71 db 00`
- 0x006fcbaa [.text] addss xmm0  (constante 0x00db71d0)  octets : `00 00 f3 0f 58 05 d0 71 db 00`
- 0x006fce4e [.text] addss xmm0  (constante 0x00db71d0)  octets : `00 00 f3 0f 58 05 d0 71 db 00`
- 0x006fd8d5 [.text] addss xmm0  (constante 0x00db71d0)  octets : `8b d0 f3 0f 58 05 d0 71 db 00`
- 0x006fddb5 [.text] movss xmm2  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 15 d0 71 db 00`
- 0x006ffaef [.text] addss xmm0  (constante 0x00db71d0)  octets : `5c cb f3 0f 58 05 d0 71 db 00`
- 0x0070223d [.text] addss xmm0  (constante 0x00db71d0)  octets : `00 00 f3 0f 58 05 d0 71 db 00`
- 0x0070719d [.text] movss xmm5  (constante 0x00db71d0)  octets : `00 00 f3 0f 10 2d d0 71 db 00`
- 0x007109f8 [.text] comiss xmm0  (constante 0x00db71d0)  octets : `01 00 00 0f 2f 05 d0 71 db 00`
- 0x0071571f [.text] mulss xmm1  (constante 0x00db71d0)  octets : `db 00 f3 0f 59 0d d0 71 db 00`
- 0x0071658d [.text] mulss xmm1  (constante 0x00db71d0)  octets : `db 00 f3 0f 59 0d d0 71 db 00`
- 0x00717815 [.text] mulss xmm1  (constante 0x00db71d0)  octets : `db 00 f3 0f 59 0d d0 71 db 00`
- 0x00718a2f [.text] mulss xmm1  (constante 0x00db71d0)  octets : `db 00 f3 0f 59 0d d0 71 db 00`
- 0x0071aeb8 [.text] comiss xmm0  (constante 0x00db71d0)  octets : `fe ce ff 0f 2f 05 d0 71 db 00`
- 0x0071b26b [.text] movss xmm1  (constante 0x00db71d0)  octets : `ce ff f3 0f 10 0d d0 71 db 00`
- 0x0071ddc8 [.text] mulss xmm0  (constante 0x00db71d0)  octets : `ff ff f3 0f 59 05 d0 71 db 00`
- 0x00724640 [.text] movss xmm1  (constante 0x00db71d0)  octets : `00 00 f3 0f 10 0d d0 71 db 00`
- 0x00746ede [.text] comiss xmm2  (constante 0x00db71d0)  octets : `0f 5a d0 0f 2f 15 d0 71 db 00`
- 0x00747bad [.text] movss xmm0  (constante 0x00db71d0)  octets : `75 10 f3 0f 10 05 d0 71 db 00`
- 0x007498c2 [.text] comiss xmm2  (constante 0x00db71d0)  octets : `0f 5a d0 0f 2f 15 d0 71 db 00`
- 0x0074cba8 [.text] comiss xmm2  (constante 0x00db71d0)  octets : `0f 5a d0 0f 2f 15 d0 71 db 00`
- 0x0076159a [.text] movss xmm0  (constante 0x00db71d0)  octets : `ca ff f3 0f 10 05 d0 71 db 00`
- 0x0076b314 [.text] movss xmm3  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 1d d0 71 db 00`
- 0x00785d01 [.text] movss xmm3  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 1d d0 71 db 00`
- 0x0079ab8e [.text] movss xmm1  (constante 0x00db71d0)  octets : `ff ff f3 0f 10 0d d0 71 db 00`
- 0x007b1fe4 [.text] movaps xmm0  (constante 0x00db8720)  octets : `18 c8 ff 0f 28 05 20 87 db 00`
- 0x007de105 [.text] movss xmm4  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 25 d0 71 db 00`
- 0x007e7639 [.text] movaps xmm0  (constante 0x00db8720)  octets : `c2 c4 ff 0f 28 05 20 87 db 00`
- 0x007fd042 [.text] movaps xmm0  (constante 0x00db8720)  octets : `68 c3 ff 0f 28 05 20 87 db 00`
- 0x0080bba7 [.text] movaps xmm0  (constante 0x00db8720)  octets : `7c c2 ff 0f 28 05 20 87 db 00`
- 0x0080f807 [.text] movaps xmm0  (constante 0x00db8720)  octets : `40 c2 ff 0f 28 05 20 87 db 00`
- 0x00811f72 [.text] movaps xmm0  (constante 0x00db8720)  octets : `19 c2 ff 0f 28 05 20 87 db 00`
- 0x00815769 [.text] mulss xmm2  (constante 0x00db71d0)  octets : `28 d0 f3 0f 59 15 d0 71 db 00`
- 0x0086a35a [.text] movss xmm1  (constante 0x00db71d0)  octets : `00 00 f3 0f 10 0d d0 71 db 00`
- 0x0086bfb1 [.text] movss xmm2  (constante 0x00db71d0)  octets : `14 c2 f3 0f 10 15 d0 71 db 00`
- 0x008e0819 [.text] mulss xmm3  (constante 0x00db71d0)  octets : `00 00 f3 0f 59 1d d0 71 db 00`
- 0x008e098f [.text] mulss xmm3  (constante 0x00db71d0)  octets : `db 00 f3 0f 59 1d d0 71 db 00`
- 0x008f0c52 [.text] mulss xmm1  (constante 0x00db71d0)  octets : `4d 0c f3 0f 59 0d d0 71 db 00`
- 0x008f0c80 [.text] mulss xmm1  (constante 0x00db71d0)  octets : `4d 10 f3 0f 59 0d d0 71 db 00`
- 0x008f0ca9 [.text] mulss xmm1  (constante 0x00db71d0)  octets : `4d 20 f3 0f 59 0d d0 71 db 00`
- 0x009e0457 [.text] movss xmm5  (constante 0x00db71d0)  octets : `db 00 f3 0f 10 2d d0 71 db 00`
- ... 85 de plus

### 2.5 (copies en donnees : 0x00db76c8, 0x00db76d4, 0x00db93dc, 0x00db93e4, 0x00dbca24, 0x00dbd984)
- 0x00459a69 [.text] movss xmm0  (constante 0x00db76c8)  octets : `77 0c f3 0f 10 05 c8 76 db 00`
- 0x004f73e2 [.text] ?   (constante 0x00e1ea34)  octets : `00 00 8d 55 b4 68 34 ea e1 00`
- 0x004f745a [.text] ?   (constante 0x00e1ea38)  octets : `00 00 8d 55 b4 68 38 ea e1 00`
- 0x004f74d2 [.text] ?   (constante 0x00e1ea3c)  octets : `00 00 8d 55 b4 68 3c ea e1 00`
- 0x004f754a [.text] ?   (constante 0x00e1ea40)  octets : `00 00 8d 55 b4 68 40 ea e1 00`
- 0x0059bd3e [.text] movss xmm0  (constante 0x00e1ea34)  octets : `59 00 f3 0f 10 05 34 ea e1 00`
- 0x0059bd47 [.text] movss xmm0  (constante 0x00e1ea38)  octets : `00 c3 f3 0f 10 05 38 ea e1 00`
- 0x0059bd50 [.text] movss xmm0  (constante 0x00e1ea3c)  octets : `00 c3 f3 0f 10 05 3c ea e1 00`
- 0x0059bd59 [.text] movss xmm0  (constante 0x00e1ea40)  octets : `00 c3 f3 0f 10 05 40 ea e1 00`
- 0x006f9811 [.text] movss xmm2  (constante 0x00db76c8)  octets : `72 e3 f3 0f 10 15 c8 76 db 00`
- 0x006fb2e9 [.text] movss xmm1  (constante 0x00db76c8)  octets : `28 d3 f3 0f 10 0d c8 76 db 00`
- 0x006fb3dc [.text] movss xmm2  (constante 0x00db76c8)  octets : `67 5c f3 0f 10 15 c8 76 db 00`
- 0x006fcbb2 [.text] movss xmm1  (constante 0x00db76c8)  octets : `db 00 f3 0f 10 0d c8 76 db 00`
- 0x006fce56 [.text] movss xmm3  (constante 0x00db76c8)  octets : `db 00 f3 0f 10 1d c8 76 db 00`
- 0x006fd8f0 [.text] movss xmm3  (constante 0x00db76c8)  octets : `28 ca f3 0f 10 1d c8 76 db 00`
- 0x006fddbd [.text] movss xmm5  (constante 0x00db76c8)  octets : `db 00 f3 0f 10 2d c8 76 db 00`
- 0x006ffa68 [.text] movss xmm5  (constante 0x00db76c8)  octets : `db 00 f3 0f 10 2d c8 76 db 00`

### 11.0 (copies en donnees : 0x00d724cc, 0x00db7908, 0x00e1f078, 0x00e1f07c, 0x00e1f094, 0x00e1f0a8)
- 0x0070117c [.text] movss xmm0  (constante 0x00db7908)  octets : `00 00 f3 0f 10 05 08 79 db 00`
- 0x007011cc [.text] movss xmm0  (constante 0x00db7908)  octets : `ff ff f3 0f 10 05 08 79 db 00`

### 12.0 (copies en donnees : 0x00db790c, 0x00db8ce0, 0x00db8ce4, 0x00db8ce8, 0x00db8cec, 0x00e1f040)
- 0x0042f6b1 [.text] movss xmm1  (constante 0x00db790c)  octets : `4d ac f3 0f 10 0d 0c 79 db 00`
- 0x0042f9f3 [.text] divss xmm7  (constante 0x00db790c)  octets : `45 c8 f3 0f 5e 3d 0c 79 db 00`
- 0x0042fe8d [.text] movss xmm1  (constante 0x00db790c)  octets : `e0 40 f3 0f 10 0d 0c 79 db 00`
- 0x0046ee87 [.text] divss xmm0  (constante 0x00db790c)  octets : `db 00 f3 0f 5e 05 0c 79 db 00`
- 0x00474bb4 [.text] ?   (constante 0x00e1f040)  octets : `24 f3 0f 10 3c f5 40 f0 e1 00`
- 0x00480d96 [.text] mulss xmm0  (constante 0x00db790c)  octets : `d2 00 f3 0f 59 05 0c 79 db 00`
- 0x0060063f [.text] mulss xmm0  (constante 0x00db790c)  octets : `5b c0 f3 0f 59 05 0c 79 db 00`
- 0x0060185b [.text] movss xmm2  (constante 0x00db790c)  octets : `58 ea f3 0f 10 15 0c 79 db 00`
- 0x00601cf8 [.text] movss xmm2  (constante 0x00db790c)  octets : `00 40 f3 0f 10 15 0c 79 db 00`
- 0x00601d27 [.text] movaps xmm3  (constante 0x00db8ce0)  octets : `83 e6 f8 0f 28 1d e0 8c db 00`
- 0x00601e32 [.text] movss xmm2  (constante 0x00db790c)  octets : `57 f6 f3 0f 10 15 0c 79 db 00`
- 0x00601ebf [.text] movss xmm2  (constante 0x00db790c)  octets : `eb 0b f3 0f 10 15 0c 79 db 00`
- 0x0061494a [.text] movss xmm1  (constante 0x00db790c)  octets : `ff ff f3 0f 10 0d 0c 79 db 00`
- 0x006151c4 [.text] mulss xmm0  (constante 0x00db790c)  octets : `5b c0 f3 0f 59 05 0c 79 db 00`
- 0x006155c8 [.text] mulss xmm0  (constante 0x00db790c)  octets : `5b c0 f3 0f 59 05 0c 79 db 00`
- 0x0061591a [.text] mulss xmm0  (constante 0x00db790c)  octets : `24 20 f3 0f 59 05 0c 79 db 00`
- 0x00615c99 [.text] mulss xmm0  (constante 0x00db790c)  octets : `5b c0 f3 0f 59 05 0c 79 db 00`
- 0x0061646e [.text] movss xmm0  (constante 0x00db790c)  octets : `00 00 f3 0f 10 05 0c 79 db 00`
- 0x00616e8b [.text] movss xmm1  (constante 0x00db790c)  octets : `58 f9 f3 0f 10 0d 0c 79 db 00`
- 0x00617252 [.text] mulss xmm0  (constante 0x00db790c)  octets : `00 00 f3 0f 59 05 0c 79 db 00`
- 0x0061778b [.text] mulss xmm0  (constante 0x00db790c)  octets : `00 00 f3 0f 59 05 0c 79 db 00`
- 0x006fa17d [.text] movss xmm2  (constante 0x00db790c)  octets : `d1 ff f3 0f 10 15 0c 79 db 00`
- 0x00701136 [.text] movss xmm0  (constante 0x00db790c)  octets : `74 46 f3 0f 10 05 0c 79 db 00`
- 0x007646a6 [.text] mulss xmm2  (constante 0x00db790c)  octets : `5b d2 f3 0f 59 15 0c 79 db 00`
- 0x00764e26 [.text] mulss xmm2  (constante 0x00db790c)  octets : `5b d2 f3 0f 59 15 0c 79 db 00`
- 0x008026f8 [.text] addss xmm0  (constante 0x00db790c)  octets : `10 07 f3 0f 58 05 0c 79 db 00`
- 0x0080ffab [.text] mulss xmm0  (constante 0x00db790c)  octets : `00 00 f3 0f 59 05 0c 79 db 00`
- 0x00811933 [.text] movss xmm5  (constante 0x00db790c)  octets : `ff ff f3 0f 10 2d 0c 79 db 00`
- 0x00811bb3 [.text] mulss xmm1  (constante 0x00db790c)  octets : `ff ff f3 0f 59 0d 0c 79 db 00`
- 0x008f1126 [.text] minss xmm0  (constante 0x00db790c)  octets : `24 10 f3 0f 5d 05 0c 79 db 00`

### 30.0 (copies en donnees : 0x00cea3a4, 0x00db798c, 0x00db8d1c)
- 0x0048758c [.text] movss xmm1  (constante 0x00db798c)  octets : `77 0c f3 0f 10 0d 8c 79 db 00`
- 0x005839b4 [.text] comiss xmm1  (constante 0x00db798c)  octets : `00 75 29 0f 2f 0d 8c 79 db 00`
- 0x0058655b [.text] movss xmm1  (constante 0x00db798c)  octets : `0c 48 f3 0f 10 0d 8c 79 db 00`
- 0x0058667f [.text] mulss xmm1  (constante 0x00db798c)  octets : `90 08 f3 0f 59 0d 8c 79 db 00`
- 0x0058d41a [.text] movss xmm5  (constante 0x00db798c)  octets : `db 00 f3 0f 10 2d 8c 79 db 00`
- 0x0058df1e [.text] movss xmm0  (constante 0x00db798c)  octets : `4d 20 f3 0f 10 05 8c 79 db 00`
- 0x0058e047 [.text] movss xmm0  (constante 0x00db798c)  octets : `4d 20 f3 0f 10 05 8c 79 db 00`
- 0x0058e63d [.text] divss xmm5  (constante 0x00db798c)  octets : `db 00 f3 0f 5e 2d 8c 79 db 00`
- 0x0058e645 [.text] divss xmm6  (constante 0x00db798c)  octets : `db 00 f3 0f 5e 35 8c 79 db 00`
- 0x0058edb0 [.text] divss xmm2  (constante 0x00db798c)  octets : `57 1c f3 0f 5e 15 8c 79 db 00`
- 0x0059145a [.text] divss xmm2  (constante 0x00db798c)  octets : `e7 ff f3 0f 5e 15 8c 79 db 00`
- 0x00591b22 [.text] divss xmm0  (constante 0x00db798c)  octets : `ff ff f3 0f 5e 05 8c 79 db 00`
- 0x005c862b [.text] divss xmm0  (constante 0x00db798c)  octets : `ff ff f3 0f 5e 05 8c 79 db 00`
- 0x005c8647 [.text] divss xmm0  (constante 0x00db798c)  octets : `5a c0 f3 0f 5e 05 8c 79 db 00`
- 0x005d1ed9 [.text] divss xmm0  (constante 0x00db798c)  octets : `db 00 f3 0f 5e 05 8c 79 db 00`
- 0x005de9a0 [.text] mulss xmm1  (constante 0x00db798c)  octets : `57 e4 f3 0f 59 0d 8c 79 db 00`
- 0x005dff42 [.text] movss xmm0  (constante 0x00db798c)  octets : `75 1c f3 0f 10 05 8c 79 db 00`
- 0x005e0012 [.text] movss xmm0  (constante 0x00db798c)  octets : `75 1c f3 0f 10 05 8c 79 db 00`
- 0x005f29cf [.text] divss xmm0  (constante 0x00db798c)  octets : `8b ce f3 0f 5e 05 8c 79 db 00`
- 0x005f2a02 [.text] divss xmm0  (constante 0x00db798c)  octets : `58 c0 f3 0f 5e 05 8c 79 db 00`
- 0x005fca17 [.text] divss xmm0  (constante 0x00db798c)  octets : `43 14 f3 0f 5e 05 8c 79 db 00`
- 0x00600ec8 [.text] movss xmm0  (constante 0x00db798c)  octets : `60 00 f3 0f 10 05 8c 79 db 00`
- 0x0061566b [.text] movss xmm1  (constante 0x00db798c)  octets : `df ff f3 0f 10 0d 8c 79 db 00`
- 0x00615809 [.text] movss xmm2  (constante 0x00db798c)  octets : `24 10 f3 0f 10 15 8c 79 db 00`
- 0x00615d3c [.text] movss xmm1  (constante 0x00db798c)  octets : `df ff f3 0f 10 0d 8c 79 db 00`
- 0x00615eda [.text] movss xmm2  (constante 0x00db798c)  octets : `24 10 f3 0f 10 15 8c 79 db 00`
- 0x0061664e [.text] addss xmm0  (constante 0x00db798c)  octets : `db 00 f3 0f 58 05 8c 79 db 00`
- 0x0061bb16 [.text] divss xmm0  (constante 0x00db798c)  octets : `28 c2 f3 0f 5e 05 8c 79 db 00`
- 0x0061c88c [.text] divss xmm0  (constante 0x00db798c)  octets : `5a c0 f3 0f 5e 05 8c 79 db 00`
- 0x0062088d [.text] divss xmm2  (constante 0x00db798c)  octets : `ec 2c f3 0f 5e 15 8c 79 db 00`
- 0x0063869c [.text] divss xmm0  (constante 0x00db798c)  octets : `28 c4 f3 0f 5e 05 8c 79 db 00`
- 0x00639346 [.text] divss xmm1  (constante 0x00db798c)  octets : `00 00 f3 0f 5e 0d 8c 79 db 00`
- 0x00639876 [.text] divss xmm0  (constante 0x00db798c)  octets : `5a c0 f3 0f 5e 05 8c 79 db 00`
- 0x0065aba9 [.text] divss xmm0  (constante 0x00db798c)  octets : `ff ff f3 0f 5e 05 8c 79 db 00`
- 0x0065e1c2 [.text] divss xmm0  (constante 0x00db798c)  octets : `f8 ff f3 0f 5e 05 8c 79 db 00`
- 0x006b255e [.text] mulss xmm0  (constante 0x00db798c)  octets : `00 00 f3 0f 59 05 8c 79 db 00`
- 0x006b2abd [.text] mulss xmm0  (constante 0x00db798c)  octets : `00 00 f3 0f 59 05 8c 79 db 00`
- 0x006b5e95 [.text] divss xmm1  (constante 0x00db798c)  octets : `db 00 f3 0f 5e 0d 8c 79 db 00`
- 0x006cac9a [.text] divss xmm0  (constante 0x00db798c)  octets : `5a c0 f3 0f 5e 05 8c 79 db 00`
- 0x006e32b7 [.text] divss xmm0  (constante 0x00db798c)  octets : `5a c0 f3 0f 5e 05 8c 79 db 00`
- 0x006e84e9 [.text] divss xmm0  (constante 0x00db798c)  octets : `5a c0 f3 0f 5e 05 8c 79 db 00`
- 0x006f7495 [.text] addss xmm0  (constante 0x00db798c)  octets : `00 00 f3 0f 58 05 8c 79 db 00`
- 0x006f9bad [.text] mulss xmm0  (constante 0x00db798c)  octets : `41 78 f3 0f 59 05 8c 79 db 00`
- 0x006fb395 [.text] mulss xmm0  (constante 0x00db798c)  octets : `41 78 f3 0f 59 05 8c 79 db 00`
- 0x006fb8d2 [.text] mulss xmm0  (constante 0x00db798c)  octets : `41 78 f3 0f 59 05 8c 79 db 00`
- 0x006fcc9b [.text] mulss xmm1  (constante 0x00db798c)  octets : `28 d4 f3 0f 59 0d 8c 79 db 00`
- 0x006fcf91 [.text] mulss xmm1  (constante 0x00db798c)  octets : `48 78 f3 0f 59 0d 8c 79 db 00`
- 0x006fd668 [.text] mulss xmm1  (constante 0x00db798c)  octets : `48 78 f3 0f 59 0d 8c 79 db 00`
- 0x006fdb4f [.text] mulss xmm1  (constante 0x00db798c)  octets : `4a 78 f3 0f 59 0d 8c 79 db 00`
- 0x006fddad [.text] movss xmm7  (constante 0x00db798c)  octets : `ef ff f3 0f 10 3d 8c 79 db 00`
- 0x006fe425 [.text] comiss xmm0  (constante 0x00db798c)  octets : `c9 d0 ff 0f 2f 05 8c 79 db 00`
- 0x006ffa60 [.text] movss xmm7  (constante 0x00db798c)  octets : `ff ff f3 0f 10 3d 8c 79 db 00`
- 0x00700114 [.text] movss xmm4  (constante 0x00db798c)  octets : `ff ff f3 0f 10 25 8c 79 db 00`
- 0x00702649 [.text] mulss xmm0  (constante 0x00db798c)  octets : `43 1c f3 0f 59 05 8c 79 db 00`
- 0x0070687e [.text] mulss xmm0  (constante 0x00db798c)  octets : `db 00 f3 0f 59 05 8c 79 db 00`
- 0x007068cf [.text] subss xmm0  (constante 0x00db798c)  octets : `db 00 f3 0f 5c 05 8c 79 db 00`
- 0x0070ca18 [.text] mulss xmm2  (constante 0x00db798c)  octets : `00 00 f3 0f 59 15 8c 79 db 00`
- 0x0070f211 [.text] movss xmm4  (constante 0x00db798c)  octets : `00 00 f3 0f 10 25 8c 79 db 00`
- 0x00710890 [.text] movss xmm4  (constante 0x00db798c)  octets : `00 00 f3 0f 10 25 8c 79 db 00`
- 0x00712be9 [.text] mulss xmm0  (constante 0x00db798c)  octets : `46 1c f3 0f 59 05 8c 79 db 00`
- ... 12 de plus

### 0.01 (copies en donnees : 0x00cff488, 0x00d36910, 0x00db71a0)
- 0x004764b7 [.text] movss xmm3  (constante 0x00db71a0)  octets : `7b 42 f3 0f 10 1d a0 71 db 00`
- 0x0047893a [.text] addss xmm0  (constante 0x00db71a0)  octets : `ec 08 f3 0f 58 05 a0 71 db 00`
- 0x004e4a66 [.text] mulss xmm1  (constante 0x00db71a0)  octets : `10 08 f3 0f 59 0d a0 71 db 00`
- 0x004e84cb [.text] movss xmm0  (constante 0x00db71a0)  octets : `74 5c f3 0f 10 05 a0 71 db 00`
- 0x004ea269 [.text] movss xmm2  (constante 0x00db71a0)  octets : `24 04 f3 0f 10 15 a0 71 db 00`
- 0x004ea2bb [.text] movss xmm2  (constante 0x00db71a0)  octets : `24 0c f3 0f 10 15 a0 71 db 00`
- 0x004ea303 [.text] movss xmm2  (constante 0x00db71a0)  octets : `24 0c f3 0f 10 15 a0 71 db 00`
- 0x004ed9ff [.text] movss xmm1  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 0d a0 71 db 00`
- 0x0054aa76 [.text] movss xmm2  (constante 0x00db71a0)  octets : `56 14 f3 0f 10 15 a0 71 db 00`
- 0x0054ab0c [.text] movss xmm2  (constante 0x00db71a0)  octets : `56 1c f3 0f 10 15 a0 71 db 00`
- 0x0054aba2 [.text] movss xmm2  (constante 0x00db71a0)  octets : `56 18 f3 0f 10 15 a0 71 db 00`
- 0x0054acc2 [.text] movss xmm0  (constante 0x00db71a0)  octets : `28 d0 f3 0f 10 05 a0 71 db 00`
- 0x0057478c [.text] movss xmm3  (constante 0x00db71a0)  octets : `5d f8 f3 0f 10 1d a0 71 db 00`
- 0x005772cc [.text] subss xmm0  (constante 0x00db71a0)  octets : `db 00 f3 0f 5c 05 a0 71 db 00`
- 0x0057733b [.text] subss xmm0  (constante 0x00db71a0)  octets : `db 00 f3 0f 5c 05 a0 71 db 00`
- 0x005853b2 [.text] minss xmm3  (constante 0x00db71a0)  octets : `db 00 f3 0f 5d 1d a0 71 db 00`
- 0x00585509 [.text] minss xmm3  (constante 0x00db71a0)  octets : `db 00 f3 0f 5d 1d a0 71 db 00`
- 0x0058d307 [.text] subss xmm0  (constante 0x00db71a0)  octets : `c4 08 f3 0f 5c 05 a0 71 db 00`
- 0x0058d31b [.text] addss xmm1  (constante 0x00db71a0)  octets : `59 c8 f3 0f 58 0d a0 71 db 00`
- 0x00590232 [.text] movss xmm7  (constante 0x00db71a0)  octets : `db 00 f3 0f 10 3d a0 71 db 00`
- 0x005902f6 [.text] movss xmm7  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 3d a0 71 db 00`
- 0x00590403 [.text] movss xmm7  (constante 0x00db71a0)  octets : `45 f8 f3 0f 10 3d a0 71 db 00`
- 0x005904c7 [.text] movss xmm7  (constante 0x00db71a0)  octets : `af c6 f3 0f 10 3d a0 71 db 00`
- 0x00590720 [.text] movss xmm4  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 25 a0 71 db 00`
- 0x005907f5 [.text] movss xmm4  (constante 0x00db71a0)  octets : `db 00 f3 0f 10 25 a0 71 db 00`
- 0x005909a5 [.text] movss xmm4  (constante 0x00db71a0)  octets : `58 f4 f3 0f 10 25 a0 71 db 00`
- 0x00599ef0 [.text] movss xmm3  (constante 0x00db71a0)  octets : `2b 00 f3 0f 10 1d a0 71 db 00`
- 0x00599f7e [.text] movss xmm2  (constante 0x00db71a0)  octets : `2b 00 f3 0f 10 15 a0 71 db 00`
- 0x0059a071 [.text] movss xmm3  (constante 0x00db71a0)  octets : `2b 00 f3 0f 10 1d a0 71 db 00`
- 0x0059a0ff [.text] movss xmm2  (constante 0x00db71a0)  octets : `2b 00 f3 0f 10 15 a0 71 db 00`
- 0x005aa3f0 [.text] movss xmm1  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 0d a0 71 db 00`
- 0x005aa4d5 [.text] movss xmm1  (constante 0x00db71a0)  octets : `57 e4 f3 0f 10 0d a0 71 db 00`
- 0x005aa679 [.text] movss xmm1  (constante 0x00db71a0)  octets : `57 e4 f3 0f 10 0d a0 71 db 00`
- 0x005c6837 [.text] movss xmm1  (constante 0x00db71a0)  octets : `33 c9 f3 0f 10 0d a0 71 db 00`
- 0x005c7170 [.text] movss xmm1  (constante 0x00db71a0)  octets : `ff ff f3 0f 10 0d a0 71 db 00`
- 0x005c74d3 [.text] movss xmm1  (constante 0x00db71a0)  octets : `ff ff f3 0f 10 0d a0 71 db 00`
- 0x005c76ad [.text] movss xmm1  (constante 0x00db71a0)  octets : `5c c1 f3 0f 10 0d a0 71 db 00`
- 0x005c773a [.text] movss xmm1  (constante 0x00db71a0)  octets : `ff ff f3 0f 10 0d a0 71 db 00`
- 0x005c7b47 [.text] movss xmm1  (constante 0x00db71a0)  octets : `0c 42 f3 0f 10 0d a0 71 db 00`
- 0x005c8337 [.text] comiss xmm0  (constante 0x00db71a0)  octets : `fe ff ff 0f 2f 05 a0 71 db 00`
- 0x005c866c [.text] mulss xmm0  (constante 0x00db71a0)  octets : `8b d7 f3 0f 59 05 a0 71 db 00`
- 0x005d4ee8 [.text] comiss xmm0  (constante 0x00db71a0)  octets : `0f 5c c1 0f 2f 05 a0 71 db 00`
- 0x005de9f1 [.text] comiss xmm1  (constante 0x00db71a0)  octets : `0f 59 c8 0f 2f 0d a0 71 db 00`
- 0x005e624a [.text] comiss xmm0  (constante 0x00db71a0)  octets : `4b e2 ff 0f 2f 05 a0 71 db 00`
- 0x005e7612 [.text] movss xmm0  (constante 0x00db71a0)  octets : `57 db f3 0f 10 05 a0 71 db 00`
- 0x005ebcd0 [.text] mulss xmm0  (constante 0x00db71a0)  octets : `45 fc f3 0f 59 05 a0 71 db 00`
- 0x005ecb12 [.text] movss xmm0  (constante 0x00db71a0)  octets : `76 56 f3 0f 10 05 a0 71 db 00`
- 0x0060e817 [.text] movss xmm2  (constante 0x00db71a0)  octets : `77 04 f3 0f 10 15 a0 71 db 00`
- 0x00618fba [.text] movss xmm0  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 05 a0 71 db 00`
- 0x00629be9 [.text] movss xmm1  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 0d a0 71 db 00`
- 0x00629f64 [.text] movss xmm0  (constante 0x00db71a0)  octets : `00 00 f3 0f 10 05 a0 71 db 00`
- 0x00688ede [.text] movss xmm4  (constante 0x00db71a0)  octets : `76 10 f3 0f 10 25 a0 71 db 00`
- 0x00688f64 [.text] movss xmm4  (constante 0x00db71a0)  octets : `76 19 f3 0f 10 25 a0 71 db 00`
- 0x0068ff43 [.text] movss xmm4  (constante 0x00db71a0)  octets : `76 10 f3 0f 10 25 a0 71 db 00`
- 0x0068ffc9 [.text] movss xmm4  (constante 0x00db71a0)  octets : `76 19 f3 0f 10 25 a0 71 db 00`
- 0x0069e250 [.text] minss xmm1  (constante 0x00db71a0)  octets : `db 00 f3 0f 5d 0d a0 71 db 00`
- 0x006b2148 [.text] movss xmm0  (constante 0x00db71a0)  octets : `7d 08 f3 0f 10 05 a0 71 db 00`
- 0x006b3a58 [.text] movss xmm0  (constante 0x00db71a0)  octets : `45 08 f3 0f 10 05 a0 71 db 00`
- 0x006be7f0 [.text] subss xmm0  (constante 0x00db71a0)  octets : `00 00 f3 0f 5c 05 a0 71 db 00`
- 0x006c612d [.text] movss xmm0  (constante 0x00db71a0)  octets : `28 c8 f3 0f 10 05 a0 71 db 00`
- ... 77 de plus

### 0.1 (copies en donnees : 0x00ce560c, 0x00d3690c, 0x00db71f8, 0x00db8600, 0x00db8830, 0x00e1e75c)
- 0x00459a48 [.text] mulss xmm2  (constante 0x00db71f8)  octets : `00 00 f3 0f 59 15 f8 71 db 00`
- 0x004646a2 [.text] movss xmm3  (constante 0x00db71f8)  octets : `41 54 f3 0f 10 1d f8 71 db 00`
- 0x0046eabd [.text] movaps xmm0  (constante 0x00db8600)  octets : `02 00 00 0f 28 05 00 86 db 00`
- 0x0046eacb [.text] movaps xmm0  (constante 0x00db8830)  octets : `02 00 00 0f 28 05 30 88 db 00`
- 0x0048e2f6 [.text] movss xmm3  (constante 0x00db71f8)  octets : `00 00 f3 0f 10 1d f8 71 db 00`
- 0x0048e38b [.text] movss xmm3  (constante 0x00db71f8)  octets : `00 00 f3 0f 10 1d f8 71 db 00`
- 0x0048e418 [.text] movss xmm3  (constante 0x00db71f8)  octets : `cf 00 f3 0f 10 1d f8 71 db 00`
- 0x0048e49f [.text] movss xmm3  (constante 0x00db71f8)  octets : `5d c3 f3 0f 10 1d f8 71 db 00`
- 0x0048e536 [.text] movss xmm3  (constante 0x00db71f8)  octets : `45 f8 f3 0f 10 1d f8 71 db 00`
- 0x0048e5cb [.text] movss xmm3  (constante 0x00db71f8)  octets : `5d c3 f3 0f 10 1d f8 71 db 00`
- 0x004e7bdb [.text] movss xmm0  (constante 0x00db71f8)  octets : `74 54 f3 0f 10 05 f8 71 db 00`
- 0x004eda0e [.text] movss xmm0  (constante 0x00db71f8)  octets : `d6 01 f3 0f 10 05 f8 71 db 00`
- 0x004eda92 [.text] movss xmm1  (constante 0x00db71f8)  octets : `ec 0c f3 0f 10 0d f8 71 db 00`
- 0x004f2261 [.text] ?   (constante 0x00e1e75c)  octets : `fc 5d 8d 55 b4 68 5c e7 e1 00`
- 0x005780ab [.text] mulss xmm3  (constante 0x00db71f8)  octets : `10 00 f3 0f 59 1d f8 71 db 00`
- 0x005781ad [.text] mulss xmm2  (constante 0x00db71f8)  octets : `28 d3 f3 0f 59 15 f8 71 db 00`
- 0x00583841 [.text] mulss xmm1  (constante 0x00db71f8)  octets : `00 00 f3 0f 59 0d f8 71 db 00`
- 0x0058523c [.text] mulss xmm6  (constante 0x00db71f8)  octets : `76 08 f3 0f 59 35 f8 71 db 00`
- 0x00587362 [.text] addss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 58 05 f8 71 db 00`
- 0x00587aff [.text] addss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 58 05 f8 71 db 00`
- 0x00589778 [.text] movss xmm0  (constante 0x00db71f8)  octets : `ec 51 f3 0f 10 05 f8 71 db 00`
- 0x005897d8 [.text] movss xmm0  (constante 0x00db71f8)  octets : `ec 51 f3 0f 10 05 f8 71 db 00`
- 0x0058cb63 [.text] movss xmm0  (constante 0x00db71f8)  octets : `5f c8 f3 0f 10 05 f8 71 db 00`
- 0x0058cc45 [.text] movss xmm1  (constante 0x00db71f8)  octets : `5d 08 f3 0f 10 0d f8 71 db 00`
- 0x0058cde0 [.text] subss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 5c 05 f8 71 db 00`
- 0x0058ce7a [.text] subss xmm0  (constante 0x00db71f8)  octets : `59 d3 f3 0f 5c 05 f8 71 db 00`
- 0x0058d2ed [.text] addss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 58 05 f8 71 db 00`
- 0x0058d549 [.text] movss xmm1  (constante 0x00db71f8)  octets : `5d 08 f3 0f 10 0d f8 71 db 00`
- 0x0058e88c [.text] movss xmm1  (constante 0x00db71f8)  octets : `00 00 f3 0f 10 0d f8 71 db 00`
- 0x0058eacc [.text] movss xmm1  (constante 0x00db71f8)  octets : `55 e4 f3 0f 10 0d f8 71 db 00`
- 0x0059b00d [.text] comiss xmm0  (constante 0x00db71f8)  octets : `72 db 00 0f 2f 05 f8 71 db 00`
- 0x005a22cc [.text] movss xmm5  (constante 0x00db71f8)  octets : `88 18 f3 0f 10 2d f8 71 db 00`
- 0x005b8419 [.text] movss xmm1  (constante 0x00db71f8)  octets : `59 d9 f3 0f 10 0d f8 71 db 00`
- 0x005c709b [.text] addss xmm0  (constante 0x00db71f8)  octets : `ff ff f3 0f 58 05 f8 71 db 00`
- 0x005c70ad [.text] subss xmm0  (constante 0x00db71f8)  octets : `ff ff f3 0f 5c 05 f8 71 db 00`
- 0x005c7f22 [.text] minss xmm0  (constante 0x00db71f8)  octets : `00 00 f3 0f 5d 05 f8 71 db 00`
- 0x005d1b07 [.text] minss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 5d 05 f8 71 db 00`
- 0x005d4b5f [.text] comiss xmm0  (constante 0x00db71f8)  octets : `72 db 00 0f 2f 05 f8 71 db 00`
- 0x005e057b [.text] movss xmm1  (constante 0x00db71f8)  octets : `db 00 f3 0f 10 0d f8 71 db 00`
- 0x005e4cfa [.text] addss xmm1  (constante 0x00db71f8)  octets : `db 00 f3 0f 58 0d f8 71 db 00`
- 0x005e6229 [.text] comiss xmm0  (constante 0x00db71f8)  octets : `10 04 18 0f 2f 05 f8 71 db 00`
- 0x005eb4ca [.text] fsub dword   (constante 0x00db71f8)  octets : `00 00 ff d0 d8 25 f8 71 db 00`
- 0x005fcab9 [.text] minss xmm3  (constante 0x00db71f8)  octets : `59 dd f3 0f 5d 1d f8 71 db 00`
- 0x0062abd1 [.text] addss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 58 05 f8 71 db 00`
- 0x0065a20b [.text] movss xmm0  (constante 0x00db71f8)  octets : `ff ff f3 0f 10 05 f8 71 db 00`
- 0x0065ba4c [.text] movss xmm0  (constante 0x00db71f8)  octets : `ff ff f3 0f 10 05 f8 71 db 00`
- 0x0065d165 [.text] movss xmm3  (constante 0x00db71f8)  octets : `da ff f3 0f 10 1d f8 71 db 00`
- 0x0065dfd0 [.text] comiss xmm0  (constante 0x00db71f8)  octets : `01 00 00 0f 2f 05 f8 71 db 00`
- 0x00664c56 [.text] movss xmm3  (constante 0x00db71f8)  octets : `da ff f3 0f 10 1d f8 71 db 00`
- 0x00687e3a [.text] minss xmm2  (constante 0x00db71f8)  octets : `db 00 f3 0f 5d 15 f8 71 db 00`
- 0x00687f0b [.text] minss xmm1  (constante 0x00db71f8)  octets : `db 00 f3 0f 5d 0d f8 71 db 00`
- 0x006881d9 [.text] movss xmm1  (constante 0x00db71f8)  octets : `5c c1 f3 0f 10 0d f8 71 db 00`
- 0x0068fa14 [.text] minss xmm3  (constante 0x00db71f8)  octets : `24 14 f3 0f 5d 1d f8 71 db 00`
- 0x0068fadb [.text] minss xmm1  (constante 0x00db71f8)  octets : `db 00 f3 0f 5d 0d f8 71 db 00`
- 0x0068fdaa [.text] movss xmm1  (constante 0x00db71f8)  octets : `5c c1 f3 0f 10 0d f8 71 db 00`
- 0x006be784 [.text] movss xmm4  (constante 0x00db71f8)  octets : `58 d2 f3 0f 10 25 f8 71 db 00`
- 0x006c4c69 [.text] movss xmm4  (constante 0x00db71f8)  octets : `57 db f3 0f 10 25 f8 71 db 00`
- 0x006c60a5 [.text] movss xmm1  (constante 0x00db71f8)  octets : `5d d1 f3 0f 10 0d f8 71 db 00`
- 0x006c61b8 [.text] comiss xmm0  (constante 0x00db71f8)  octets : `01 00 00 0f 2f 05 f8 71 db 00`
- 0x006ca199 [.text] subss xmm0  (constante 0x00db71f8)  octets : `db 00 f3 0f 5c 05 f8 71 db 00`
- ... 152 de plus

### 0.5 (copies en donnees : 0x00ce55e0, 0x00ce5608, 0x00cea3d0, 0x00d00cb0, 0x00d00cb8, 0x00d00ccc)
- 0x004112ec [.text] addss xmm0  (constante 0x00db72cc)  octets : `db 00 f3 0f 58 05 cc 72 db 00`
- 0x0041132d [.text] addss xmm0  (constante 0x00db72cc)  octets : `db 00 f3 0f 58 05 cc 72 db 00`
- 0x0041136f [.text] addss xmm0  (constante 0x00db72cc)  octets : `db 00 f3 0f 58 05 cc 72 db 00`
- 0x004113b1 [.text] addss xmm0  (constante 0x00db72cc)  octets : `db 00 f3 0f 58 05 cc 72 db 00`
- 0x00422376 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `45 d8 f3 0f 59 05 cc 72 db 00`
- 0x00422388 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `fe ff f3 0f 59 05 cc 72 db 00`
- 0x004223a8 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `76 08 f3 0f 59 05 cc 72 db 00`
- 0x0042baf4 [.text] movss xmm0  (constante 0x00db72cc)  octets : `4e 48 f3 0f 10 05 cc 72 db 00`
- 0x0042ddf2 [.text] movss xmm4  (constante 0x00db72cc)  octets : `55 b4 f3 0f 10 25 cc 72 db 00`
- 0x0042dfcd [.text] movss xmm0  (constante 0x00db72cc)  octets : `45 d8 f3 0f 10 05 cc 72 db 00`
- 0x0042e09b [.text] movss xmm0  (constante 0x00db72cc)  octets : `58 10 f3 0f 10 05 cc 72 db 00`
- 0x0042e4ee [.text] movss xmm4  (constante 0x00db72cc)  octets : `c2 03 f3 0f 10 25 cc 72 db 00`
- 0x0042e605 [.text] movss xmm4  (constante 0x00db72cc)  octets : `ff ff f3 0f 10 25 cc 72 db 00`
- 0x0042ec6d [.text] mulss xmm2  (constante 0x00db72cc)  octets : `ec 70 f3 0f 59 15 cc 72 db 00`
- 0x00430c4c [.text] mulss xmm0  (constante 0x00db72cc)  octets : `00 00 f3 0f 59 05 cc 72 db 00`
- 0x00430d52 [.text] mulss xmm2  (constante 0x00db72cc)  octets : `5e d1 f3 0f 59 15 cc 72 db 00`
- 0x00430d5a [.text] addss xmm2  (constante 0x00db72cc)  octets : `db 00 f3 0f 58 15 cc 72 db 00`
- 0x00430e52 [.text] mulss xmm1  (constante 0x00db72cc)  octets : `7f 34 f3 0f 59 0d cc 72 db 00`
- 0x00430e64 [.text] addss xmm1  (constante 0x00db72cc)  octets : `47 28 f3 0f 58 0d cc 72 db 00`
- 0x00430f50 [.text] mulss xmm4  (constante 0x00db72cc)  octets : `5e c1 f3 0f 59 25 cc 72 db 00`
- 0x00430f5c [.text] addss xmm4  (constante 0x00db72cc)  octets : `5e fa f3 0f 58 25 cc 72 db 00`
- 0x00430fa1 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `00 00 f3 0f 59 05 cc 72 db 00`
- 0x00431213 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `58 c0 f3 0f 59 05 cc 72 db 00`
- 0x004315f8 [.text] movss xmm3  (constante 0x00db72cc)  octets : `00 00 f3 0f 10 1d cc 72 db 00`
- 0x004316d5 [.text] movss xmm2  (constante 0x00db72cc)  octets : `59 d8 f3 0f 10 15 cc 72 db 00`
- 0x004317cf [.text] mulss xmm0  (constante 0x00db72cc)  octets : `58 c0 f3 0f 59 05 cc 72 db 00`
- 0x00431c11 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `58 c0 f3 0f 59 05 cc 72 db 00`
- 0x004337ae [.text] addss xmm0  (constante 0x00db72cc)  octets : `00 00 f3 0f 58 05 cc 72 db 00`
- 0x0043fd4d [.text] movss xmm0  (constante 0x00db72cc)  octets : `4e 08 f3 0f 10 05 cc 72 db 00`
- 0x0043fe0b [.text] movss xmm0  (constante 0x00db72cc)  octets : `4b 08 f3 0f 10 05 cc 72 db 00`
- 0x004404b7 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `c4 04 f3 0f 59 05 cc 72 db 00`
- 0x00440873 [.text] mulss xmm3  (constante 0x00db72cc)  octets : `00 00 f3 0f 59 1d cc 72 db 00`
- 0x0044087e [.text] mulss xmm5  (constante 0x00db72cc)  octets : `d6 50 f3 0f 59 2d cc 72 db 00`
- 0x00440b0e [.text] movss xmm2  (constante 0x00db72cc)  octets : `8b c8 f3 0f 10 15 cc 72 db 00`
- 0x00440bb2 [.text] movss xmm2  (constante 0x00db72cc)  octets : `8b d0 f3 0f 10 15 cc 72 db 00`
- 0x00440ed1 [.text] movss xmm0  (constante 0x00db72cc)  octets : `45 08 f3 0f 10 05 cc 72 db 00`
- 0x0044159b [.text] mulss xmm0  (constante 0x00db72cc)  octets : `8b d6 f3 0f 59 05 cc 72 db 00`
- 0x00441ae9 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `24 10 f3 0f 59 05 cc 72 db 00`
- 0x004428f6 [.text] movss xmm2  (constante 0x00db72cc)  octets : `db 00 f3 0f 10 15 cc 72 db 00`
- 0x00442981 [.text] movss xmm1  (constante 0x00db72cc)  octets : `00 00 f3 0f 10 0d cc 72 db 00`
- 0x004429b6 [.text] movss xmm1  (constante 0x00db72cc)  octets : `ff ff f3 0f 10 0d cc 72 db 00`
- 0x00442a48 [.text] movss xmm1  (constante 0x00db72cc)  octets : `00 00 f3 0f 10 0d cc 72 db 00`
- 0x00442abf [.text] movss xmm1  (constante 0x00db72cc)  octets : `00 00 f3 0f 10 0d cc 72 db 00`
- 0x00442afb [.text] movss xmm2  (constante 0x00db72cc)  octets : `5d ec f3 0f 10 15 cc 72 db 00`
- 0x00442b15 [.text] movss xmm2  (constante 0x00db72cc)  octets : `5d ec f3 0f 10 15 cc 72 db 00`
- 0x00442b73 [.text] movss xmm1  (constante 0x00db72cc)  octets : `55 ec f3 0f 10 0d cc 72 db 00`
- 0x00444b15 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `00 00 f3 0f 59 05 cc 72 db 00`
- 0x00456c0c [.text] movss xmm4  (constante 0x00db72cc)  octets : `db 00 f3 0f 10 25 cc 72 db 00`
- 0x00457790 [.text] addss xmm0  (constante 0x00db72cc)  octets : `42 34 f3 0f 58 05 cc 72 db 00`
- 0x00457b14 [.text] mulss xmm2  (constante 0x00db72cc)  octets : `28 ca f3 0f 59 15 cc 72 db 00`
- 0x00457c8c [.text] mulss xmm0  (constante 0x00db72cc)  octets : `5d ec f3 0f 59 05 cc 72 db 00`
- 0x00457cc9 [.text] mulss xmm0  (constante 0x00db72cc)  octets : `28 c4 f3 0f 59 05 cc 72 db 00`
- 0x00457ec0 [.text] movss xmm7  (constante 0x00db72cc)  octets : `00 00 f3 0f 10 3d cc 72 db 00`
- 0x00458004 [.text] movss xmm7  (constante 0x00db72cc)  octets : `5d 08 f3 0f 10 3d cc 72 db 00`
- 0x0045811d [.text] movss xmm7  (constante 0x00db72cc)  octets : `75 bc f3 0f 10 3d cc 72 db 00`
- 0x00459a58 [.text] movss xmm0  (constante 0x00db72cc)  octets : `00 00 f3 0f 10 05 cc 72 db 00`
- 0x0045d776 [.text] addss xmm1  (constante 0x00db72cc)  octets : `00 50 f3 0f 58 0d cc 72 db 00`
- 0x0045d7a9 [.text] addss xmm1  (constante 0x00db72cc)  octets : `4d c0 f3 0f 58 0d cc 72 db 00`
- 0x0045d7f8 [.text] addss xmm2  (constante 0x00db72cc)  octets : `00 00 f3 0f 58 15 cc 72 db 00`
- 0x0045d828 [.text] addss xmm2  (constante 0x00db72cc)  octets : `55 c0 f3 0f 58 15 cc 72 db 00`
- ... 1473 de plus

### 48 (copies en donnees : 0x00db79b4)
- 0x006c34c3 [.text] mulss xmm0  (constante 0x00db79b4)  octets : `4d 88 f3 0f 59 05 b4 79 db 00`
- 0x0071a0d6 [.text] maxss xmm0  (constante 0x00db79b4)  octets : `28 c1 f3 0f 5f 05 b4 79 db 00`

### 72 (copies en donnees : 0x00d7249c, 0x00db79cc)
- 0x0071a0ec [.text] maxss xmm1  (constante 0x00db79cc)  octets : `75 14 f3 0f 5f 0d cc 79 db 00`

### 144 (copies en donnees : 0x00db7a00)
- 0x0071a0cb [.text] movss xmm2  (constante 0x00db7a00)  octets : `ff ff f3 0f 10 15 00 7a db 00`

### 600 (copies en donnees : 0x00db7a70)
- 0x0045d3f1 [.text] mulss xmm0  (constante 0x00db7a70)  octets : `46 18 f3 0f 59 05 70 7a db 00`
- 0x005e4f97 [.text] movss xmm0  (constante 0x00db7a70)  octets : `5e c3 f3 0f 10 05 70 7a db 00`
- 0x007018fc [.text] subss xmm1  (constante 0x00db7a70)  octets : `ff ff f3 0f 5c 0d 70 7a db 00`
- 0x00701d5e [.text] comiss xmm0  (constante 0x00db7a70)  octets : `fd ff ff 0f 2f 05 70 7a db 00`
- 0x00701d69 [.text] addss xmm1  (constante 0x00db7a70)  octets : `28 c8 f3 0f 58 0d 70 7a db 00`
- 0x00701f52 [.text] movss xmm0  (constante 0x00db7a70)  octets : `ff ff f3 0f 10 05 70 7a db 00`
- 0x0077dd70 [.text] movss xmm3  (constante 0x00db7a70)  octets : `ff ff f3 0f 10 1d 70 7a db 00`
- 0x007c7379 [.text] divss xmm0  (constante 0x00db7a70)  octets : `db 00 f3 0f 5e 05 70 7a db 00`
- 0x007f77aa [.text] movss xmm1  (constante 0x00db7a70)  octets : `4d b8 f3 0f 10 0d 70 7a db 00`

### 1800 (copies en donnees : aucune)

### -1800 (copies en donnees : 0x00db7e54)
- 0x007018e5 [.text] movss xmm2  (constante 0x00db7e54)  octets : `70 00 f3 0f 10 15 54 7e db 00`
- 0x00701d2f [.text] comiss xmm0  (constante 0x00db7e54)  octets : `fd ff ff 0f 2f 05 54 7e db 00`

### 80 (copies en donnees : 0x00db79d4)
- 0x004df49b [.text] movss xmm1  (constante 0x00db79d4)  octets : `57 d2 f3 0f 10 0d d4 79 db 00`
- 0x00629851 [.text] minss xmm0  (constante 0x00db79d4)  octets : `db 00 f3 0f 5d 05 d4 79 db 00`
- 0x006fe330 [.text] minss xmm5  (constante 0x00db79d4)  octets : `ff ff f3 0f 5d 2d d4 79 db 00`
- 0x00706854 [.text] subss xmm0  (constante 0x00db79d4)  octets : `db 00 f3 0f 5c 05 d4 79 db 00`
- 0x0073fd52 [.text] movss xmm2  (constante 0x00db79d4)  octets : `5a c2 f3 0f 10 15 d4 79 db 00`
- 0x00868715 [.text] movss xmm1  (constante 0x00db79d4)  octets : `00 00 f3 0f 10 0d d4 79 db 00`

### 1200 (copies en donnees : 0x00db7a94, 0x00e1e71c, 0x00e1e72c)
- 0x004f1b41 [.text] ?   (constante 0x00e1e71c)  octets : `fc 4d 8d 55 b4 68 1c e7 e1 00`
- 0x004f1d09 [.text] ?   (constante 0x00e1e72c)  octets : `fc 51 8d 55 b4 68 2c e7 e1 00`
- 0x007013e0 [.text] movss xmm2  (constante 0x00db7a94)  octets : `d0 ff f3 0f 10 15 94 7a db 00`
- 0x0070147d [.text] movss xmm2  (constante 0x00db7a94)  octets : `d0 ff f3 0f 10 15 94 7a db 00`
- 0x007166d2 [.text] fld dword   (constante 0x00e1e71c)  octets : `cc cc cc cc d9 05 1c e7 e1 00`
- 0x00721b32 [.text] fld dword   (constante 0x00e1e72c)  octets : `cc cc cc cc d9 05 2c e7 e1 00`
- 0x00723249 [.text] divss xmm2  (constante 0x00db7a94)  octets : `57 c9 f3 0f 5e 15 94 7a db 00`

### 1000 (copies en donnees : 0x00db7a8c, 0x00e1e704, 0x00e1e708, 0x00e1e70c, 0x00e1eab4)
- 0x00462f4e [.text] divss xmm3  (constante 0x00db7a8c)  octets : `76 16 f3 0f 5e 1d 8c 7a db 00`
- 0x00462f64 [.text] divss xmm3  (constante 0x00db7a8c)  octets : `eb 19 f3 0f 5e 1d 8c 7a db 00`
- 0x0048fde9 [.text] divss xmm0  (constante 0x00db7a8c)  octets : `5a c0 f3 0f 5e 05 8c 7a db 00`
- 0x004d6fcb [.text] movss xmm3  (constante 0x00db7a8c)  octets : `57 54 f3 0f 10 1d 8c 7a db 00`
- 0x004dc1b0 [.text] movss xmm0  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 05 8c 7a db 00`
- 0x004f1895 [.text] ?   (constante 0x00e1e704)  octets : `fc 47 8d 55 b4 68 04 e7 e1 00`
- 0x004f1907 [.text] ?   (constante 0x00e1e708)  octets : `fc 48 8d 55 b4 68 08 e7 e1 00`
- 0x004f1979 [.text] ?   (constante 0x00e1e70c)  octets : `fc 49 8d 55 b4 68 0c e7 e1 00`
- 0x004f82e2 [.text] ?   (constante 0x00e1eab4)  octets : `00 00 8d 55 b4 68 b4 ea e1 00`
- 0x0054ac2d [.text] movss xmm3  (constante 0x00db7a8c)  octets : `c4 08 f3 0f 10 1d 8c 7a db 00`
- 0x0055418a [.text] divss xmm0  (constante 0x00db7a8c)  octets : `40 28 f3 0f 5e 05 8c 7a db 00`
- 0x0055481f [.text] divss xmm0  (constante 0x00db7a8c)  octets : `40 28 f3 0f 5e 05 8c 7a db 00`
- 0x005837c4 [.text] divss xmm0  (constante 0x00db7a8c)  octets : `32 c0 f3 0f 5e 05 8c 7a db 00`
- 0x0059bbb0 [.text] movss xmm0  (constante 0x00db7a8c)  octets : `00 c3 f3 0f 10 05 8c 7a db 00`
- 0x005e236c [.text] minss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5d 05 8c 7a db 00`
- 0x005ec102 [.text] fld dword   (constante 0x00e1e704)  octets : `cc cc cc cc d9 05 04 e7 e1 00`
- 0x005ecac5 [.text] movss xmm0  (constante 0x00db7a8c)  octets : `00 5e f3 0f 10 05 8c 7a db 00`
- 0x005ed310 [.text] movss xmm0  (constante 0x00db7a8c)  octets : `00 c3 f3 0f 10 05 8c 7a db 00`
- 0x006002ab [.text] movss xmm1  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 0d 8c 7a db 00`
- 0x00621edd [.text] movss xmm0  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 05 8c 7a db 00`
- 0x00642f73 [.text] fld dword   (constante 0x00db7a8c)  octets : `84 c0 75 0b d9 05 8c 7a db 00`
- 0x006b2212 [.text] fld dword   (constante 0x00e1e70c)  octets : `cc cc cc cc d9 05 0c e7 e1 00`
- 0x006b3085 [.text] movss xmm0  (constante 0x00e1e704)  octets : `d6 ff f3 0f 10 05 04 e7 e1 00`
- 0x006bc0ac [.text] movss xmm0  (constante 0x00e1e708)  octets : `00 00 f3 0f 10 05 08 e7 e1 00`
- 0x006c2c05 [.text] movss xmm0  (constante 0x00db7a8c)  octets : `74 0a f3 0f 10 05 8c 7a db 00`
- 0x006c499b [.text] movss xmm3  (constante 0x00e1eab4)  octets : `2b d0 f3 0f 10 1d b4 ea e1 00`
- 0x006cd20b [.text] movss xmm2  (constante 0x00db7a8c)  octets : `5a c2 f3 0f 10 15 8c 7a db 00`
- 0x006d105d [.text] divss xmm0  (constante 0x00db7a8c)  octets : `ff 51 f3 0f 5e 05 8c 7a db 00`
- 0x006d13cb [.text] subss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5c 05 8c 7a db 00`
- 0x006d142f [.text] subss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5c 05 8c 7a db 00`
- 0x006d255b [.text] mulss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 59 05 8c 7a db 00`
- 0x006d2563 [.text] addss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 58 05 8c 7a db 00`
- 0x006d2594 [.text] subss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5c 05 8c 7a db 00`
- 0x006d25e7 [.text] subss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5c 05 8c 7a db 00`
- 0x006d2d3b [.text] mulss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 59 05 8c 7a db 00`
- 0x006d2d43 [.text] addss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 58 05 8c 7a db 00`
- 0x006d2d74 [.text] subss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5c 05 8c 7a db 00`
- 0x006d2dd0 [.text] subss xmm0  (constante 0x00db7a8c)  octets : `db 00 f3 0f 5c 05 8c 7a db 00`
- 0x006d6e1c [.text] movss xmm0  (constante 0x00db7a8c)  octets : `76 0d f3 0f 10 05 8c 7a db 00`
- 0x006f7ebe [.text] movss xmm2  (constante 0x00db7a8c)  octets : `ff ff f3 0f 10 15 8c 7a db 00`
- 0x00701a7d [.text] movss xmm1  (constante 0x00db7a8c)  octets : `d0 ff f3 0f 10 0d 8c 7a db 00`
- 0x007062bc [.text] divss xmm0  (constante 0x00db7a8c)  octets : `24 38 f3 0f 5e 05 8c 7a db 00`
- 0x0070635a [.text] mulss xmm0  (constante 0x00db7a8c)  octets : `5a c0 f3 0f 59 05 8c 7a db 00`
- 0x007166e2 [.text] fld dword   (constante 0x00db7a8c)  octets : `cc cc cc cc d9 05 8c 7a db 00`
- 0x0071a959 [.text] movss xmm3  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 1d 8c 7a db 00`
- 0x0071b8bf [.text] movss xmm3  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 1d 8c 7a db 00`
- 0x0071c4dc [.text] movss xmm3  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 1d 8c 7a db 00`
- 0x0071d06e [.text] comiss xmm0  (constante 0x00db7a8c)  octets : `ff ff ff 0f 2f 05 8c 7a db 00`
- 0x0071d39f [.text] movss xmm2  (constante 0x00db7a8c)  octets : `57 c0 f3 0f 10 15 8c 7a db 00`
- 0x00722f55 [.text] movss xmm1  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 0d 8c 7a db 00`
- 0x0072352d [.text] movss xmm1  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 0d 8c 7a db 00`
- 0x0072392f [.text] divss xmm2  (constante 0x00db7a8c)  octets : `57 c9 f3 0f 5e 15 8c 7a db 00`
- 0x007240c2 [.text] movss xmm2  (constante 0x00db7a8c)  octets : `ff ff f3 0f 10 15 8c 7a db 00`
- 0x00724392 [.text] movss xmm1  (constante 0x00db7a8c)  octets : `ff ff f3 0f 10 0d 8c 7a db 00`
- 0x0072ba7a [.text] movss xmm0  (constante 0x00db7a8c)  octets : `76 0a f3 0f 10 05 8c 7a db 00`
- 0x00748289 [.text] movss xmm0  (constante 0x00db7a8c)  octets : `00 00 f3 0f 10 05 8c 7a db 00`
- 0x0074d3de [.text] movss xmm0  (constante 0x00db7a8c)  octets : `76 12 f3 0f 10 05 8c 7a db 00`
- 0x00761dfc [.text] addss xmm0  (constante 0x00db7a8c)  octets : `ff ff f3 0f 58 05 8c 7a db 00`
- 0x007b6643 [.text] divss xmm0  (constante 0x00db7a8c)  octets : `ff ff f3 0f 5e 05 8c 7a db 00`
- 0x007b94d8 [.text] divss xmm2  (constante 0x00db7a8c)  octets : `c1 10 f3 0f 5e 15 8c 7a db 00`
- ... 6 de plus

### -1000 (copies en donnees : 0x00db7e50)
- 0x007019f6 [.text] comiss xmm0  (constante 0x00db7e50)  octets : `fd ff ff 0f 2f 05 50 7e db 00`
- 0x00701e5c [.text] movss xmm0  (constante 0x00db7e50)  octets : `ff ff f3 0f 10 05 50 7e db 00`

### 50 (copies en donnees : 0x00db79b8, 0x00db7f30, 0x00e1e9cc)
- 0x004f67d9 [.text] ?   (constante 0x00e1e9cc)  octets : `fc f9 8d 55 b4 68 cc e9 e1 00`
- 0x0058cf05 [.text] mulss xmm3  (constante 0x00db79b8)  octets : `7d 10 f3 0f 59 1d b8 79 db 00`
- 0x0061ad77 [.text] movss xmm2  (constante 0x00db79b8)  octets : `6a 08 f3 0f 10 15 b8 79 db 00`
- 0x00629c6b [.text] comiss xmm1  (constante 0x00db79b8)  octets : `0f 47 c1 0f 2f 0d b8 79 db 00`
- 0x006b5b13 [.text] movss xmm0  (constante 0x00e1e9cc)  octets : `f7 fe f3 0f 10 05 cc e9 e1 00`
- 0x006fe0a1 [.text] movss xmm0  (constante 0x00db79b8)  octets : `5f d0 f3 0f 10 05 b8 79 db 00`
- 0x006fe1b7 [.text] addss xmm2  (constante 0x00db79b8)  octets : `db 00 f3 0f 58 15 b8 79 db 00`
- 0x00705ab2 [.text] fld dword   (constante 0x00db79b8)  octets : `cc cc cc cc d9 05 b8 79 db 00`
- 0x007068c7 [.text] mulss xmm0  (constante 0x00db79b8)  octets : `04 90 f3 0f 59 05 b8 79 db 00`
- 0x0071d447 [.text] movss xmm0  (constante 0x00db79b8)  octets : `ff ff f3 0f 10 05 b8 79 db 00`
- 0x0072ea58 [.text] movss xmm2  (constante 0x00db79b8)  octets : `45 9c f3 0f 10 15 b8 79 db 00`
- 0x00746839 [.text] addss xmm0  (constante 0x00db79b8)  octets : `db 00 f3 0f 58 05 b8 79 db 00`
- 0x00767725 [.text] movss xmm2  (constante 0x00db79b8)  octets : `cd ff f3 0f 10 15 b8 79 db 00`
- 0x0077de1a [.text] movss xmm2  (constante 0x00db79b8)  octets : `ff ff f3 0f 10 15 b8 79 db 00`
- 0x007b9041 [.text] movaps xmm0  (constante 0x00db7f30)  octets : `0f 28 d8 0f 28 05 30 7f db 00`
- 0x007b9059 [.text] mulss xmm2  (constante 0x00db79b8)  octets : `00 00 f3 0f 59 15 b8 79 db 00`
- 0x007b9086 [.text] mulss xmm5  (constante 0x00db79b8)  octets : `80 3f f3 0f 59 2d b8 79 db 00`
- 0x007b90ab [.text] movaps xmm0  (constante 0x00db7f30)  octets : `00 00 00 0f 28 05 30 7f db 00`
- 0x007b910e [.text] mulss xmm5  (constante 0x00db79b8)  octets : `28 eb f3 0f 59 2d b8 79 db 00`
- 0x007b91ec [.text] mulss xmm1  (constante 0x00db79b8)  octets : `ff ff f3 0f 59 0d b8 79 db 00`
- 0x007b9287 [.text] mulss xmm1  (constante 0x00db79b8)  octets : `ff ff f3 0f 59 0d b8 79 db 00`
- 0x007bab0d [.text] movaps xmm0  (constante 0x00db7f30)  octets : `fb ff ff 0f 28 05 30 7f db 00`
- 0x007bab3f [.text] movaps xmm0  (constante 0x00db7f30)  octets : `00 00 00 0f 28 05 30 7f db 00`

### 100 (copies en donnees : 0x00db79e0)
- 0x004645f0 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `00 00 f3 0f 59 05 e0 79 db 00`
- 0x0047892f [.text] mulss xmm0  (constante 0x00db79e0)  octets : `45 dc f3 0f 59 05 e0 79 db 00`
- 0x004875e6 [.text] minss xmm3  (constante 0x00db79e0)  octets : `db 00 f3 0f 5d 1d e0 79 db 00`
- 0x004d6f3e [.text] movss xmm3  (constante 0x00db79e0)  octets : `57 50 f3 0f 10 1d e0 79 db 00`
- 0x004de3aa [.text] mulss xmm1  (constante 0x00db79e0)  octets : `d2 00 f3 0f 59 0d e0 79 db 00`
- 0x004dede3 [.text] mulss xmm1  (constante 0x00db79e0)  octets : `d2 00 f3 0f 59 0d e0 79 db 00`
- 0x0058c5c9 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x0058c5fa [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x0058c634 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x0058e6d0 [.text] movss xmm0  (constante 0x00db79e0)  octets : `41 78 f3 0f 10 05 e0 79 db 00`
- 0x005d3661 [.text] addss xmm0  (constante 0x00db79e0)  octets : `28 c2 f3 0f 58 05 e0 79 db 00`
- 0x005eb462 [.text] fld dword   (constante 0x00db79e0)  octets : `cc cc cc cc d9 05 e0 79 db 00`
- 0x005ed307 [.text] movss xmm0  (constante 0x00db79e0)  octets : `5e 00 f3 0f 10 05 e0 79 db 00`
- 0x006006b0 [.text] movss xmm0  (constante 0x00db79e0)  octets : `58 d0 f3 0f 10 05 e0 79 db 00`
- 0x0061cf63 [.text] mulss xmm1  (constante 0x00db79e0)  octets : `5e c8 f3 0f 59 0d e0 79 db 00`
- 0x00635422 [.text] maxss xmm0  (constante 0x00db79e0)  octets : `45 14 f3 0f 5f 05 e0 79 db 00`
- 0x006ad073 [.text] divss xmm0  (constante 0x00db79e0)  octets : `5e c8 f3 0f 5e 05 e0 79 db 00`
- 0x006ad682 [.text] divss xmm1  (constante 0x00db79e0)  octets : `5e c1 f3 0f 5e 0d e0 79 db 00`
- 0x006c296c [.text] movss xmm0  (constante 0x00db79e0)  octets : `d4 ff f3 0f 10 05 e0 79 db 00`
- 0x006c2bef [.text] movss xmm0  (constante 0x00db79e0)  octets : `8b cf f3 0f 10 05 e0 79 db 00`
- 0x006c35c4 [.text] addss xmm0  (constante 0x00db79e0)  octets : `5a c0 f3 0f 58 05 e0 79 db 00`
- 0x006ca8f0 [.text] addss xmm1  (constante 0x00db79e0)  octets : `ff ff f3 0f 58 0d e0 79 db 00`
- 0x006cd003 [.text] movss xmm2  (constante 0x00db79e0)  octets : `6a 08 f3 0f 10 15 e0 79 db 00`
- 0x006cd09d [.text] movss xmm2  (constante 0x00db79e0)  octets : `5a c2 f3 0f 10 15 e0 79 db 00`
- 0x006cd3f4 [.text] movss xmm2  (constante 0x00db79e0)  octets : `5a c2 f3 0f 10 15 e0 79 db 00`
- 0x006e2e6c [.text] mulss xmm0  (constante 0x00db79e0)  octets : `47 64 f3 0f 59 05 e0 79 db 00`
- 0x00707063 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `5a c0 f3 0f 59 05 e0 79 db 00`
- 0x007070a8 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `5a c0 f3 0f 59 05 e0 79 db 00`
- 0x007070d9 [.text] mulss xmm1  (constante 0x00db79e0)  octets : `5a c8 f3 0f 59 0d e0 79 db 00`
- 0x0070710a [.text] mulss xmm0  (constante 0x00db79e0)  octets : `24 24 f3 0f 59 05 e0 79 db 00`
- 0x00714912 [.text] fld dword   (constante 0x00db79e0)  octets : `00 cc cc cc d9 05 e0 79 db 00`
- 0x0071cc27 [.text] divss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5e 05 e0 79 db 00`
- 0x00724bd5 [.text] mulss xmm3  (constante 0x00db79e0)  octets : `ff ff f3 0f 59 1d e0 79 db 00`
- 0x00724caf [.text] mulss xmm1  (constante 0x00db79e0)  octets : `4d 90 f3 0f 59 0d e0 79 db 00`
- 0x0072b3da [.text] movss xmm0  (constante 0x00db79e0)  octets : `00 00 f3 0f 10 05 e0 79 db 00`
- 0x0073fe72 [.text] movss xmm2  (constante 0x00db79e0)  octets : `5a c2 f3 0f 10 15 e0 79 db 00`
- 0x00748630 [.text] movss xmm0  (constante 0x00db79e0)  octets : `76 21 f3 0f 10 05 e0 79 db 00`
- 0x00751bbe [.text] mulss xmm0  (constante 0x00db79e0)  octets : `ff ff f3 0f 59 05 e0 79 db 00`
- 0x00752900 [.text] movss xmm1  (constante 0x00db79e0)  octets : `47 40 f3 0f 10 0d e0 79 db 00`
- 0x00757ad7 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `57 c0 f3 0f 59 05 e0 79 db 00`
- 0x00757f65 [.text] mulss xmm3  (constante 0x00db79e0)  octets : `5c d9 f3 0f 59 1d e0 79 db 00`
- 0x00763528 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `e2 ff f3 0f 59 05 e0 79 db 00`
- 0x007665e6 [.text] movss xmm0  (constante 0x00db79e0)  octets : `ca ff f3 0f 10 05 e0 79 db 00`
- 0x00766623 [.text] movss xmm0  (constante 0x00db79e0)  octets : `ca ff f3 0f 10 05 e0 79 db 00`
- 0x0076f889 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `ec 08 f3 0f 59 05 e0 79 db 00`
- 0x0076fb61 [.text] mulss xmm0  (constante 0x00db79e0)  octets : `ec 08 f3 0f 59 05 e0 79 db 00`
- 0x007745aa [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x007745ee [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x007747d8 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x00774823 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x007748f3 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x00774924 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x00774a29 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x00774a87 [.text] subss xmm0  (constante 0x00db79e0)  octets : `db 00 f3 0f 5c 05 e0 79 db 00`
- 0x007b0928 [.text] addss xmm1  (constante 0x00db79e0)  octets : `db 00 f3 0f 58 0d e0 79 db 00`
- 0x007c7a2f [.text] movss xmm3  (constante 0x00db79e0)  octets : `00 00 f3 0f 10 1d e0 79 db 00`
- 0x007c7d6a [.text] movss xmm3  (constante 0x00db79e0)  octets : `5d e4 f3 0f 10 1d e0 79 db 00`
- 0x00805b89 [.text] movss xmm1  (constante 0x00db79e0)  octets : `57 d2 f3 0f 10 0d e0 79 db 00`
- 0x0080609f [.text] movss xmm1  (constante 0x00db79e0)  octets : `57 d2 f3 0f 10 0d e0 79 db 00`
- 0x00806609 [.text] movss xmm1  (constante 0x00db79e0)  octets : `57 d2 f3 0f 10 0d e0 79 db 00`
- ... 31 de plus

### 120 (copies en donnees : 0x00db79ec)
- 0x0045a799 [.text] divss xmm0  (constante 0x00db79ec)  octets : `76 16 f3 0f 5e 05 ec 79 db 00`
- 0x0060bf8a [.text] movss xmm2  (constante 0x00db79ec)  octets : `33 ff f3 0f 10 15 ec 79 db 00`
- 0x006297b2 [.text] subss xmm0  (constante 0x00db79ec)  octets : `45 d0 f3 0f 5c 05 ec 79 db 00`
- 0x006299d0 [.text] subss xmm7  (constante 0x00db79ec)  octets : `c4 04 f3 0f 5c 3d ec 79 db 00`
- 0x006760f5 [.text] divss xmm0  (constante 0x00db79ec)  octets : `5a c0 f3 0f 5e 05 ec 79 db 00`
- 0x00683e0c [.text] movss xmm2  (constante 0x00db79ec)  octets : `00 00 f3 0f 10 15 ec 79 db 00`
- 0x00683e3c [.text] divss xmm2  (constante 0x00db79ec)  octets : `57 c0 f3 0f 5e 15 ec 79 db 00`
- 0x0068a2fd [.text] movss xmm2  (constante 0x00db79ec)  octets : `00 00 f3 0f 10 15 ec 79 db 00`
- 0x0068a32a [.text] divss xmm2  (constante 0x00db79ec)  octets : `57 c0 f3 0f 5e 15 ec 79 db 00`
- 0x006fe1af [.text] addss xmm0  (constante 0x00db79ec)  octets : `28 c7 f3 0f 58 05 ec 79 db 00`
- 0x006fed11 [.text] minss xmm1  (constante 0x00db79ec)  octets : `5f c8 f3 0f 5d 0d ec 79 db 00`
- 0x00701bd0 [.text] addss xmm0  (constante 0x00db79ec)  octets : `db 00 f3 0f 58 05 ec 79 db 00`
- 0x0071ceb5 [.text] divss xmm0  (constante 0x00db79ec)  octets : `00 00 f3 0f 5e 05 ec 79 db 00`
- 0x0071ddd0 [.text] movss xmm5  (constante 0x00db79ec)  octets : `db 00 f3 0f 10 2d ec 79 db 00`
- 0x0071de41 [.text] divss xmm5  (constante 0x00db79ec)  octets : `db 00 f3 0f 5e 2d ec 79 db 00`
- 0x0075aee0 [.text] comiss xmm0  (constante 0x00db79ec)  octets : `03 00 00 0f 2f 05 ec 79 db 00`
- 0x007a87e1 [.text] divss xmm0  (constante 0x00db79ec)  octets : `ff ff f3 0f 5e 05 ec 79 db 00`
- 0x007ec0d8 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x007ec19c [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x007ec44d [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x007ec580 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x00803ed7 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x00803f9b [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x0080424c [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x00804351 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x0080cf72 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x0080d036 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x0080d2d8 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x0080d3db [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x008132e0 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x008133a4 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x00813655 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`
- 0x00813758 [.text] movss xmm1  (constante 0x00db79ec)  octets : `57 d2 f3 0f 10 0d ec 79 db 00`

### 20 (copies en donnees : 0x00db7960)
- 0x00488a1c [.text] mulss xmm1  (constante 0x00db7960)  octets : `00 00 f3 0f 59 0d 60 79 db 00`
- 0x00489a87 [.text] mulss xmm0  (constante 0x00db7960)  octets : `8b c7 f3 0f 59 05 60 79 db 00`
- 0x004ddc1c [.text] movss xmm3  (constante 0x00db7960)  octets : `00 00 f3 0f 10 1d 60 79 db 00`
- 0x004dde2e [.text] movss xmm3  (constante 0x00db7960)  octets : `00 00 f3 0f 10 1d 60 79 db 00`
- 0x004ef5d6 [.text] mulss xmm0  (constante 0x00db7960)  octets : `28 cb f3 0f 59 05 60 79 db 00`
- 0x0058c0a1 [.text] mulss xmm0  (constante 0x00db7960)  octets : `5a c0 f3 0f 59 05 60 79 db 00`
- 0x005c8366 [.text] mulss xmm0  (constante 0x00db7960)  octets : `ff ff f3 0f 59 05 60 79 db 00`
- 0x005d3df7 [.text] subss xmm0  (constante 0x00db7960)  octets : `ff ff f3 0f 5c 05 60 79 db 00`
- 0x005de9b1 [.text] subss xmm1  (constante 0x00db7960)  octets : `04 40 f3 0f 5c 0d 60 79 db 00`
- 0x00600647 [.text] addss xmm0  (constante 0x00db7960)  octets : `db 00 f3 0f 58 05 60 79 db 00`
- 0x0061af3f [.text] mulss xmm0  (constante 0x00db7960)  octets : `ff ff f3 0f 59 05 60 79 db 00`
- 0x0061af7e [.text] mulss xmm0  (constante 0x00db7960)  octets : `ff ff f3 0f 59 05 60 79 db 00`
- 0x0061afb2 [.text] mulss xmm0  (constante 0x00db7960)  octets : `ff ff f3 0f 59 05 60 79 db 00`
- 0x0061afdf [.text] mulss xmm0  (constante 0x00db7960)  octets : `c7 08 f3 0f 59 05 60 79 db 00`
- 0x006d32fd [.text] movss xmm2  (constante 0x00db7960)  octets : `ff ff f3 0f 10 15 60 79 db 00`
- 0x006f76c0 [.text] addss xmm0  (constante 0x00db7960)  octets : `00 00 f3 0f 58 05 60 79 db 00`
- 0x006fa5ed [.text] mulss xmm2  (constante 0x00db7960)  octets : `28 c6 f3 0f 59 15 60 79 db 00`
- 0x006fe3eb [.text] movss xmm0  (constante 0x00db7960)  octets : `00 00 f3 0f 10 05 60 79 db 00`
- 0x00701bc8 [.text] mulss xmm0  (constante 0x00db7960)  octets : `ff 50 f3 0f 59 05 60 79 db 00`
- 0x0071cc01 [.text] subss xmm6  (constante 0x00db7960)  octets : `ff ff f3 0f 5c 35 60 79 db 00`
- 0x0072eb83 [.text] movss xmm2  (constante 0x00db7960)  octets : `5a c2 f3 0f 10 15 60 79 db 00`
- 0x0072edf6 [.text] movss xmm2  (constante 0x00db7960)  octets : `75 24 f3 0f 10 15 60 79 db 00`
- 0x0074ab9f [.text] movss xmm0  (constante 0x00db7960)  octets : `00 00 f3 0f 10 05 60 79 db 00`
- 0x0074d185 [.text] movss xmm0  (constante 0x00db7960)  octets : `ff ff f3 0f 10 05 60 79 db 00`
- 0x0074d250 [.text] movss xmm0  (constante 0x00db7960)  octets : `eb 9d f3 0f 10 05 60 79 db 00`
- 0x00761b3f [.text] mulss xmm0  (constante 0x00db7960)  octets : `10 00 f3 0f 59 05 60 79 db 00`
- 0x00764048 [.text] mulss xmm0  (constante 0x00db7960)  octets : `5a c0 f3 0f 59 05 60 79 db 00`
- 0x00784265 [.text] mulss xmm0  (constante 0x00db7960)  octets : `00 00 f3 0f 59 05 60 79 db 00`
- 0x008124c1 [.text] subss xmm0  (constante 0x00db7960)  octets : `5a c0 f3 0f 5c 05 60 79 db 00`
- 0x00869c88 [.text] movss xmm1  (constante 0x00db7960)  octets : `db 00 f3 0f 10 0d 60 79 db 00`
- 0x008f1016 [.text] minss xmm0  (constante 0x00db7960)  octets : `24 10 f3 0f 5d 05 60 79 db 00`
- 0x00a06428 [.text] movss xmm0  (constante 0x00db7960)  octets : `db 00 f3 0f 10 05 60 79 db 00`

### 70 (copies en donnees : 0x00d724b8, 0x00db79c8)
- 0x00488c7a [.text] mulss xmm0  (constante 0x00db79c8)  octets : `00 00 f3 0f 59 05 c8 79 db 00`
- 0x00616646 [.text] mulss xmm0  (constante 0x00db79c8)  octets : `24 3c f3 0f 59 05 c8 79 db 00`

### 23.5 (copies en donnees : aucune)

### -2.0 (copies en donnees : 0x00cec418, 0x00cedc44, 0x00cf0374, 0x00cf52e8, 0x00cf5320, 0x00cf5330)
- 0x00430d11 [.text] movss xmm0  (constante 0x00db7d38)  octets : `24 10 f3 0f 10 05 38 7d db 00`
- 0x00430e2f [.text] movss xmm0  (constante 0x00db7d38)  octets : `24 0c f3 0f 10 05 38 7d db 00`
- 0x00430f24 [.text] movss xmm0  (constante 0x00db7d38)  octets : `11 07 f3 0f 10 05 38 7d db 00`
- 0x004d6838 [.text] mulss xmm1  (constante 0x00db7d38)  octets : `4d f8 f3 0f 59 0d 38 7d db 00`
- 0x004d697f [.text] mulss xmm1  (constante 0x00db7d38)  octets : `28 d0 f3 0f 59 0d 38 7d db 00`
- 0x004d6a9f [.text] mulss xmm1  (constante 0x00db7d38)  octets : `28 d8 f3 0f 59 0d 38 7d db 00`
- 0x00599da8 [.text] op0F10(F2) xmm4  (constante 0x00db75f0)  octets : `db 00 f2 0f 10 25 f0 75 db 00`
- 0x00599db7 [.text] op0F10(F2) xmm2  (constante 0x00db7d18)  octets : `db 00 f2 0f 10 15 18 7d db 00`
- 0x00599dd4 [.text] movaps xmm3  (constante 0x00db8940)  octets : `04 00 00 0f 28 1d 40 89 db 00`
- 0x0059a670 [.text] movaps xmm3  (constante 0x00db8a00)  octets : `03 00 00 0f 28 1d 00 8a db 00`
- 0x0059a678 [.text] op0F10(F2) xmm4  (constante 0x00db7568)  octets : `db 00 f2 0f 10 25 68 75 db 00`
- 0x0059a687 [.text] op0F10(F2) xmm2  (constante 0x00db7d00)  octets : `db 00 f2 0f 10 15 00 7d db 00`
- 0x006c1e6f [.text] op0F59(F2) xmm0  (constante 0x00db75c0)  octets : `5a c0 f2 0f 59 05 c0 75 db 00`
- 0x006c2021 [.text] op0F59(F2) xmm0  (constante 0x00db75c0)  octets : `5a c0 f2 0f 59 05 c0 75 db 00`
- 0x006fe320 [.text] maxss xmm5  (constante 0x00db7d38)  octets : `c7 50 f3 0f 5f 2d 38 7d db 00`
- 0x008e08c4 [.text] mulss xmm0  (constante 0x00db7d38)  octets : `59 e8 f3 0f 59 05 38 7d db 00`
- 0x008e0a2e [.text] mulss xmm0  (constante 0x00db7d38)  octets : `59 e9 f3 0f 59 05 38 7d db 00`
- 0x008e0bd8 [.text] mulss xmm0  (constante 0x00db7d38)  octets : `28 c1 f3 0f 59 05 38 7d db 00`
- 0x008e0e60 [.text] mulss xmm1  (constante 0x00db7d38)  octets : `59 c1 f3 0f 59 0d 38 7d db 00`
- 0x008e109f [.text] mulss xmm1  (constante 0x00db7d38)  octets : `24 08 f3 0f 59 0d 38 7d db 00`
- 0x008ef971 [.text] mulss xmm0  (constante 0x00db7d38)  octets : `24 0c f3 0f 59 05 38 7d db 00`
- 0x008efb94 [.text] op0F10(F2) xmm0  (constante 0x00db7618)  octets : `35 00 f2 0f 10 05 18 76 db 00`
- 0x008f0e32 [.text] mulss xmm0  (constante 0x00db7d38)  octets : `28 c2 f3 0f 59 05 38 7d db 00`
- 0x008f1819 [.text] mulss xmm0  (constante 0x00db7d38)  octets : `24 30 f3 0f 59 05 38 7d db 00`
- 0x008f197a [.text] mulss xmm0  (constante 0x00db7d38)  octets : `28 c2 f3 0f 59 05 38 7d db 00`
- 0x008f1aae [.text] op0F10(F2) xmm0  (constante 0x00db75c8)  octets : `24 14 f2 0f 10 05 c8 75 db 00`
- 0x008f23bb [.text] mulss xmm0  (constante 0x00db7d38)  octets : `28 c2 f3 0f 59 05 38 7d db 00`
- 0x00a0cffa [.text] mulss xmm6  (constante 0x00db7d38)  octets : `28 f1 f3 0f 59 35 38 7d db 00`
- 0x00a0d0a9 [.text] mulss xmm5  (constante 0x00db7d38)  octets : `59 cd f3 0f 59 2d 38 7d db 00`
- 0x00a0d0e9 [.text] mulss xmm7  (constante 0x00db7d38)  octets : `28 c1 f3 0f 59 3d 38 7d db 00`
- 0x00a15c7c [.text] mulss xmm0  (constante 0x00db7d38)  octets : `58 c9 f3 0f 59 05 38 7d db 00`
- 0x00a19a4c [.text] mulss xmm6  (constante 0x00db7d38)  octets : `28 f1 f3 0f 59 35 38 7d db 00`
- 0x00a19afb [.text] mulss xmm5  (constante 0x00db7d38)  octets : `59 cd f3 0f 59 2d 38 7d db 00`
- 0x00a19b3b [.text] mulss xmm7  (constante 0x00db7d38)  octets : `28 c1 f3 0f 59 3d 38 7d db 00`
- 0x00ae7f37 [.text] mulss xmm5  (constante 0x00db7d38)  octets : `00 00 f3 0f 59 2d 38 7d db 00`
- 0x00c0fa6c [.text] mulss xmm6  (constante 0x00db7d38)  octets : `28 f7 f3 0f 59 35 38 7d db 00`
- 0x00c0fb3c [.text] mulss xmm7  (constante 0x00db7d38)  octets : `59 c1 f3 0f 59 3d 38 7d db 00`
- 0x00c0fb63 [.text] mulss xmm3  (constante 0x00db7d38)  octets : `24 58 f3 0f 59 1d 38 7d db 00`
- 0x00c20d52 [.text] mulss xmm0  (constante 0x00db7d38)  octets : `28 c2 f3 0f 59 05 38 7d db 00`
- 0x00c41628 [.text] ?   (constante 0x00e59120)  octets : `30 de c4 dd 04 f5 20 91 e5 00`
- 0x00c59c7d [.text] ?   (constante 0x00cec418)  octets : `de e1 d9 c9 dc 0d 18 c4 ce 00`

## 3. Vecteurs de 4 nombres (atterrissage)

### vec(1000,-600,0,0) : copies aucune

### vec(-1000,600,0,0) : copies aucune

### vec(1000,1800,0,0) [deja patche ?] : copies aucune

## 4. Chaines qui existent dans tous les builds

| chaine | adresse(s) | nombre de references (code + donnees) |
|---|---|---|
| `lift_constraint` | 0x00d22e90 | 2 |
| `load_lift_lower` | 0x00d22598 | 2 |
| `runway_start` | 0x00d70f60 | 2 |
| `runway_end` | 0x00d70f70 | 2 |
| `lift_lower` | 0x00d22550 | 1 |
| `lift_upper` | 0x00d22564 | 1 |
| `hanger_center` | 0x00d220a4 | 3 |
| `vehicle_ai_wing_cruise_speed` | 0x00d2e8dc | 1 |
| `docking_queue` | 0x00d70e1c | 4 |
| `runway_state` | 0x00d70d1c | 4 |
| `vehicle_id_crane` | 0x00d223a8 | 1 |
| `crane_instructions` | 0x00d2237c | 2 |
| `docking_join_time` | 0x00d22520 | 1 |
| `docking_manager_air` | 0x00d22da8 | 2 |
| `c_vehicle_server_carrier` | ABSENTE | 0 |

- `lift_constraint` utilisee en : 0x00705543 (.text), 0x00713038 (.text)
- `load_lift_lower` utilisee en : 0x006fca83 (.text), 0x00700b80 (.text)
- `runway_start` utilisee en : 0x00627c96 (.text), 0x006fc294 (.text)
- `runway_end` utilisee en : 0x00627d0c (.text), 0x006fc30e (.text)
- `lift_lower` utilisee en : 0x006fc1a3 (.text)
- `lift_upper` utilisee en : 0x006fc21a (.text)
- `hanger_center` utilisee en : 0x006f59e9 (.text), 0x006fc129 (.text), 0x00705641 (.text)
- `vehicle_ai_wing_cruise_speed` utilisee en : 0x00869401 (.text)
- `docking_queue` utilisee en : 0x00626fa9 (.text), 0x006f8ab5 (.text), 0x008ba9be (.text), 0x008baa67 (.text)
- `runway_state` utilisee en : 0x00626f6b (.text), 0x006fbd4a (.text), 0x006fbd7c (.text), 0x006fbdbc (.text)
- `vehicle_id_crane` utilisee en : 0x006fbeaa (.text)
- `crane_instructions` utilisee en : 0x008ba7a0 (.text), 0x008ba83c (.text)
- `docking_join_time` utilisee en : 0x006fc038 (.text)
- `docking_manager_air` utilisee en : 0x007049c3 (.text), 0x007049e1 (.text)

## 5. Groupes (voisinage dans le code)

### Plateforme : 0,025 et 0,001
Ancre 0.025 (55 lectures), voisins ['0.001'] dans +/-300 octets : **1 ancres avec tous les voisins**.
- 0.025@0x00705c14 movss | 0.001@0x00705c53 comiss

### Plateforme : -0,025 et 0,001
Ancre -0.025 (2 lectures), voisins ['0.001'] dans +/-300 octets : **1 ancres avec tous les voisins**.
- -0.025@0x00705c3e maxss | 0.001@0x00705c53 comiss

### Roulage : 2,5 et 0,05 (7 paires attendues)
Ancre 2.5 (17 lectures), voisins ['0.05'] dans +/-120 octets : **6 ancres avec tous les voisins**.
- 2.5@0x006f9811 movss | 0.05@0x006f9845 addss
- 2.5@0x006fb2e9 movss | 0.05@0x006fb2ce addss
- 2.5@0x006fcbb2 movss | 0.05@0x006fcbaa addss
- 2.5@0x006fce56 movss | 0.05@0x006fce4e addss
- 2.5@0x006fd8f0 movss | 0.05@0x006fd8d5 addss
- 2.5@0x006fddbd movss | 0.05@0x006fddb5 movss

### Grue : 1/6, 1/30, 11, 12
Ancre 1/6 (8 lectures), voisins ['1/30', '11.0', '12.0'] dans +/-900 octets : **2 ancres avec tous les voisins**.
- 1/6@0x00700f26 movss | 1/30@0x00700f9a movss | 11.0@0x0070117c movss | 12.0@0x00701136 movss
- 1/6@0x00701035 movss | 1/30@0x007010a6 movss | 11.0@0x0070117c movss | 12.0@0x00701136 movss

### Grue : -1/6, -1/30
Ancre -1/6 (3 lectures), voisins ['-1/30'] dans +/-900 octets : **2 ancres avec tous les voisins**.
- -1/6@0x00700f31 movss | -1/30@0x00700f82 movss
- -1/6@0x00701040 movss | -1/30@0x00701083 movss

### Rotation grue 0,04 pres de 1/6
Ancre 0.04 (14 lectures), voisins ['1/6'] dans +/-900 octets : **1 ancres avec tous les voisins**.
- 0.04@0x00701219 movss | 1/6@0x00701035 movss

### Vitesse IA : 144, 48, 72
Ancre 144 (1 lectures), voisins ['48', '72'] dans +/-500 octets : **1 ancres avec tous les voisins**.
- 144@0x0071a0cb movss | 48@0x0071a0d6 maxss | 72@0x0071a0ec maxss

### Atterrissage : 600 pres des vecteurs et de 1200 / 80
Ancre 600 (9 lectures), voisins ['1200', '80'] dans +/-3000 octets : **0 ancres avec tous les voisins**.

### Energie : immediats 0,8 / 0,6 / 0,4 / 0,2 dans le code
- 0.8 : 15 occurrences en immediat
- 0.6 : 7 occurrences en immediat
- 0.4 : 20 occurrences en immediat
- 0.2 : 60 occurrences en immediat
Groupes {0,8 ; 0,6 ; 0,4 ; 0,2} a moins de 400 octets : **6**
- 0,4 en 0x006ea0a1 (octets autour : `c7 47 08 cd cc cc 3e`) ; 0,8 en 0x006e9f6f ; 0,6 en 0x006ea001 ; 0,2 en 0x006e9f33
- 0,4 en 0x008f0718 (octets autour : `44 24 20 cd cc cc 3e`) ; 0,8 en 0x008f06a8, 0x008f0748, 0x008f0778, 0x008f07c0 ; 0,6 en 0x008f0740, 0x008f0858 ; 0,2 en 0x008f0588, 0x008f0618, 0x008f0620, 0x008f0698, 0x008f07b0, 0x008f08a8
- 0,4 en 0x008f0830 (octets autour : `44 24 20 cd cc cc 3e`) ; 0,8 en 0x008f06a8, 0x008f0748, 0x008f0778, 0x008f07c0, 0x008f0957, 0x008f099f ; 0,6 en 0x008f0740, 0x008f0858, 0x008f093f ; 0,2 en 0x008f07b0, 0x008f08a8, 0x008f098f
- 0,4 en 0x008f0917 (octets autour : `44 24 20 cd cc cc 3e`) ; 0,8 en 0x008f07c0, 0x008f0957, 0x008f099f ; 0,6 en 0x008f0858, 0x008f093f, 0x008f0a26 ; 0,2 en 0x008f07b0, 0x008f08a8, 0x008f098f, 0x008f0a76
- 0,4 en 0x008f09fe (octets autour : `44 24 20 cd cc cc 3e`) ; 0,8 en 0x008f0957, 0x008f099f ; 0,6 en 0x008f093f, 0x008f0a26 ; 0,2 en 0x008f08a8, 0x008f098f, 0x008f0a76, 0x008f0af9
- 0,4 en 0x008f0af1 (octets autour : `44 24 20 cd cc cc 3e`) ; 0,8 en 0x008f099f ; 0,6 en 0x008f0a26 ; 0,2 en 0x008f098f, 0x008f0a76, 0x008f0af9

