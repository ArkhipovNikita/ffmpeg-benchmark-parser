# FFmpeg benchmark parser

Parse ffmpeg benchmark output and export to CSV.

Get input from ffmpeg command directly using pipes
```
ffmpeg -benchmark ... | python3 parse_ffmpeg_benchmark.py --csv_file bench.csv
```

Get input from pre-save file with ffmpeg benchmakrk output
```
python3 parse_ffmpeg_benchmark.py --benchmark_file bench.txt --csv_file bench.csv
```
