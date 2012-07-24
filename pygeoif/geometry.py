# -*- coding: utf-8 -*-
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import re

wkt_regex = re.compile(r'^(SRID=(?P<srid>\d+);)?'
    r'(?P<wkt>'
    r'(?P<type>POINT|LINESTRING|LINEARRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)'
    r'[ACEGIMLONPSRUTYZ\d,\.\-\(\) ]+)$',
    re.I)



class _Feature(object):
    """ Base class """
    _type = None
    _coordinates = None

    @property
    def __geo_interface__(self):
        if self._type and self._coordinates:
            return {
                    'type': self._type,
                    'coordinates': tuple(self._coordinates)
                    }

    def __str__(self):
        return self.to_wkt()

    def to_wkt(self):
        return self._type.upper() + ' ' + str(tuple(self._coordinates)).replace(',','')


class Point(_Feature):
    """
    A zero dimensional feature

    A point has zero length and zero area.

    Attributes
    ----------
    x, y, z : float
        Coordinate values

    Example
    -------

      >>> p = Point(1.0, -1.0)
      >>> print p
      POINT (1.0000000000000000 -1.0000000000000000)
      >>> p.y
      -1.0
      >>> p.x
      1.0
    """

    _type = 'Point'

    def __init__(self, *args):
        """
        Parameters
        ----------
        There are 2 cases:

        1) 1 parameter: this must satisfy the __geo_interface__ protocol
            or be a tuple or list of x, y, [z]
        2) 2 or more parameters: x, y, [z] : float
            Easting, northing, and elevation.
        """
        if len(args) == 1:
            if hasattr(args[0], '__geo_interface__'):
                if args[0].__geo_interface__['type'] == 'Point':
                    self._coordinates = list(args[0].__geo_interface__['coordinates'])
                else:
                    raise TypeError
            else:
                if isinstance(args[0], (list, tuple)):
                    if 2 <= len(args[0]) <= 3:
                        coords = [float(x) for x in args[0]]
                        self._coordinates = coords
                    else:
                        raise TypeError
                else:
                    raise TypeError
        elif 2 <= len(args) <= 3:
            coords = [float(x) for x in args]
            self._coordinates = coords
        else:
            raise ValueError


    @property
    def x(self):
        """Return x coordinate."""
        return self._coordinates[0]

    @property
    def y(self):
        """Return y coordinate."""
        return self._coordinates[1]

    @property
    def z(self):
        """Return z coordinate."""
        if len(self._coordinates) != 3:
            raise ValueError("This point has no z coordinate.")
        return self._coordinates[2]

    @property
    def coords(self):
        return tuple(self._coordinates)

    @coords.setter
    def coords(self, coordinates):
        if isinstance(coordinates, (list, tuple)):
            if 2 <= len(coordinates) <= 3:
                coords = [float(x) for x in coordinates]
                self._coordinates = coords
            else:
                raise TypeError
        else:
            raise TypeError



class LineString(_Feature):
    """A one-dimensional figure comprising one or more line segments """
    _type = 'LineString'

    def __init__(self, coordinates):
        """
        Parameters
        ----------
        coordinates : sequence
            A sequence of (x, y [,z]) numeric coordinate pairs or triples
            or a sequence of Points or
            an object that provides the __geo_interface__, including another
            instance of LineString.

        Example
        -------
        Create a line with two segments

          >>> a = LineString([[0, 0], [1, 0], [1, 1]])
        """

        if hasattr(coordinates, '__geo_interface__'):
            gi = coordinates.__geo_interface__
            if (gi['type'] == 'LineString') or (gi['type'] == 'LinearRing'):
                self._coordinates = gi['coordinates']
            elif gi['type'] == 'Polygon':
                raise ValueError('Use poligon.exterior or polygon.interiors[x]')
            else:
                raise NotImplementedError
        elif isinstance(coordinates, (list, tuple)):
            coords = []
            for coord in coordinates:
                p = Point(coord)
                l = len(p.coords)
                if coords:
                    if l != l2:
                        raise ValueError
                l2 = l
                coords.append(tuple(p.coords))
            self._coordinates = coords
        else:
            raise ValueError


    @property
    def coords(self):
        return tuple(self._coordinates)

    @coords.setter
    def coords(self, coordinates):
        if isinstance(coordinates, (list, tuple)):
            coords = []
            for coord in coordinates:
                p = Point(coord)
                l = len(p.coords)
                if coords:
                    if l != l2:
                        raise ValueError
                l2 = l
                coords.append(tuple(p.coords))
            self._coordinates = coords
        else:
            raise ValueError

    def to_wkt(self):
        wc = [ ' '.join([str(x) for x in c]) for c in self.coords]
        return self._type.upper() + ' (' + ', '.join(wc) + ')'



