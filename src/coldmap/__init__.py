import argparse
from pathlib import Path
import shutil
from typing import Tuple

import matplotlib.pyplot as plt
import july

AUDIO_SUFFIX = [
    "mp3",
    "flac",
    "wav",
    "ogg",
    "m4a",
    "wma",
    "aac",
]

def is_audio(filename: str) -> bool:
    for ext in AUDIO_SUFFIX:
        if filename.lower().endswith('.'+ext):
            return True
    
    return False

def get_args():
    parser = argparse.ArgumentParser()
    mux_group = parser.add_mutually_exclusive_group(required=True)
    mux_group.add_argument("--src", type=str, help="Audio files directory to scan")
    mux_group.add_argument("--txt", type=str, help="filelist.txt")
    parser.add_argument("--out", type=str, help="Output directory", default="out")
    parser.add_argument("--prune", action="store_true", help="Prune output directory before processing")
    
    return parser.parse_args()

def iter_files(path: Path, recursive: bool = True):
    for item in path.iterdir():
        if item.is_dir():
            if recursive:
                yield from iter_files(item)
            else:
                continue
        else:
            yield item.name, item

def parse_datetime(filename: str) -> Tuple[str, str]:
    digits = [c for c in filename if c.isdigit()]
    digits = "".join(digits)

    if not len(digits) >= 12:
        raise ValueError(f"Filename {filename} should have at least 12 digits")

    year, month, day = digits[:4], digits[4:6], digits[6:8]
    hour, minute = digits[8:10], digits[10:12]

    return (f"{year}-{month}-{day}", f"{hour}:{minute}")

def from_txt(path: str):
    with open(path) as fp:
        for line in fp:
            f = Path(line.strip())
            yield f.name, f
    

def main():
    args = get_args()
    output_dir = Path(args.out)
    if args.prune:
        shutil.rmtree(output_dir, ignore_errors=True)

    output_dir.mkdir(exist_ok=True)

    dates: dict[str, int] = {}
    seencheck = set()

    for filename, _ in (iter_files(Path(args.src)) if args.src else from_txt(args.txt)):
        if not is_audio(filename):
            continue

        try:
            date, time = parse_datetime(filename)
        except ValueError as e:
            print(f"Skipping {filename}: {e}")
            continue

        if date+time in seencheck:
            # print(f"Skipping {filename}: dup")
            continue

        seencheck.add(date+time)

        dates[date] = dates.get(date, 0) + 1

    dates_listed = sorted(dates.items())

    per_year_dates = {}
    for date, count in dates_listed:
        year, _, _ = date.split("-")
        per_year_dates.setdefault(year, []).append((date, count))

    biggest_year = "0000"
    for year, year_dates in per_year_dates.items():
        if year > biggest_year:
            biggest_year = year

        print(f"Generating {year}.png")
        assert len([date for (date, _) in year_dates]) == len(set([date for (date, _) in year_dates]))
        july.heatmap(dates=[date for (date, _) in year_dates], data=[float(count) for _, count in year_dates],
                     title='Records', cmap="github", colorbar=True, month_grid=True)
        with open(output_dir / f"{year}.png", "wb") as f:
            plt.savefig(f)

    if year != "0000":
        shutil.copy(output_dir / f"{biggest_year}.png", output_dir / "latest.png")

if __name__ == "__main__":
    main()