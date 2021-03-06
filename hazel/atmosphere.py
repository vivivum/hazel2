from collections import OrderedDict
import numpy as np
import os
from hazel.util import i0_allen, fvoigt
from hazel.codes import hazel_code, sir_code
from hazel.hsra import hsra_continuum
from hazel.io import Generic_hazel_file, Generic_SIR_file, Generic_parametric_file
from hazel.transforms import transformed_to_physical, physical_to_transformed, jacobian_transformed_to_physical, jacobian_transformation
import copy
# from ipdb import set_trace as stop
from hazel.sir import Sir


__all__ = ['General_atmosphere']
    
class General_atmosphere(object):
    def __init__(self, atm_type, name):
        self.ff = 1.0
        self.name = name

        self.active_lines = []
        self.wavelength = dict()
        self.wavelength_range = dict()
        self.wvl_axis = dict()
        self.wvl_range = dict()
        self.type = atm_type
        self.spectrum = dict()
        self.active = False
        self.n_pixel = 1
        self.stray_profile = None
        

        self.multiplets = {'10830': 10829.0911, '3888': 3888.6046, '7065': 7065.7085, '5876': 5875.9663}

        self.parameters = OrderedDict()
        self.ranges = OrderedDict()
        self.cycles = OrderedDict()
        self.n_nodes = OrderedDict()
        self.nodes = OrderedDict()
        self.epsilon = OrderedDict()
        self.error = OrderedDict()
        self.jacobian = OrderedDict()
        self.units = OrderedDict()

    def allocate_info_cycles(self, n_cycles):
        """
        Set the appropriate variables to store per-cycle models
        
        Parameters
        ----------        
        n_cycles : int
            Number of cycles
        
        Returns
        -------
        None
    
        """

        self.reference_cycle = [None] * n_cycles

    def to_physical(self):
        """
        Transform the atmospheric parameters from transformed domain to physical domain given the ranges.
        This only applies in inversion mode
        
        Parameters
        ----------        
        None
        
        Returns
        -------
        None
    
        """
        
        for k, v in self.parameters.items():            
            lower = self.ranges[k][0]
            upper = self.ranges[k][1]
            self.parameters[k] = transformed_to_physical(v, lower, upper)
            self.jacobian[k] = jacobian_transformed_to_physical(v, lower, upper)
                        
    def to_transformed(self):
        """
        Transform the atmospheric parameters from transformed domain to physical domain given the ranges.
        This only applies in inversion mode
        
        Parameters
        ----------        
        None
        
        Returns
        -------
        None
    
        """
        for k, v in self.parameters.items():                        
            lower = self.ranges[k][0]
            upper = self.ranges[k][1]            
            self.parameters[k] = physical_to_transformed(v, lower, upper)
            

    def set_reference(self, cycle=None):
        """
        Set reference model to that of the current parameters

        Parameters
        ----------
        None

        Returns
        -------
        None
        """            
        self.nodes_to_model()
        self.reference = copy.deepcopy(self.parameters)

        if (cycle is not None):
            self.to_physical()        
            self.reference_cycle[cycle] = copy.deepcopy(self.parameters)

    def init_reference(self, check_borders=False):
        """
        Initialize the reference atmosphere to the values of the parameters, doing the inverse transformation if in inversion mode

        Parameters
        ----------
        check_borders : bool
            Check that the input parameters are inside the ranges of parameters

        Returns
        -------
        None
        """

        # Transform parameters to  unbounded domain
        if (self.working_mode == 'inversion'):
            if (check_borders):
                for k, v in self.parameters.items():                    
                    if (not np.all(np.logical_and(v >= self.ranges[k][0], v <= self.ranges[k][1]))):
                        raise Exception("Parameter {0} of atmosphere {1} is outside ranges".format(k, self.name))

            self.to_transformed()            

        self.reference = copy.deepcopy(self.parameters)
        