class LinearRing(LineString):
    """
    A closed one-dimensional feature comprising one or more line segments

    A LinearRing that crosses itself or touches itself at a single point is
    invalid and operations on it may fail.

    A Linear Ring is self closing: self._coordinates[0] == self._coordinates[-1]
    """
    _type = 'LinearRing'

    def __init__(self, coordinates=None):
        super(LinearRing, self).__init__(coordinates)
        if self._coordinates[0] != self._coordinates[-1]:
            self._coordinates.append(self._coordinates[0])


    @property
    def coords(self):
        if self._coordinates[0] == self._coordinates[-1]:
            return tuple(self._coordinates)
        else:
            raise ValueError

    @coords.setter
    def coords(self, coordinates):
        LineString.coords.fset(self, coordinates)
        if self._coordinates[0] != self._coordinates[-1]:
            self._coordinates.append(self._coordinates[0])




class Polygon(_Feature):
    """
    A two-dimensional figure bounded by a linear ring

    A polygon has a non-zero area. It may have one or more negative-space
    "holes" which are also bounded by linear rings. If any rings cross each
    other, the feature is invalid and operations on it may fail.

    Attributes
    ----------
    exterior : LinearRing
        The ring which bounds the positive space of the polygon.
    interiors : sequence
        A sequence of rings which bound all existing holes.
    """
    _type = 'Polygon'
    _exterior = None
    _interiors = None

    @property
    def __geo_interface__(self):
        if self._interiors:
            coords = [self.exterior.coords]
            for hole in self.interiors:
                coords.append(hole.coords)
            return {
                'type': self._type,
                'coordinates': tuple(coords)
                }
        elif self._exterior:
            return {
                'type': self._type,
                'coordinates': (self._exterior.coords,)

                }



    def __init__(self, shell, holes=None):
        """
        Parameters
        ----------
        shell : sequence
            A sequence of (x, y [,z]) numeric coordinate pairs or triples
            or a LinearRing.
            If a Polygon is passed as shell the holes parameter will be
            ignored
        holes : sequence
            A sequence of objects which satisfy the same requirements as the
            shell parameters above

        Example
        -------
        Create a square polygon with no holes

          >>> coords = ((0., 0.), (0., 1.), (1., 1.), (1., 0.), (0., 0.))
          >>> polygon = Polygon(coords)
          >>> polygon.area
          1.0
        """
        if holes:
            self._interiors = []
            for hole in holes:
                if hasattr(hole, '__geo_interface__'):
                    gi = hole.__geo_interface__
                    if gi['type'] == 'LinearRing':
                        self._interiors.append(LinearRing(hole))
                    else:
                        raise NotImplementedError
                elif isinstance(hole, (list, tuple)):
                    self._interiors.append(LinearRing(hole))
        else:
            self._interiors = []
        if hasattr(shell, '__geo_interface__'):
            gi = shell.__geo_interface__
            if gi['type'] == 'LinearRing':
                self._exterior = LinearRing(shell)
            elif gi['type'] == 'Polygon':
                self._exterior = LinearRing(gi['coordinates'][0])
                if len(gi['coordinates']) > 1:
                    #XXX should the holes passed if any be ignored
                    # or added to the polygon?
                    self._interiors = []
                    for hole in gi['coordinates'][1:]:
                        self._interiors.append(LinearRing(hole))
            else:
                raise NotImplementedError
        elif isinstance(shell, (list, tuple)):
            assert isinstance(shell[0], (list, tuple))
            if isinstance(shell[0][0], (list, tuple)):
                # we passed shell and holes in the first parameter
                self._exterior = LinearRing(shell[0])
                for hole in shell[1]:
                    self._interiors.append(LinearRing(hole))
            else:
                self._exterior = LinearRing(shell)
        else:
            raise ValueError


    @property
    def exterior(self):
        if self._exterior is not None:
            return self._exterior

    @property
    def interiors(self):
        if self._exterior is not None:
            if self._interiors:
                for interior in self._interiors:
                    yield interior
        else:
            yield None

    def to_wkt(self):
        raise NotImplementedError

