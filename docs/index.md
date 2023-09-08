
ECE 4750 Section 3: RTL Testing with Verilator
==========================================================================

 - Author: Cecilio C. Tamarit
 - Date: September 7, 2023
 - Inspired by previous ECE 4750 material

**Table of Contents**

 - VCD format and waveform visualization in VSCode
 - Overview of Testing Strategies
 - (Review: Testing with Stream Sources and Sinks)
 - Generating Coverage Reports with gcov/lcov

This discussion section serves as gentle introduction to the basics of
RTL testing using Verilator and gcov/lcov. 

Start by logging into the `ecelinux` servers using the remote access option 
of your choice and then source the setup script. We can then reuse the
setup from last week. Make sure you `make clean` if your directory from last 
week already exists:

Make sure you `make clean` if your directory from last week already exists:
    
    % cd $HOME/ece4750/sec/sec02
    % make clean

If it _doesn't_ exist, we can set it up again:

    % source setup-ece4750.sh
    % mkdir -p $HOME/ece4750/sec
    % cd $HOME/ece4750/sec
    % TOPDIR=$PWD
    % wget https://github.com/cornell-ece4750/ece4750-sec02-verilog/raw/m3/docs/sec02.tar.gz
    % tar xvf sec02.tar.gz
    % rm sec02.tar.gz
    % make setup
    % cd $TOPDIR/sec02


## Pro tip: VCD format and waveform visualization in VSCode

While GTKWave suits the needs of this class, VSCode users
will benefit from storing waveforms in the VCD format (as
opposed to FST). Several VCD visualization plug-ins exist
and can be installed right from VSCode, such as the one shown
below. This circumvents the need to resort to X11 or X2Go.

![](assets/fig/vsplugins.png)

However, we still need to modify `$TOPDIR/sec02/verilator.cpp`
so that we generate VCD files instead of FST files in the `waves`
folder. First, by including the right header at the top:

    ...
    #include "verilated_vcd_c.h"
    ...

Then, by modifying lines ~77-92 as follows to make use of the `VerilatedVcdC` class:

    Verilated::debug(0);
    Verilated::randReset(2);
    Verilated::traceEverOn(true);
    Verilated::commandArgs(argc, argv);
    Verilated::mkdir("logs");
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    Verilated::traceEverOn(true);
    Vtop* top = new Vtop{contextp.get(), "TOP"};  // Or use a const unique_ptr, or the VL_UNIQUE_PTR wrapper
      //svSetScope (svGetScopeFromName("Vtop.v"));
    VerilatedVcdC* tfp = new VerilatedVcdC;
    Verilated::traceEverOn(true);
    if(waves){
        top->trace(tfp, 99);  // Trace 99 levels of hierarchy
        Verilated::mkdir("waves");
        tfp->open((std::string("waves/")+outname +"waves.vcd").c_str());
    }

Lastly, defying course policy, edit the Makefile at 
`$TOPDIR/sec02/Makefile` so that line 88 becomes:

    VERILATOR_FLAGS += --trace

If you proceed to cleaning, regenerating, and running the testbench,
you will now find the VCD files in the `waves` folder. If you click
on any of them, the corresponding plug-in should launch. You should now
have a phenomenal 3-tile workflow set up! You can edit your Verilog
code, verilate, and debug it, all in the same window.

![](assets/fig/vscode.png)


Overview of Testing Strategies
--------------------------------------------------------------------------

Now let's get back to testing the simple single-cycle adder we developed
in last week's discussion:

![](assets/fig/adder.png)

As a reminder, here is the interface for our latency-insensitive adder:

    module sec02_Adder
    (
     input  logic        clk,
     input  logic        reset,
       
     input  logic        istream_val,
     output logic        istream_rdy,
     input  logic [63:0] istream_msg,
       
     output logic        ostream_val,
     input  logic        ostream_rdy,
     output logic [31:0] ostream_msg
    );

- Again, anyone care to explain how this works?

