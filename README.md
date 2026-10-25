# Deltarooms
Convert DELTARUNE's `data.win` to a nice CSV list of Rooms According to their global ID's.
## Usage
```
$ python main.py -h
Convert DELTARUNE chapters data.win to room list

options:
  -h, --help            show this help message and exit
  -v, --verbose         debug logs
  -d, --directory DIRECTORY
                        Game root folder (with DELTARUNE.exe)
  -e, --executable EXECUTABLE
                        Path to the UndertaleModCli.exe (Not the GUI version)
```
## Requirements
1. [UndertaleModCli](https://github.com/UnderminersTeam/UndertaleModTool/releases)
2. DELTARUNE
## Output
You will get `rooms.csv` file with list of rooms.

### Example output
```csv
id,localid,gmsname,name
10283,2,room_krisroom,Kris's Room
10316,35,room_dark1a,??????
10321,40,room_dark_eyepuzzle,Eye Puzzle
10326,45,room_castle_town,Castle Town
```
## Explanation

DELTARUNE uses GMS asset ids for room naming and global handmade ids for it's saves. (`filech1_2`, etc...)
So i've made this script to easily convert unreadable global room ids to nice readable and seen in game room names.
There is a similar [project](https://github.com/portaldash/deltarooms) to this which just converts local and global ids to gms room names. (`room_krisroom`)
But i've decided to go further than that. And made this tool.
## Note
Regarding Chapter 1: script also reads JSON `lang/lang_en.json` to retrieve room names because chapter 1 has a different system.
## License
[MIT License](https://github.com/Lakomka2204/deltarooms?tab=MIT-1-ov-file)