class MultiPoint(_Feature):
    """A collection of one or more points

    Attributes
    ----------
    geoms : sequence
        A sequence of Points
    """

    _geoms = None
    _type = 'MultiPoint'

    @property
    def __geo_interface__(self):
        return {
            'type': self._type,
            'coordinates': tuple([g.coords[0] for g in self._geoms])
            }


    def __init__(self, points):
        """
        Parameters
        ----------
        points : sequence
            A sequence of (x, y [,z]) numeric coordinate pairs or triples or a
            sequence of objects that implement the __geo_interface__,
            including instaces of Point.

        Example
        -------
        Construct a 2 point collection

          >>> ob = MultiPoint([[0.0, 0.0], [1.0, 2.0]])
          >>> len(ob.geoms)
          2
          >>> type(ob.geoms[0]) == Point
          True
        """
        self._geoms = []
        if isinstance(points, (list, tuple)):
            for point in points:
                if hasattr(point, '__geo_interface__'):
                    self._from_geo_interface(point)
                elif isinstance(point, (list, tuple)):
                    p = Point(point)
                    self._geoms.append(p)
                else:
                    raise ValueError
        elif hasattr(points, '__geo_interface__'):
            self._from_geo_interface(points)
        else:
            raise ValueError

    def _from_geo_interface(self, point):
        gi = point.__geo_interface__
        if gi['type'] == 'Point':
            p = Point(point)
            self._geoms.append(p)
        elif gi['type'] == 'LinearRing' or gi['type'] == 'LineString':
            l = LineString(point)
            for coord in l.coords:
                p = Point(coord)
                self._geoms.append(p)
        elif gi['type'] == 'Polygon':
            p = Polygon(gi['coordinates'])
            for coord in p.exterior.coords:
                p = Point(coord)
                self._geoms.append(p)
            for interior in p.interiors:
                for coord in interior.coords:
                    p = Point(coord)
                    self._geoms.append(p)
        else:
            raise ValueError

    @property
    def geoms(self):
        return self._geoms

    def unique(self):
        """ Make Points unique, delete duplicates """
        coords = []
        for geom in self.geoms:
            coords.append(geom.coords)
        coords = list(set(coords))
        self._geoms = []
        for coord in coords:
            p = Point(coord)
            self._geoms.append(p)

    def to_wkt(self):
        raise NotImplementedError

class MultiLineString(_Feature):
    """
    A collection of one or more line strings

    A MultiLineString has non-zero length and zero area.

    Attributes
    ----------
    geoms : sequence
        A sequence of LineStrings
    """
    _geoms = None
    _type = 'MultiLineString'

    @property
    def __geo_interface__(self):
        return {
            'type': self._type,
            'coordinates': tuple(tuple(c for c in g.coords) for g in self.geoms)
            }



    def __init__(self, lines):
        """
        Parameters
        ----------
        lines : sequence
            A sequence of line-like coordinate sequences or objects that
            provide the __geo_interface__, including instances of
            LineString.

        Example
        -------
        Construct a collection containing one line string.

          >>> lines = MultiLineString( [[[0.0, 0.0], [1.0, 2.0]]] )
        """
        self._geoms = []
        if isinstance(lines, (list, tuple)):
            for line in lines:
                l = LineString(line)
                self._geoms.append(l)
        elif hasattr(lines, '__geo_interface__'):
            gi = lines.__geo_interface__
            if gi['type'] == 'LinearRing' or gi['type'] == 'LineString':
                l = LineString(gi['coordinates'])
                self._geoms.append(l)
            elif gi['type'] == 'MultiLineString':
                for line in  gi['coordinates']:
                    l = LineString(line)
                    self._geoms.append(l)

        else:
            raise ValueError

    @property
    def geoms(self):
        return self._geoms

    def to_wkt(self):
        raise NotImplementedError


