
ECE 4750 Section 3: RTL Testing with Python
==========================================================================

 - Author: Christopher Batten
 - Date: September 9, 2022

**Table of Contents**

 - Overview of Testing Strategies
 - Ad-Hoc vs. Assertion Testing
 - Testing with pytest
 - Testing with Test Vectors
 - Testing with Stream Sources and Sinks
 - Using Functional-Level Models

This discussion section serves as gentle introduction to the basics of
RTL testing using Python. We will start by discussing various different
kinds of testing strategies including:

 - Ad-Hoc vs. Assertion Testing
 - Directed vs. Random Testing
 - Black-Box vs. White-Box Testing
 - Unit vs. Integration Testing
 - Reference Models

After this discussion you should log into the `ecelinux` servers using
the remote access option of your choice and then source the setup script.

    % source setup-ece4750.sh
    % mkdir -p $HOME/ece4750
    % cd $HOME/ece4750
    % git clone git@github.com:cornell-ece4750/ece4750-sec03-pymtl sec03
    % cd sec03
    % TOPDIR=$PWD
    % mkdir $TOPDIR/build

Ad-Hoc vs. Assertion Testing
--------------------------------------------------------------------------

We will start by testing the simple single-cycle multiplier, we developed
in last week's discussion section which does include any kind of flow
control (i.e., no valid/ready signals):

![](assets/fig/imul-v1.png)

As a reminder, here is the interface for our single-cycle multiplier.

    module imul_IntMulScycleV1
    (
      input  logic        clk,
      input  logic        reset,

      input  logic [31:0] in0,
      input  logic [31:0] in1,
      output logic [31:0] out
    );

Our single-cycle multiplier takes two 32-bit input values and produces a
32-bit output value. Let's use the same ad-hoc test we used last week to
test this multiplier. Start by reviewing the Python test bench located in
`imul/imul-v1-adhoc-test.py`:

    from sys import argv

    from pymtl3  import *
    from pymtl3.passes.backends.verilog import *

    from IntMulScycleV1 import IntMulScycleV1

    # Get list of input values from command line

    in0_values = [ int(x,0) for x in argv[1::2] ]
    in1_values = [ int(x,0) for x in argv[2::2] ]

    # Create and elaborate the model

    model = IntMulScycleV1()
    model.elaborate()

    # Apply the Verilog import passes and the default pass group

    model.apply( VerilogPlaceholderPass() )
    model = VerilogTranslationImportPass()( model )
    model.apply( DefaultPassGroup(linetrace=True,textwave=True,vcdwave="imul-v1-adhoc-test") )

    # Reset simulator

    model.sim_reset()

    # Apply input values and display output values

    for in0_value,in1_value in zip(in0_values,in1_values):

      # Write input value to input port

      model.in0 @= in0_value
      model.in1 @= in1_value
      model.sim_eval_combinational()

      # Tick simulator one cycle

      model.sim_tick()

    # Tick simulator three more cycles and print text wave

    model.sim_tick()
    model.sim_tick()
    model.sim_tick()
    model.print_textwave()

The test bench gets some input values from the command line, instantiates
the design under test, applies some PyMLT3 passes, and then runs a
simulation by setting the input values and displaying the output value.
Let's run this ad-hoc test as follows:

    % cd $TOPDIR/build
    % python ../imul/imul-v1-adhoc-test.py 2 2 3 3

Experiment with different input values. Try large values that result in
overflow:

    % cd $TOPDIR/build
    % python ../imul/imul-v1-adhoc-test.py 70000 70000

In _ad-hoc testing_, we try different inputs and inspect the output
manually to see if the design under test produces the correct result.
This “verification by inspection” is error prone and not reproducible. If
you later make a change to your design, you would have to take another
look at the debug output and/or waveforms to ensure that your design
still works. If another member of your group wants to understand your
design and verify that it is working, he or she would also need to take a
look at the debug output and/or waveforms. Ad-hoc testing is usually
verbose, which makes it error prone and more cumbersome to write tests.
Ad-hoc testing is difficult for others to read and understand since by
definition it is ad-hoc. Ad-hoc testing does not use any kind of standard
test output, and does not provide support for controlling the amount of
test output. While using ad-hoc testing might be feasible for very simple
designs, it is obviously not a scalable approach when building the more
complicated designs we will tackle in this course.

The first step to improving our testing strategy is to use _assertion
testing_ where we explictly write assertions that must be true for the
test to pass. This way we have made the checking for the correct results
systematic and automatic. Take a look at the simple Python test bench for
assertion testing located in `imul/imul-v1-assertion-test.py`:

    def test_basic():

      ... create and elaborate model ...
      ... apply Verilog import passes and the default pass group ...

      model.sim_reset()

      model.in0 @= 2
      model.in1 @= 2
      model.sim_tick()
      assert model.out == 0

    def test_basic():

      ... create and elaborate model ...
      ... apply Verilog import passes and the default pass group ...

      model.sim_reset()

      model.in0 @= 0x80000001
      model.in1 @= 2
      model.sim_tick()
      assert model.out == 0

    test_basic()
    test_overflow()

We have structured our assertion testing into a set of _test cases_. Each
test case is implemented as a Python function named with the prefix
`test_`. Each test case creates and elaborates the design under test,
applies appropriate passes, and resets the model. The test case then sets
the inputs to the model, ticks the simulator, and asserts that the output
of the model match the expected value. We explicitly call both test case
functions at the end of the script. Let's run this assertion test:

    % cd $TOPDIR/build
    % python ../imul/imul-v1-assertion-test.py

