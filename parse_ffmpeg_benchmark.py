import argparse
import contextlib
import csv
import dataclasses as dc
import json
import logging
import os.path
import re
import sys
import typing as tp

logger = logging.getLogger()

FIRST_ROW_PATTERN = re.compile(r'bench: utime=([\d\.]+)s stime=([\d\.]+)s rtime=([\d\.]+)s')
SECOND_ROW_PATTERN = re.compile(r'bench: maxrss=(\d+)')


@dc.dataclass
class FFmpegBenchmark:
	utime: float
	stime: float
	rtime: float
	maxrss: int


def parse_ffmpeg_benchmark(lines: list[str]) -> FFmpegBenchmark:
	if len(lines) != 2:
		raise ValueError('Expected 2 lines of ffmpeg benchmark, got %d', len(lines))

	match = FIRST_ROW_PATTERN.search(lines[0])
	utime, stime, rtime = match.groups()

	match = SECOND_ROW_PATTERN.search(lines[1])
	maxrss = match.groups()[0]

	return FFmpegBenchmark(
		utime=float(utime),
		stime=float(stime),
		rtime=float(rtime),
		maxrss=int(maxrss)
	)


def parse_ffmpeg_benchmark_lines(lines: tp.Iterable[str]) -> tp.Generator[FFmpegBenchmark, None, None]:
	buff = [None, None]
	cur_idx = 0

	for line in lines:
		buff[cur_idx] = line
		cur_idx = (cur_idx + 1) % 2

		if cur_idx == 0:
			benchmark = parse_ffmpeg_benchmark(buff)
			yield benchmark

	if cur_idx != 0:
		logger.warning('Unprocessed lines left: "%s"', ', '.join(buff))


def strip_newline(s: str) -> str:
	return s.strip(' \n')


def main(benchmark_filename: str | None, csv_filename: str) -> None:
	exit_stack = contextlib.ExitStack()

	if benchmark_filename is None:
		benchmark_input = sys.stdin
	else:
		benchmark_file = open(benchmark_filename, 'r')
		exit_stack.enter_context(benchmark_file)
		benchmark_input = benchmark_file

	benchmark_input = filter(bool, map(strip_newline, benchmark_input))
	benchmark_generator = parse_ffmpeg_benchmark_lines(benchmark_input)

	with open(csv_filename, 'w', newline='') as csvfile:
		benchmark_writer = csv.writer(csvfile, delimiter=',')

		column_names = ('utime', 'stime', 'rtime', 'maxrss')
		benchmark_writer.writerow(column_names)

		for benchmark in benchmark_generator:
			data = json.loads(json.dumps(dc.asdict(benchmark)))
			row = [data[column_name] for column_name in column_names]
			benchmark_writer.writerow(row)

	exit_stack.close()


def exising_filename(mode: str) -> tp.Callable[[str], str]:
	def wrapped(file: str) -> str:
		if not os.path.exists(file):
			raise argparse.ArgumentTypeError('File does not exist')

		if 'r' in mode and not os.access(file, os.R_OK):
			raise argparse.ArgumentTypeError('File cannot be read')

		if 'w' in mode and not os.access(file, os.W_OK):
			raise argparse.ArgumentTypeError('File cannot be written')

		return file

	return wrapped


def cli():
	parser = argparse.ArgumentParser()
	parser.add_argument('--benchmark_file', type=exising_filename('r'), required=False)
	parser.add_argument('--csv_file', type=str, required=True)

	args = parser.parse_args()
	main(args.benchmark_file, args.csv_file)


if __name__ == '__main__':
	cli()
