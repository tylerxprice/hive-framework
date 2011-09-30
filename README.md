# Hive-Framework

This is framework for running a game of Hive between two bots.

## Developers

Requires:

 * Python 2.7

To run the framework:

shell> python framework.py [-h] [--white WHITE] [--black BLACK] [--times TIMES] [--moves MOVES] [--expansions EXPANSIONS]
optional arguments:
  -h, --help                show this help message and exit
  --white WHITE             The file name of the bot to play white
  --black BLACK             The file name of the bot to play black
  --times TIMES             Game Time (ms),White Time Used (ms),Black Time Used(ms)
  --moves MOVES             List of moves in the boardspace.net move notation (e.g., "1. wA1, 2. bG1 -wA1")
  --expansions EXPANSIONS   String of expansions pieces (e.g., "LM" or "L" or "M")

## Bots

The bots that use this framework to run should accept all the same times, moves, and expansions arguments as the framework does.


## Authors

Tyler Price

* http://twitter.com/thoughtcrimes
* https://github.com/tylerxprice


## MIT License

Copyright (C) 2011 by Tyler Price

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