In tb_Adder.v we had set up the following sample test cases:

    test_case( { 32'd1, 32'd1 },  32'd2 );
    test_case( { 32'd2, 32'd2 },  32'd4 );
    test_case( { 32'd4, 32'd5 },  32'd9 );

As a reminder, we can then run these tests as follows:

    % cd $TOPDIR/sec02
    % make tb_Adder_RandDelay.v DESIGN=Adder

Experiment with different input values. Try large values that result in
overflow:

    test_case( { 32'd1, 32'd1 },  32'd2 );
    test_case( { 32'd2, 32'd2 },  32'd4 );
    test_case( { 32'd4294967295, 32'd1 },  32'd4294967296 );

What we have been doing is a form of _assertion testing_ where we 
explicitly define input vectors and expected outputs so that the
testbench systematically determines whether any given test passes or fails.
This is as opposed to _ad-hoc testing_, in which case we also specify
the inputs, but then manually inspect the output (e.g. traces or waves)
to determine whether they reflect the expected behavior. The latter approach
is only truly feasible in the context of small modules, or as you know,
for debugging, but as designs increase in complexity it is of the utmost
importance that an automated testing process be in place. Being able to
replicate the original testing strategy will save us a significant amount 
of time if we expect this design to be modified (by others) in the future. 

To discuss in class: testing spectra

 - Ad-Hoc vs. Assertion Testing
 - Directed vs. Random Testing
 - Black-Box vs. White-Box Testing
 - Value vs. Delay Testing
 - Unit vs. Integration Testing
 - Reference Models


Generating Coverage Reports with gcov/lcov
--------------------------------------------------------------------------

To discuss in class:

- Drawing from your own experience with Lab 1, define "coverage."
- Why is test coverage such a big deal?

In our Makefile, we have included a series of commands that will generate
coverage reports _after your tests have been run_. This last part is important
to stress, and in fact we recommend that you `make clean` and rerun the
tests you are interested in before proceeding with generating the report. Not
cleaning can result in stale and essentially incorrect reports.
For our example, we would generate the report as follows:

    % make clean
    % make tb_Adder_RandDelay.v DESIGN=Adder
    % make coverage-report

This will populate your `logs` folder...


Testing with Stream Sources and Sinks
--------------------------------------------------------------------------

So far we have been testing a latency-sensitive design. We write the
inputs on one cycle and then the result is produced after exactly one
cycle. In this course, we will make extensive use of latency-insensitive
streaming interfaces. Such interfaces use a val/rdy micro-protocol which
will enable other logic to always function correctly regardless of how
many cycles a component requires. Here is how we can implement a
single-cycle multiplier with a latency-insensitive streaming interface:

![](assets/fig/imul-v3.png)

Here is the interface for this single-cycle multiplier:

    module imul_IntMulScycleV3
    (
      input  logic        clk,
      input  logic        reset,

      input  logic        istream_val,
      output logic        istream_rdy,
      input  logic [63:0] istream_msg,

      output logic        ostream_val,
      input  logic        ostream_rdy,
      output logic [31:0] ostream_msg
    );

Testing a latency-sensitive design requires using cycle-by-cycle testing,
but when testing a latency-insensitive design we can make use of stream
sources and sinks to both simplify our testing strategy and at the same
time ensure we can robustly test the flow control.

![](assets/fig/imul-v3-src-sink.png)

Take a look at the test script `imul/test/IntMulScycleV3a_test.py`.

    class TestHarness( Component ):

      def construct( s, imul, imsgs, omsgs ):

        # Instantiate models

        s.src  = StreamSourceFL( Bits64, imsgs )
        s.sink = StreamSinkFL  ( Bits32, omsgs )
        s.imul = imul

        # Connect

        s.src.ostream  //= s.imul.istream
        s.imul.ostream //= s.sink.istream

      def done( s ):
        return s.src.done() and s.sink.done()

      def line_trace( s ):
        return s.src.line_trace() + " > " + s.imul.line_trace() + " > " + s.sink.line_trace()

The test harness composes a stream source, the latency-insensitive
single-cycle multiplier, and a stream sink. When constructing the test
harness we pass in a list of input messages for the stream source to send
to the multiplier, and a list of output messages for the stream sink to
check against the messages received from the multiplier. The stream source
and sink take care of correctly handling the val/rdy micro-protocol. Here
is what a test case now looks like:

    def test_basic( cmdline_opts ):

      imsgs = [ mk_imsg(2,2), mk_imsg(3,3) ]
      omsgs = [ mk_omsg(4),   mk_omsg(9)   ]

      th = TestHarness( IntMulScycleV3(), imsgs, omsgs )
      run_sim( th, cmdline_opts, duts=['imul'] )

The test cases look a little different from the previous approach.
Instead of creating a test vector table, we now need to create the input
and output message list and pass them into the test harness. We can use
the `run_sim` function to handle applying PyMTL3 passes and actually
ticking the simulator. Let's use `pytest` to run this test:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV3a_test.py -s -v

So far we have only been using directed testing, but random testing is of
course also very important to help increase our test coverage. Here is a
test case that randomly generates input messages and then calculates the
correct output messages:

    def test_random( cmdline_opts ):

      imsgs = []
      omsgs = []

      for i in range(10):
        a = randint(0,100)
        b = randint(0,100)
        imsgs.extend([ mk_imsg(a,b) ])
        omsgs.extend([ mk_omsg(a*b) ])

      th = TestHarness( IntMulScycleV3(), imsgs, omsgs )
      run_sim( th, cmdline_opts, duts=['imul'] )

You can use arbitrary Python to create a variety of random tests
sequences. Let's go ahead and run these random tests:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV3b_test.py -s -v

In addition to testing the values, we also want to test that the
latency-sensitive single-cycle multiplier correctly implements the
val/rdy micro protocol. In other words, we want to make sure that the
design under test can handle arbitrary source/sink delays. The stream
source and sink components enable setting an `initial_delay` and a
`interval_delay` to help with this kind of _delay testing_. Here we set
the delay to be three cycles in the stream sink:

    def test_random_delay3( cmdline_opts ):

      imsgs = []
      omsgs = []

      for i in range(10):
        a = randint(0,100)
        b = randint(0,100)
        imsgs.extend([ mk_imsg(a,b) ])
        omsgs.extend([ mk_omsg(a*b) ])

      th = TestHarness( IntMulScycleV3(), imsgs, omsgs, 3 )
      run_sim( th, cmdline_opts, duts=['imul'] )

Let's go ahead and run these delay tests:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV3c_test.py -s -v

Carefully compare the line trace to what we saw before without any
delays. Finally, we can use a test case table and the
`pytest.mark.parametrize` decorator to further simplify our test code.

    #-------------------------------------------------------------------------
    # mk_imsg/mk_omsg
    #-------------------------------------------------------------------------
    # Make input/output msgs, truncate ints to ensure they fit in 32 bits.

    def mk_imsg( a, b ):
      return concat( Bits32( a, trunc_int=True ), Bits32( b, trunc_int=True ) )

    def mk_omsg( a ):
      return Bits32( a, trunc_int=True )

    #-------------------------------------------------------------------------
    # test msgs
    #-------------------------------------------------------------------------

    basic_msgs = [
      mk_imsg(2,2), mk_omsg(4),
      mk_imsg(3,3), mk_omsg(9),
    ]

    overflow_msgs = [
      mk_imsg(0x80000001,2), mk_omsg(2),
      mk_imsg(0xc0000002,4), mk_omsg(8),
    ]

    random_msgs  = []
    for i in range(10):
      a = randint(0,100)
      b = randint(0,100)
      random_msgs.extend([ mk_imsg(a,b), mk_omsg(a*b) ])

    #-------------------------------------------------------------------------
    # Test Case Table
    #-------------------------------------------------------------------------

    test_case_table = mk_test_case_table([
      (                  "msgs          delay"),
      [ "basic",         basic_msgs,    0     ],
      [ "overflow",      overflow_msgs, 0     ],
      [ "random",        random_msgs,   0     ],
      [ "random_delay1", random_msgs,   1     ],
      [ "random_delay3", random_msgs,   3     ],
    ])

    #-------------------------------------------------------------------------
    # run tests
    #-------------------------------------------------------------------------

    @pytest.mark.parametrize( **test_case_table )
    def test( test_params, cmdline_opts ):

      imsgs = test_params.msgs[::2]
      omsgs = test_params.msgs[1::2]
      delay = test_params.delay

      th = TestHarness( IntMulScycleV3(), imsgs, omsgs, delay )
      run_sim( th, cmdline_opts, duts=['imul'] )

With a test case table, we can reuse the same input/output messages and
simply vary the delays. Let's try running the tests using this new
approach:

    % cd $TOPDIR/build
    % pytest ../imul/test/IntMulScycleV3d_test.py -s -v

Add a new row to the test case table that reuses the random messages but
with a delay of 10. Rerun the test case and look at the line trace to
verify the longer delays.