class MultiPolygon(_Feature):
    """A collection of one or more polygons

    If component polygons overlap the collection is `invalid` and some
    operations on it may fail.

    Attributes
    ----------
    geoms : sequence
        A sequence of `Polygon` instances
    """
    _geoms = None
    _type = 'MultiPolygon'

    @property
    def __geo_interface__(self):
        allcoords = []
        for geom in self.geoms:
            coords = []
            coords.append(tuple(geom.exterior.coords))
            for hole in geom.interiors:
                coords.append(tuple(hole.coords))
            allcoords.append(coords)
        return {
            'type': self._type,
            'coordinates': allcoords
            }


    def __init__(self, polygons):
        """
        Parameters
        ----------
        polygons : sequence
            A sequence of (shell, holes) tuples where shell is the sequence
            representation of a linear ring (see linearring.py) and holes is
            a sequence of such linear rings

        Example
        -------
        Construct a collection from a sequence of coordinate tuples

          >>> ob = MultiPolygon( [
          ...     (
          ...     ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)),
          ...     [((0.1,0.1), (0.1,0.2), (0.2,0.2), (0.2,0.1))]
          ...     )
          ... ] )
          >>> len(ob.geoms)
          1
          >>> type(ob.geoms[0]) == Polygon
          True
        """
        self._geoms = []
        if isinstance(polygons, (list, tuple)):
            for polygon in polygons:
                if isinstance(polygon, (list, tuple)):
                    p = Polygon(polygon[0], polygon[1])
                    self._geoms.append(p)
                elif hasattr(polygon, '__geo_interface__'):
                    p = Polygon(polygon)
                    self._geoms.append(p)
                else:
                    raise ValueError
        elif hasattr(polygons, '__geo_interface__'):
            gi = polygons.__geo_interface__
            if gi['type'] == 'Polygon':
                p = Polygon(polygons)
                self._geoms.append(p)
            elif gi['type'] == 'MultiPolygon':
                raise NotImplementedError
        else:
            raise ValueError

    @property
    def geoms(self):
        return self._geoms

    def to_wkt(self):
        raise NotImplementedError

class GeometryCollection(_Feature):
    """A heterogenous collection of geometries

    Attributes
    ----------
    geoms : sequence
        A sequence of geometry instances
    """
    def __init__(self):
        raise NotImplementedError

    def to_wkt(self):
        raise NotImplementedError

def as_shape(feature):
    """ creates a pygeoif feature from an object that
    provides the __geo_interface__ """
    if hasattr(feature, '__geo_interface__'):
        gi = feature.__geo_interface__
        coords = gi['coordinates']
        ft = gi['type']
        if ft == 'Point':
            return Point(coords)
        elif ft == 'LineString':
            return LineString(coords)
        elif ft == 'LinearRing':
            return LinearRing(coords)
        elif ft == 'Polygon':
            return Polygon(coords)
        elif ft == 'MultiPoint':
            return MultiPoint(coords)
        elif ft == 'MultiLineString':
            return MultiLineString(coords)
        elif ft == 'MultiPolygon':
            return MultiPolygon(coords)
        else:
            raise NotImplementedError
    else:
        return TypeError('Object does not implement __geo_interface__')


def from_wkt(geo_str):
    wkt = geo_str.strip()
    if wkt.startswith('POINT'):
        coords = wkt[wkt.find('(') + 1 : wkt.find(')')].split()
        return Point(coords)
    elif wkt.startswith('LINESTRING'):
        coords = wkt[wkt.find('(') + 1 : wkt.find(')')].split(',')
        return LineString([c.split() for c in coords])
    elif wkt.startswith('LINEARRING'):
        coords = wkt[wkt.find('(') + 1 : wkt.find(')')].split(',')
        return LinearRing([c.split() for c in coords])
    #elif wkt.startswith('POLYGON'):
    #    pass
    else:
        raise NotImplementedError





