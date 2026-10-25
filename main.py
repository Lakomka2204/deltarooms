#!/usr/bin/env python3
import argparse
import os
import subprocess
from pathlib import Path
import logging
import re
import json
from functools import cache
import csv

arg0_re = re.compile(r"arg0 == (\d+)")
ch1_re = re.compile(r"scr_84_get_lang_string\(\"(.+)\"\)")
ch_name_re = re.compile(r"stringset(?:sub)?loc\(\"(.+)\",(?:.*)\)")
idsarr_re = re.compile(r"scr_room\(([\w_]+), (\d+)")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert DELTARUNE chapters data.win to room list",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logs")
    parser.add_argument(
        "-d", "--directory",
        required=True,
        help="Game root folder (with DELTARUNE.exe)",
    )
    parser.add_argument(
        "-e", "--executable",
        required=True,
        help="Path to the UndertaleModCli.exe (Not the GUI version)",
    )
    return parser.parse_args()

@cache
def _load_lang_file(json_path: Path) -> dict:
    with open(json_path,"r",encoding="utf-8") as f:
        return json.load(f)
    
def get_84_localized(data: Path, key: str) -> str:
    return _load_lang_file(data.parent/"lang"/"lang_en.json")[key]
    
def neighbors(lines, i, before=2, after=2):
    lo, hi = max(0, i - before), min(len(lines), i + after + 1)
    return "\n".join(
        f"{'>>' if j == i else '  '} {j+1:5d}: {lines[j]}" for j in range(lo, hi)
    )

def run_script(executable: Path, data: Path,script: Path) -> str:
    cmd = [
        str(executable),
        "load",
        str(data),
        "-s",
        str(script)
    ]
    process = subprocess.run(cmd,
        text=True,
        capture_output=True,
    )
    return str(process.stdout)
REPLACER = "~1"
def process_scr_roomname(data:Path,rawdata:str) -> dict[int, str]:
    l = logging.getLogger("process_scr_roomname")
    room_data = {-1: ""}
    current_id = -1
    lines =rawdata.splitlines()
    for i, line in enumerate(lines):
        l.debug(f"processing {line}")
        if REPLACER in line:
            l.debug(f"replacing {REPLACER} with '{room_data[-1]}'")
            line = line.replace(REPLACER,room_data[-1])
        arg0_match = arg0_re.search(line)
        if arg0_match:
            l.debug("arg0_match")
            current_id = int(arg0_match.group(1))
            continue
        ch1_match = ch1_re.search(line)
        if ch1_match:
            l.debug("ch1_match")
            if current_id == -1:
                l.warning(f"warn no current id while at ch1 84 str\n{neighbors(lines,i)}")
                continue
            current_key = ch1_match.group(1)
            room_name = get_84_localized(data=data,key=current_key)
            if room_name is not None:
                room_data[current_id] = room_name
                current_id = -1
        ch_name_match = ch_name_re.search(line)
        if ch_name_match:
            l.debug("ch_name_watch")
            room_name = ch_name_match.group(1)
            if room_name is not None:
                room_data[current_id] = room_name
                current_id = -1
    room_data.pop(-1,None)
    return room_data

def process_scr_room_list(rawdata: str)-> dict:
    l = logging.getLogger("process_scr_room_list")
    lines = rawdata.splitlines()
    line = next((line for line in lines if "var idsarr =" in line), None)
    rooms = idsarr_re.finditer(line)
    room_map = {
        m.group(1): m.group(2)
        for m in rooms
    }
    return room_map

def main():
    l = logging.getLogger()
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    directory = Path(args.directory).resolve()
    executable = Path(args.executable).resolve()
    room_script = Path("Script.csx").resolve()
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError("-d is not a directory")
    if not executable.exists() or not executable.is_file():
        raise FileNotFoundError("-e is not a file")
    if os.name == "nt" and executable.suffix.lower() not in (".exe", ".bat", ".cmd", ".com"):
        raise FileNotFoundError("-e is not EXE file")
    datas = [p for p in directory.rglob("data.win") if p.is_file() and p.parent != directory]
    result = {}
    for data in datas:
        try:
            l.info(f"Loading {data.relative_to(directory)}")
            chapter_data_raw = run_script( 
                executable=executable,
                data=data,
                script=room_script
            )
            json_start = min(
                (i for i in (chapter_data_raw.find("{"),chapter_data_raw.find("[")) if i != -1),
                default=-1
            )
            if json_start == -1:
                l.warning("Process did not return JSON to stdout, did not found starting json chars")

            chapter_data = json.loads(chapter_data_raw[json_start:])
            l.debug(f"rooms (gonna be reversed): {chapter_data["rooms"]}")
            
            room_data = process_scr_roomname(data,chapter_data["scr_roomname"])
            global_room_data = process_scr_room_list(chapter_data["scr_get_room_by_id"])
            l.debug(f"room_data: {room_data}")
            l.debug(f"global_room_data: {global_room_data}")
            room_ids = {name: int(idx) for idx, name in chapter_data["rooms"].items()}
            loaded = 0
            for room_name, global_id in global_room_data.items():
                l.debug(f"Current element: {room_name}: {global_id}")
                local_id = room_ids.get(room_name,None)
                l.debug(f"local_id {local_id}")
                if local_id is None:
                    continue
                cool_name = room_data.get(local_id,None)
                if cool_name is None:
                    continue
                if result.get(global_id) is not None:
                    l.warning(f"Result already has entry with id {global_id}!!")
                result[global_id] = (local_id,room_name,cool_name)
                loaded += 1
                pass
            l.info(f"Loaded {loaded} rooms")
        except Exception as e:
            l.error("Error",exc_info=e)
    l.info(f"Retrieved total {len(result)} rooms")
    rooms_csv = Path("rooms.csv").resolve()
    with open(rooms_csv,"w",encoding="utf-8",newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["id","localid","gmsname","name"])
        wr.writerows([key, *value] for key, value in result.items())
    l.info(f"Wrote to {str(rooms_csv)}")
    pass


if __name__ == "__main__":
    main()