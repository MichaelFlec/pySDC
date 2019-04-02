import copy as cp

import numpy as np
import pfft
from mpi4py import MPI

from pySDC.core.Errors import DataError


class mesh(object):
    """
    Mesh data type with arbitrary dimensions, made to work with parallel FFTs

    This data type can be used whenever structured data with a single unknown per point in space is required

    Attributes:
        values (np.ndarray): contains the ndarray of the values
    """

    def __init__(self, init=None, val=None):
        """
        Initialization routine

        Args:
            init: either another mesh object (create by copy) or an R2C object (FFT)
            val: initial value (default: None)
        Raises:
            DataError: if init is none of the types above
        """

        # if init is another mesh, do a deepcopy (init by copy)
        if isinstance(init, mesh):
            self.init = init.init
            self.values = cp.deepcopy(init.values)
        # if init is a number or a tuple of numbers, create mesh object with val as initial value
        elif isinstance(init, R2C):
            self.init = init
            self.values = np.empty(self.init.real_shape(), dtype=np.float64)
            self.values[:] = val
        # something is wrong, if none of the ones above hit
        else:
            raise DataError('something went wrong during %s initialization' % type(self))

    def __add__(self, other):
        """
        Overloading the addition operator for mesh types

        Args:
            other (mesh.mesh): mesh object to be added
        Raises:
            DataError: if other is not a mesh object
        Returns:
            mesh.mesh: sum of caller and other values (self+other)
        """

        if isinstance(other, mesh):
            # always create new mesh, since otherwise c = a + b changes a as well!
            me = mesh(self.init)
            me.values = self.values + other.values
            return me
        else:
            raise DataError("Type error: cannot add %s to %s" % (type(other), type(self)))

    def __sub__(self, other):
        """
        Overloading the subtraction operator for mesh types

        Args:
            other (mesh.mesh): mesh object to be subtracted
        Raises:
            DataError: if other is not a mesh object
        Returns:
            mesh.mesh: differences between caller and other values (self-other)
        """

        if isinstance(other, mesh):
            # always create new mesh, since otherwise c = a - b changes a as well!
            me = mesh(self.init)
            me.values = self.values - other.values
            return me
        else:
            raise DataError("Type error: cannot subtract %s from %s" % (type(other), type(self)))

    def __rmul__(self, other):
        """
        Overloading the right multiply by factor operator for mesh types

        Args:
            other (float): factor
        Raises:
            DataError: is other is not a float
        Returns:
            mesh.mesh: copy of original values scaled by factor
        """

        if isinstance(other, float) or isinstance(other, complex):
            # always create new mesh, since otherwise c = f*a changes a as well!
            me = mesh(self.init)
            me.values = self.values * other
            return me
        else:
            raise DataError("Type error: cannot multiply %s to %s" % (type(other), type(self)))

    def __abs__(self):
        """
        Overloading the abs operator for mesh types

        Returns:
            float: absolute maximum of all mesh values
        """

        # take absolute values of the mesh values
        local_absval = abs(self.values)
        global_absval = self.init.comm.allreduce(np.amax(local_absval), MPI.MAX)
        # return maximum
        return global_absval

    def send(self, dest=None, tag=None, comm=None):
        """
        Routine for sending data forward in time (blocking)

        Args:
            dest (int): target rank
            tag (int): communication tag
            comm: communicator

        Returns:
            None
        """

        comm.send(self.values, dest=dest, tag=tag)
        return None

    def isend(self, dest=None, tag=None, comm=None):
        """
        Routine for sending data forward in time (non-blocking)

        Args:
            dest (int): target rank
            tag (int): communication tag
            comm: communicator

        Returns:
            request handle
        """
        return comm.isend(self.values, dest=dest, tag=tag)

    def recv(self, source=None, tag=None, comm=None):
        """
        Routine for receiving in time

        Args:
            source (int): source rank
            tag (int): communication tag
            comm: communicator

        Returns:
            None
        """
        self.values = comm.recv(source=source, tag=tag)
        return None

    def bcast(self, root=None, comm=None):
        """
        Routine for broadcasting values

        Args:
            root (int): process with value to broadcast
            comm: communicator

        Returns:
            broadcasted values
        """
        me = mesh(self.init)
        me.values = comm.bcast(self.values, root=root)
        return me


class rhs_imex_mesh(object):
    """
    RHS data type for meshes with implicit and explicit components

    This data type can be used to have RHS with 2 components (here implicit and explicit)

    Attributes:
        impl (mesh.mesh): implicit part
        expl (mesh.mesh): explicit part
    """

    def __init__(self, init, val=0.0):
        """
        Initialization routine

        Args:
            init: eitehr another rhs_imex_mesh (create by copy) or an R2C object (FFT)
            val (float): an initial number (default: 0.0)
        Raises:
            DataError: if init is none of the types above
        """

        # if init is another rhs_imex_mesh, do a deepcopy (init by copy)
        if isinstance(init, type(self)):
            self.init = init.init
            self.impl = mesh(init.impl)
            self.expl = mesh(init.expl)
        # if init is a number or a tuple of numbers, create mesh object with None as initial value
        elif isinstance(init, R2C):
            self.init = init
            self.impl = mesh(init, val=val)
            self.expl = mesh(init, val=val)
        # something is wrong, if none of the ones above hit
        else:
            raise DataError('something went wrong during %s initialization' % type(self))

    def __sub__(self, other):
        """
        Overloading the subtraction operator for rhs types

        Args:
            other (mesh.rhs_imex_mesh): rhs object to be subtracted
        Raises:
            DataError: if other is not a rhs object
        Returns:
            mesh.rhs_imex_mesh: differences between caller and other values (self-other)
        """

        if isinstance(other, rhs_imex_mesh):
            # always create new rhs_imex_mesh, since otherwise c = a - b changes a as well!
            me = rhs_imex_mesh(self.init)
            me.impl.values = self.impl.values - other.impl.values
            me.expl.values = self.expl.values - other.expl.values
            return me
        else:
            raise DataError("Type error: cannot subtract %s from %s" % (type(other), type(self)))

    def __add__(self, other):
        """
         Overloading the addition operator for rhs types

        Args:
            other (mesh.rhs_imex_mesh): rhs object to be added
        Raises:
            DataError: if other is not a rhs object
        Returns:
            mesh.rhs_imex_mesh: sum of caller and other values (self-other)
        """

        if isinstance(other, rhs_imex_mesh):
            # always create new rhs_imex_mesh, since otherwise c = a + b changes a as well!
            me = rhs_imex_mesh(self.init)
            me.impl.values = self.impl.values + other.impl.values
            me.expl.values = self.expl.values + other.expl.values
            return me
        else:
            raise DataError("Type error: cannot add %s to %s" % (type(other), type(self)))

    def __rmul__(self, other):
        """
        Overloading the right multiply by factor operator for mesh types

        Args:
            other (float): factor
        Raises:
            DataError: is other is not a float
        Returns:
             mesh.rhs_imex_mesh: copy of original values scaled by factor
        """

        if isinstance(other, float):
            # always create new rhs_imex_mesh
            me = rhs_imex_mesh(self.init)
            me.impl.values = other * self.impl.values
            me.expl.values = other * self.expl.values
            return me
        else:
            raise DataError("Type error: cannot multiply %s to %s" % (type(other), type(self)))
