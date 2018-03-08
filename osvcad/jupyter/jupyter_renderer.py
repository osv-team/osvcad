#!/usr/bin/python
# coding: utf-8

r"""OCC.Display.WebGl.jupyter_renderer's JupyterRenderer enhancement

Vectors display

"""

from __future__ import division

from ccad.model import cylinder, cone
from OCC.Display.WebGl.jupyter_renderer import JupyterRenderer

from osvcad.geometry import transformation_from_2_anchors


class JupyterRendererV(JupyterRenderer):
    def __init__(self):
        super(JupyterRendererV, self).__init__()

    def DisplayVector(self, origin, direction, multiplier=1):
        assert len(origin) == 3
        assert len(direction) == 3

        xo, yo, zo = origin
        xd, yd, zd = direction

        norm = (xd**2 + yd**2 + zd**2)**0.5

        # create a cylinder
        cy = cylinder(rad=norm / 20, height=norm * 2 / 3)

        # create a cone
        co = cone(rad1=norm / 8, rad2=0, height=norm / 3)
        co.translate((0., 0., norm * 2 / 3))

        # cy.translate(origin)
        # co.translate(origin)

        tr = transformation_from_2_anchors({"position": (xo, yo, zo), "direction": (xd, yd, zd)},
                                           {"position": (0, 0, 0), "direction": (0, 0, 1)})

        cy.transform(tr)
        co.transform(tr)

        # display them
        self.DisplayShape(cy.shape, shape_color="yellow")
        self.DisplayShape(co.shape, shape_color="yellow")


