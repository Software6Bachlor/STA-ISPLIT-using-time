import argparse
import sys

from benchmarks.scalingChain import scalingChain
from benchmarks.scalingLong import scalingLong
from benchmarks.fixedTimeChain import fixedTimeChain
from benchmarks.fixedTimeLong import fixedTimeLong
from benchmarks.fixedTimeManufacturing import fixedTimeManufacturing
from benchmarks.fixedRunsChain import fixedRunsChain
from benchmarks.fixedRunsLong import fixedRunsLong
from benchmarks.fixedRunsManufacturing import fixedRunsManufacturing
from benchmarks.groundTruthLong import groundTruthLong
from benchmarks.groundTruthManufacturing import groundTruthManufacturing

def main():
	# Parse and validate command-line arguments
	memoryMb =2000
	ifTimeLimit = 3600

	#scalingChain(memoryMb, ifTimeLimit)
	#scalingLong(memoryMb, ifTimeLimit)
	#fixedTimeChain(memoryMb, ifTimeLimit)
	#fixedTimeLong(memoryMb, ifTimeLimit)
	#fixedTimeManufacturing(memoryMb, ifTimeLimit)
	groundTruthLong(memoryMb, ifTimeLimit)
	groundTruthManufacturing(memoryMb, ifTimeLimit)


	#fixedRunsChain(memoryMb, ifTimeLimit)
	#fixedRunsLong(memoryMb, ifTimeLimit)
	#fixedRunsManufacturing(memoryMb, ifTimeLimit)



def parseCliArgs(args: list[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(add_help=True)
	parser.add_argument("--memoryMb", dest="memoryMb", type=int, required=True)
	parser.add_argument("--ifTimeLimit", dest="ifTimeLimit", type=float)
	parser.add_argument("--resultsDir", type=str, default="/results", help="Directory where JSON results are saved")

	return parser.parse_args(args[1:])


def parseMemoryArg(parsedArgs: argparse.Namespace) -> int:
	memoryMb = parsedArgs.memoryMb
	if memoryMb <= 0:
		print("Invalid memory argument. Please provide a positive integer in MB.")
		raise SystemExit(1)

	return memoryMb

def parseIfTimeLimitArg(parsedArgs: argparse.Namespace) -> float | None:
	ifTimeLimit = parsedArgs.ifTimeLimit
	if ifTimeLimit is not None and ifTimeLimit <= 0:
		print("Invalid time limit. Please provide a positive number for --ifTimeLimit.")
		raise SystemExit(1)

	return ifTimeLimit




if __name__ == "__main__":
	main()
