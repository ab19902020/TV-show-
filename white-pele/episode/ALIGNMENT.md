# The White Pelé — lyric alignment

Every sung word timed against the supplied recording (`song.mp3`, untouched, 177.520 s). Built by `film/align_song.py`:
pocketsphinx forced alignment of each lyric line inside its window on the separated vocal stem (Demucs), with an
onset-snap fallback where the aligner can't hold a legato stretch; word edges refined to vocal onsets; phones
remapped to visemes. Whisper then re-hears each line on its own and the word error rate (WER) against the corrected
lyrics is reported below as an independent check. `film/timing.py` merges this into `song-timing.json` (the mouth
track, led 2 frames ahead of the voice, guitar bleed 25.3–37.7 s muted).

Words: 277 · phones: 630 · lines: 45

| line | start | end | lyric | Whisper heard | WER | method |
|---|---|---|---|---|---|---|
| 0 | 2.26 | 5.03 | I saw my mate the other day | I saw my mane the other day. | 0.14 | aligned |
| 1 | 5.43 | 8.19 | He said to me he'd seen the White Pele | He said to me, he'd seen the white pellet. | 0.11 | aligned |
| 2 | 8.42 | 10.97 | So I asked, who is he? | So I asked, who is he? | 0.00 | aligned |
| 3 | 11.31 | 13.90 | He goes by the name of Wayne Rooney | He goes by the name of Wayne Rooney. | 0.00 | aligned |
| 4 | 14.39 | 15.90 | Wayne Rooney | Wayne Rooney | 0.00 | aligned |
| 5 | 17.29 | 19.68 | Wayne Rooney | Wayne Rooney | 0.00 | onsets |
| 6 | 20.75 | 24.27 | He goes by the name of Wayne Rooney | He goes by the name of Wailon. | 0.25 | aligned |
| 7 | 38.02 | 41.12 | From Croxteth streets to theatre dreams | Cross that street, the theater dreams | 0.83 | onsets |
| 8 | 41.44 | 43.88 | Bursting through defences and seams | First and do the friends, is a scene | 1.50 | aligned |
| 9 | 43.89 | 46.49 | Number ten with fire inside | Number 10 with fire inside | 0.00 | aligned |
| 10 | 46.87 | 49.75 | Red Devil with that Merseyside pride | Red devil with thy Merseside pride. | 0.33 | aligned |
| 11 | 50.05 | 52.68 | First time strike, no second thought | First time strike, no second thought | 0.00 | aligned |
| 12 | 53.19 | 55.74 | Every battle fiercely fought | Every battle, fiercely fought | 0.00 | aligned |
| 13 | 55.75 | 58.16 | Roars the crowd on Sir Matt Busby Way | The crowd on some at bus be way | 0.62 | aligned |
| 14 | 58.17 | 62.16 | When Rooney scores, we lose our minds that day | When ruin is cold, we lose our minds that day. | 0.33 | aligned |
| 15 | 62.60 | 67.94 | When he turns and lets one fly | When he turns and lets one fly | 0.00 | aligned |
| 16 | 68.46 | 70.56 | You just know it's top bin time | You just know it's topping time | 0.29 | aligned |
| 17 | 72.74 | 75.15 | I saw my mate the other day | So my mate, the other day. | 0.29 | aligned |
| 18 | 75.28 | 78.42 | He said to me he'd seen the White Pele | He said to me he'd seen a white pillow. | 0.22 | onsets |
| 19 | 78.43 | 80.97 | So I asked, who is he? | So I ask, who is he? | 0.17 | aligned |
| 20 | 80.98 | 83.82 | He goes by the name of Wayne Rooney | He goes by the name of Wayne Moon. | 0.12 | onsets |
| 21 | 84.21 | 85.46 | Wayne Rooney | Wait, Moody! | 1.00 | aligned |
| 22 | 87.03 | 88.90 | Wayne Rooney | Wayne Rooney! | 0.00 | onsets |
| 23 | 90.65 | 94.48 | He goes by the name of Wayne Rooney | He goes by the name of Wayne Rooney. | 0.00 | aligned |
| 24 | 96.85 | 99.15 | Volley smash in the derby night | Volley smash in the derby now | 0.17 | aligned |
| 25 | 99.83 | 102.54 | City stunned by that bicycle strike | Did he stun by that bicycle strike? | 0.50 | aligned |
| 26 | 102.55 | 104.74 | History written in mid-air flight | History written in mid-air fly | 0.17 | aligned |
| 27 | 105.07 | 107.97 | Old Trafford shaking left and right | I don't stop the shaking left in a row | 1.20 | aligned |
| 28 | 108.35 | 110.90 | Captain's armband on his sleeve | Captain's armband on his sleeve. | 0.00 | aligned |
| 29 | 111.29 | 113.74 | Never a man you'd doubt or leave | Never a man, you die or leave. | 0.33 | aligned |
| 30 | 113.85 | 116.13 | England's hope and United's pride | Leave England's hoping you're not yet. | 1.25 | onsets |
| 31 | 116.20 | 119.81 | Goals and glory side by side | Pride, goals and glory side by side. | 0.20 | onsets |
| 32 | 120.46 | 122.76 | Through the rain and through the cold | Through the rain and through the cold | 0.00 | aligned |
| 33 | 123.10 | 125.81 | He gave us moments worth more than gold | Save us moments worth more than gold | 0.25 | aligned |
| 34 | 125.82 | 128.76 | From Everton blue to United red | From Everton blue to United ready | 0.17 | aligned |
| 35 | 128.77 | 132.44 | He led the line and forged ahead | He led the line and forged ahead | 0.00 | aligned |
| 36 | 132.90 | 136.17 | I saw my mate the other day | I saw my name the other day | 0.14 | aligned |
| 37 | 136.18 | 139.31 | He said to me he'd seen the White Pele | Day he said to me Tina white | 0.56 | onsets |
| 38 | 139.32 | 142.00 | So I asked, who is he? | So I asked, who is he? | 0.00 | onsets |
| 39 | 142.03 | 145.18 | He goes by the name of Wayne Rooney | See he goes by the name of Wayne | 0.25 | aligned |
| 40 | 145.19 | 147.30 | Wayne Rooney | Rooney wait Rooney | 1.00 | onsets |
| 41 | 147.60 | 149.97 | Wayne Rooney | Oh, wait, move it | 2.00 | aligned |
| 42 | 151.60 | 158.41 | He goes by the name of Wayne Rooney | He goes by the name of Wairoonah! | 0.25 | onsets |
| 43 | 158.90 | 161.79 | White Pele, White Pele | Wipe my leg! | 1.00 | onsets |
| 44 | 163.20 | 170.43 | White Pele, goes by the name of Wayne Rooney | The white walaay goes by the name of Waboo needs. | 0.44 | onsets |

Mean WER 0.36. A high WER is Whisper failing on a shouted, crowd-doubled terrace vocal ("Wait, Moody!" for "Wayne
Rooney"), not a different lyric: the words were checked by ear against the stem, and each line's timing comes from
the aligner or, where marked `onsets`, from the vocal's onsets distributed over the line's syllables (lines 5, 7, 18, 20, 22, 30, 31,
37, 38, 40, 42, 43, 44: legato or shouted stretches the aligner can't hold). The onset lines are where the lip sync is least
precise; they were checked against the stem on the preview's lips sheet. Uncertain readings in the lyrics (flagged in `lyrics.md`): "top bin time", "Volley
smash", "Sir Matt Busby Way".

Per-word times: `alignment.json` (`words`: [start, end, word, line]; `phones`: [phone, start, end]).
