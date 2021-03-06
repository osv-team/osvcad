# coding: utf-8

r"""Geometry computations

The highlight of this module is the computation of the transformation matrix
from 2 anchors.

The module also features a function that transforms an anchor using a 4x3
transformation matrix and a function that builds a ccad.model.Solid
(of compound type) from a list of OCC shapes

"""

import logging

import numpy as np

from OCC.Core.TopoDS import TopoDS_Builder, TopoDS_Compound
from ccad.model import Solid, Shape

from osvcad.transformations import translation_matrix, rotation_matrix,\
    angle_between_vectors, vector_product


logger = logging.getLogger(__name__)


def transformation_from_2_anchors(anchor_master,
                                  anchor_slave,
                                  angle=0.,
                                  distance=0.):
    r"""Compute the transformation to bring vector_b's origin
    to vector_a's origin and to align vector_b with vector_a

    vector_a does not move.

    Parameters
    ----------
    anchor_master : dict
        {"position": (1, 2, 3), "direction": (4, 5, 6)}
    anchor_slave : same as vector_a
    angle : float, optional (default is 0.)
        Angle in degrees
        Putting the master and slave anchors in opposition
        leaves one degree of freedom that is dealt with by the angle
    distance : float, optional (default is 0.)
        Distance between the anchor positions

    Returns
    -------
    np.ndarray : 4 x 3 transformation matrix

    """
    logger.debug("Computing transformation from 2 anchors")
    logger.debug(("Master | pos : %s | dir : %s" % (anchor_master["position"],
                                                    anchor_master["direction"])))
    logger.debug(("Slave  | pos : %s | dir : %s" % (anchor_slave["position"],
                                                    anchor_slave["direction"])))
    logger.debug("Distance : %f" % distance)
    logger.debug("Angle : %f" % angle)

    pa_x, pa_y, pa_z = anchor_master["position"]
    pb_x, pb_y, pb_z = anchor_slave["position"]

    trans_slave_to_orig = (-pb_x, -pb_y, -pb_z)

    angle_anchors = angle_between_vectors(anchor_master["direction"],
                                          anchor_slave["direction"])
    import math

    logger.debug("Angle between anchors : %f deg" % math.degrees(angle_anchors))

    if math.isnan(angle_anchors):
        logger.critical("Angle between anchors is NAN")

    axis_dir = vector_product(anchor_master["direction"],
                              anchor_slave["direction"])

    angle_correction = 0.  # correction for special cases

    if np.array_equal(axis_dir, np.array([0, 0, 0])):
        # logger.debug("Axis dir is equal to [0, 0, 0]")
        # anchor directions are parallel, any perpendicular axis will do
        # BUT
        # we have to distinguish between:
        #   - collinear in the same direction
        #   - collinear in opposite directions
        norm_of_sum = np.linalg.norm(np.array(anchor_master["direction"]) +
                                     np.array(anchor_slave["direction"]))
        if norm_of_sum > np.linalg.norm(np.array(anchor_master["direction"])):
            angle_correction = np.pi

        # arbitrary unit vector, just make sure not parallel
        if np.array_equal(np.cross(np.array([1.,  0., 0.]),
                                   np.array(anchor_master["direction"])),
                          np.array([0, 0, 0])):
            k = np.array([0.,  1., 0.])
        else:
            k = np.array([1., 0., 0.])

        y = np.cross(k, np.array(anchor_master["direction"]))

        axis_dir = y
        # logger.debug("Axis dir is now %s" % axis_dir)

    # rot_matrix = rotation_matrix(angle + np.pi, axis_dir)
    rot_angle = -angle_anchors % np.pi + angle_correction
    rot_matrix_anchors_opposition = rotation_matrix(rot_angle, axis_dir)

    trans_orig_to_master = (pa_x, pa_y, pa_z)

    transformation_mat_anchors_opposition = \
        np.dot(translation_matrix(trans_orig_to_master),
               np.dot(rot_matrix_anchors_opposition,
                      translation_matrix(trans_slave_to_orig)))

    # angle and distance
    trans_master_to_orig = (-pa_x, -pa_y, -pa_z)

    rot_matrix_around_anchor = rotation_matrix(np.radians(angle),
                                               anchor_master["direction"])
    unit_anchor_direction = [c / np.linalg.norm(anchor_master["direction"])
                             for c in anchor_master["direction"]]

    # assert 1 - 1e-6 <= np.linalg.norm(unit_anchor_direction) <= 1. + 1e-6

    if not (1 - 1e-6 <= np.linalg.norm(unit_anchor_direction) <= 1. + 1e-6):
        msg = "Unit anchor direction norm should be 1 +- tolerance"
        logger.error(msg)
        raise AssertionError(msg)

    transformation_mat_near_anchor = \
        np.dot(translation_matrix(np.array(anchor_master["position"]) +
                                  np.array(unit_anchor_direction) * distance),
               np.dot(rot_matrix_around_anchor,
                      translation_matrix(trans_master_to_orig)))[:3]

    transformation_mat = np.dot(transformation_mat_near_anchor,
                                transformation_mat_anchors_opposition)[:3]

    logger.debug("... Done computing transformation from 2 anchors")
    return transformation_mat


def transform_anchor(anchor, transformation_matrix):
    r"""Transform an anchor using a transformation matrix

    Parameters
    ----------
    anchor : dict
        A dict with a least the position and direction keys
    transformation_matrix : np.ndarray
        4 x 3 matrix

    """

    translation_vec = transformation_matrix.T[-1:, :3][0]
    matrix_3x3 = transformation_matrix[:3, :3]

    px, py, pz = anchor["position"]
    dx, dy, dz = anchor["direction"]

    new_px, new_py, new_pz = np.dot(np.array([px, py, pz]),
                                    matrix_3x3.T) + translation_vec

    new_dx, new_dy, new_dz = np.dot(np.array([dx, dy, dz]),
                                    matrix_3x3.T)

    return {"position": (new_px, new_py, new_pz),
            "direction": (new_dx, new_dy, new_dz)}


def compound(shapes):
    r"""Accumulate a bunch of ccad.model.Solid in list `topo`
    to a TopoDS_Compound used to build a ccad.model.Solid

    Parameters
    ----------
    shapes : list[TopoDS_*]

    Returns
    -------
    ccad.model.Solid

    """
    for shape in shapes:
        if not isinstance(shape, Shape):
            raise ValueError("The shapes list "
                             "should only contains ccad.model.Shape(s)")
    bd = TopoDS_Builder()
    comp = TopoDS_Compound()
    bd.MakeCompound(comp)
    for shape in shapes:
        bd.Add(comp, shape.shape)

    return Solid(comp)
