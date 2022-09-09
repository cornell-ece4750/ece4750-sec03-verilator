#=========================================================================
# IntMulScycleV1_test
#=========================================================================

import pytest

from random import randint

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_sim
from pymtl3.stdlib.stream import StreamSourceFL, StreamSinkFL

from imul.IntMulScycleV3 import IntMulScycleV3

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, imul, src_msgs, sink_msgs, delay=0 ):

    # Instantiate models

    s.src  = StreamSourceFL( Bits64, src_msgs  )
    s.sink = StreamSinkFL  ( Bits32, sink_msgs,
                             initial_delay=delay, interval_delay=delay )
    s.imul = imul

    # Connect

    s.src.ostream  //= s.imul.istream
    s.imul.ostream //= s.sink.istream

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " > " + s.imul.line_trace() + " > " + s.sink.line_trace()

#-------------------------------------------------------------------------
# mk_imsg/mk_omsg
#-------------------------------------------------------------------------
# Make input/output msgs, truncate ints to ensure they fit in 32 bits.

def mk_imsg( a, b ):
  return concat( Bits32( a, trunc_int=True ), Bits32( b, trunc_int=True ) )

def mk_omsg( a ):
  return Bits32( a, trunc_int=True )

#-------------------------------------------------------------------------
# test_basic
#-------------------------------------------------------------------------

def test_basic( cmdline_opts ):

  src_msgs  = [ mk_imsg(2,2), mk_imsg(3,3) ]
  sink_msgs = [ mk_omsg(4),   mk_omsg(9)   ]

  th = TestHarness( IntMulScycleV3(), src_msgs, sink_msgs )
  run_sim( th, cmdline_opts, duts=['imul'] )

#-------------------------------------------------------------------------
# test_overflow
#-------------------------------------------------------------------------

def test_overflow( cmdline_opts ):

  src_msgs  = [ mk_imsg(0x80000001,2), mk_imsg(0xc0000002,4) ]
  sink_msgs = [ mk_omsg(2),            mk_omsg(8)            ]

  th = TestHarness( IntMulScycleV3(), src_msgs, sink_msgs )
  run_sim( th, cmdline_opts, duts=['imul'] )

#-------------------------------------------------------------------------
# test_random
#-------------------------------------------------------------------------

def test_random( cmdline_opts ):

  src_msgs  = []
  sink_msgs = []

  for i in range(10):
    a = randint(0,100)
    b = randint(0,100)
    src_msgs.extend ([ mk_imsg(a,b) ])
    sink_msgs.extend([ mk_omsg(a*b) ])

  th = TestHarness( IntMulScycleV3(), src_msgs, sink_msgs )
  run_sim( th, cmdline_opts, duts=['imul'] )

#-------------------------------------------------------------------------
# test_random_delay1
#-------------------------------------------------------------------------

def test_random_delay1( cmdline_opts ):

  src_msgs  = []
  sink_msgs = []

  for i in range(10):
    a = randint(0,100)
    b = randint(0,100)
    src_msgs.extend ([ mk_imsg(a,b) ])
    sink_msgs.extend([ mk_omsg(a*b) ])

  th = TestHarness( IntMulScycleV3(), src_msgs, sink_msgs, 1 )
  run_sim( th, cmdline_opts, duts=['imul'] )

#-------------------------------------------------------------------------
# test_random_delay3
#-------------------------------------------------------------------------

def test_random_delay3( cmdline_opts ):

  src_msgs  = []
  sink_msgs = []

  for i in range(10):
    a = randint(0,100)
    b = randint(0,100)
    src_msgs.extend ([ mk_imsg(a,b) ])
    sink_msgs.extend([ mk_omsg(a*b) ])

  th = TestHarness( IntMulScycleV3(), src_msgs, sink_msgs, 3 )
  run_sim( th, cmdline_opts, duts=['imul'] )