The first test case will fail since we have not specified the correct
expected value. Modify the assertion test script to have the correct
expected values for both test cases and then rerun the assertion test.

Testing with pytest
--------------------------------------------------------------------------

In this course, we will be using the powerful `pytest` unit testing
framework. The `pytest` framework is popular in the Python programming
community with many features that make it well-suited for test-driven
hardware development including: no-boilerplate testing with the standard
assert statement; automatic test discovery; helpful traceback and
failing assertion reporting; standard output capture; sophisticated
parameterized testing; test marking for skipping certain tests;
distributed testing; and many third-party plugins. More information is
available here:

 - <http://www.pytest.org>

It is pretty easy to adapt the assertion test script we already have to
make it suitable for use with `pytest`. Usually we like to keep all of
our tests in a dedicated `test` subdirectory. Take a look at the test
script `imul/test/IntMulScycleV1a_test.py`. It looks exactly like our
previous assertion test script with two changes:

 - we pass in `cmdline_opts` to each test case function
 - we do not need to explicitly call the test case functions at the bottom of the script

Let's use `pytest` to run this test:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV1a_test.py

You can see that `pytest` has automatically discovered the two test
cases; `pytest` will assume any function that starts with the `test_`
prefix is a test case. The test cases will fail since we have not
specified the correct expected values. We can use the `-v` command line

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV1a_test.py -v

We can then "zoom in" on the first test case using the `-k` command line
option to run just that first test case:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV1a_test.py -v -k test_basic

Then we can use the `-s` option to display the line trace and the
`--dump-vcd` option to dump the VCD file.

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV1a_test.py -v -k test_basic -s --dump-vcd

Modify the test script to have the correct expected values for both test
cases and then rerun the test using `pytest`.

Testing with Test Vectors
--------------------------------------------------------------------------

Our testing so far requires quite a bit of boilerplate code. Every test
case must construct a model, elaborate that model, apply PyMTL3 passes,
and reset the simulator. For every cycle, the test case must set the
inputs, tick the simulator, and check the outputs. We can use the power
of Python to encapsulate much of this common functionality into a library
to simplify testing. PyMTL3 provides a `run_test_vector_sim` function
that makes it easy to write these kind of cycle-by-cycle tests where we
want to explicitly set inputs and check outputs every cycle. Take a look
at the test script `imul/test/IntMulScycleV1b_test.py`.

    def test_basic( cmdline_opts ):
      run_test_vector_sim( IntMulScycleV1(), [
        ('in0 in1 out*'),
        [ 2,  2,  '?'  ],
        [ 3,  2,   0   ],
        [ 3,  3,   0   ],
        [ 0,  0,   0   ],
      ], cmdline_opts )

    def test_overflow( cmdline_opts ):
      run_test_vector_sim( IntMulScycleV1(), [
        ('in0         in1 out*'),
        [ 0x80000001, 2,  '?'  ],
        [ 0xc0000002, 4,   0   ],
        [ 0x00000000, 0,   0   ],
      ], cmdline_opts )

The `run_test_vector_sim` takes three arguments: a design under test, the
test vector table, and the command line options. The first row in the
test vector table specifies the names of the input and output ports.
Output ports need to be indicated by adding a `*` suffix. The remaining
rows in the test vector table specify the inputs and the correct outputs
for every cycle. We can indicate we don't care about an output on a given
cycle with `?`. Notice how Python can make things very compact while at
the same time very readable. Let's use `pytest` to run this test:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV1b_test.py -s -v

The test cases will fail since we have not specified the correct expected
values. Modify the test script to have the correct expected values for
both test cases and then rerun the test using `pytest`. Use the `-v` and
`-s` options and notice that the line trace roughly corresponds to the
test vector table.

But wait there is more! We can use the `pytest.mark.parametrize`
decorator to parameterize a single test case over many different
parameters. In other words, instead of explicitly defining two test case
functions, we can _generate_ two test case functions from a single
specification. Take a look at the test script
`imul/test/IntMulScycleV1c_test.py`.

    basic_test_vectors = [
      ('in0 in1 out*'),
      [ 2,  2,  '?'  ],
      [ 3,  2,   0   ],
      [ 3,  3,   0   ],
      [ 0,  0,   0   ],
    ]

    overflow_test_vectors = [
      ('in0         in1 out*'),
      [ 0x80000001, 2,  '?'  ],
      [ 0xc0000002, 4,   0   ],
      [ 0x00000000, 0,   0   ],
    ]

    @pytest.mark.parametrize( "test_vectors", [
      basic_test_vectors,
      overflow_test_vectors
    ])
    def test_overflow( test_vectors, cmdline_opts ):
        run_test_vector_sim( IntMulScycleV1(), test_vectors, cmdline_opts )

Here we define test vector tables and then we use those test vector
tables in the `pytest.mark.parametrize` decorator. In this specific
example it does not save too much boiler plate, but we will see in the
next section how this is a very powerful way to generate test cases.
Modify the test script to have the correct expected values for both test
cases and then rerun the test using `pytest`. Use the `-v` and `-s`
options and notice that the output is basically the same as if we have
explicitly defined two test cases.

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV1c_test.py -s -v

Testing with Stream Sources and Sinks
--------------------------------------------------------------------------

![](assets/fig/imul-v3.png)

![](assets/fig/imul-v3-src-sink.png)

 - V3a: directed src/sink, no delays
 - V3b: add random src/sink, no delays
 - V3c: add delays
 - V3d: test case table

Using Functional-Level Models
--------------------------------------------------------------------------

 - run FL model
 - run all of the tests
