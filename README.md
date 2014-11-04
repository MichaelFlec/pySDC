pySDC
======

The pySDC project is a Python implementation of the spectral deferred correction (SDC) approach and its flavors, 
esp. the multilevel extension MLSDC. It is intended for rapid prototyping and educational purposes. New ideas like e.g 
sweepers or predictors can be tested and first toy problems can be easily implemented. A further extension to PFASST 
(at least virtually parallel) is possible and on the todo list (volunteers welcomed).


News
----

* November 4, 2014: First open source release on github, four very basic examples up and running, code is documented


Documentation and Testing
-----------------------

Doxygen generated documentation can be found in the doc directory, a Doxyfile is provided. To compile your own, 
full doxygen-based documentation, use the [doxypypy](https://github.com/Feneric/doxypypy) filter.

Some first, rather rudimentary tests can be found in the tests directory and nose should be able to run those 
out-of-the-box.


HowTo
-----

To start your own example, take a look at the examples shipped with this code:

* heat1d: MLSDC implementation of the forced 1D heat equation with Dirichlet-0 BC in [0,1]
* penningtrap: a particle in a penning trap, driven by external electric and magnetic fields
* spiraling_particle: a particle moving in varying electric and magnetic fields
* vanderpol: the van der pol oscillator

Each of these examples should demonstrate some features of this code, e.g. MLSDC and an IMEX sweeper for the heat 
equation, the Boris-SDC approach in the particle case and the LU decomposition as well as the application of a 
nonlinear solver in the van der pol example.
 
For a new example, you have to either choose or provide at least five components:

* the collocation, examples can be found in pySDC/CollocationClasses.py
* a problem description, examples can be found in examples/*/ProblemClass.py
* a data type, examples can be found in pySDC/datatype_classes/
* a sweeper, examples can be found in pySDC/sweeper_classes/
* a method/stepper, where SDC and MLSDC are already provided in pySDC/Methods.py


For MLSDC, suitable transfer operators are also required, examples can be found e.g. in examples/heat1d/TransferClass.py.

The playground.py routines in the examples show how these components need to be linked together. Basically, 
most of the management is done via the level and the step data structures. Here, 
the components are coupled as expected by the method and all the other components.

In the easiest case (where collocation, data type, sweeper, method and transfer operators can be used as provided 
with this code ), only a custom problem description and a suitable transfer between degrees-of-freedom has to be 
implemented.

Note: all interfaces are subject to changes, if necessary.


