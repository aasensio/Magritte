import os
import sys

curdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{curdir}/../../../')


import numpy             as np
import scipy             as sp
import magritte.setup    as setup
import magritte.core     as magritte
import healpy


dimension = 3
nshells   = 20
nrays     = 12*3**2
nspecs    = 5
nlspecs   = 1
nquads    = 1

r_in   = 1.0E13   # [m]
r_out  = 7.8E16   # [m]
rho_in = 2.0E13   # [m^-3]
X_mol  = 1.0E-8   # [.]
temp   = 20.0     # [K]
turb   = 150.00   # [.]


def rho (r):
    return rho_in * np.power(r_in/r, 2.0)

def abn (r):
    return X_mol * rho(r)


r_shell = np.logspace (np.log10(r_in), np.log10(r_out), nshells, endpoint=True)

npoints_in_shell = [healpy.nside2npix(1+s) for s in range(nshells)]
npoints          = sum(npoints_in_shell)


xyz = np.array([[0, 0, 0]])
for (r, n) in zip(r_shell, npoints_in_shell):
    pos = r*np.array(healpy.pixelfunc.pix2vec(healpy.npix2nside(n), range(n))).T
    pos = sp.spatial.transform.Rotation.random().apply(pos)
    xyz = np.concatenate((xyz, pos))
position = xyz[1:]

rs = np.linalg.norm(position, axis=1)

modelFile = f'{curdir}/vanZadelhoff_1a_3D.hdf5'
lamdaFile = f'{curdir}/../../data/test.txt'


model = magritte.Model ()
model.parameters.set_model_name(modelFile)
model.parameters.set_dimension (dimension)
model.parameters.set_npoints   (npoints)
model.parameters.set_nrays     (nrays)
model.parameters.set_nspecs    (nspecs)
model.parameters.set_nlspecs   (nlspecs)
model.parameters.set_nquads    (nquads)

model.geometry.points.position.set(position)
model.geometry.points.velocity.set(np.zeros((npoints, 3)))

model.chemistry.species.abundance = [[     0.0, abn(r), rho(r),  0.0,      1.0] for r in rs]
model.chemistry.species.symbol    =  ['dummy0', 'test',   'H2', 'e-', 'dummy1']

model.thermodynamics.temperature.gas  .set( temp                 * np.ones(npoints))
model.thermodynamics.turbulence.vturb2.set((turb/magritte.CC)**2 * np.ones(npoints))

model = setup.set_Delaunay_neighbor_lists (model)

model.parameters.set_nboundary(npoints_in_shell[-1])
model.geometry.boundary.boundary2point.set(range(npoints-npoints_in_shell[-1], npoints))

model = setup.set_boundary_condition_CMB  (model)
model = setup.set_uniform_rays            (model)
model = setup.set_linedata_from_LAMDA_file(model, lamdaFile)
model = setup.set_quadrature              (model)

model.write()
model.read ()

model.compute_spectral_discretisation ()
model.compute_inverse_line_widths     ()
model.compute_LTE_level_populations   ()
model.compute_level_populations       (False, 50)