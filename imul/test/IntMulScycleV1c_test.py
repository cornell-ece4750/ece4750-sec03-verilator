#=========================================================================
# IntMulScycleV1_test
#=========================================================================

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import run_test_vector_sim

from imul.IntMulScycleV1 import IntMulScycleV1

#-------------------------------------------------------------------------
# basic
#-------------------------------------------------------------------------

basic_test_vectors = [
  ('in0 in1 out*'),
  [ 2,  2,  '?'  ],
  [ 3,  2,   4   ],
  [ 3,  3,   6   ],
  [ 0,  0,   9   ],
]

#-------------------------------------------------------------------------
# overflow
#-------------------------------------------------------------------------

overflow_test_vectors = [
  ('in0         in1 out*'),
  [ 0x80000001, 2,  '?'  ],
  [ 0xc0000002, 4,   2   ],
  [ 0x00000000, 0,   8   ],
]

#-------------------------------------------------------------------------
# test_overflow
#-------------------------------------------------------------------------

@pytest.mark.parametrize( "test_vectors", [
  basic_test_vectors,
  overflow_test_vectors
])
def test_overflow( test_vectors, cmdline_opts ):
    run_test_vector_sim( IntMulScycleV1(), test_vectors, cmdline_opts )

