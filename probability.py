"""
    probability.py - all probability-related models (particle filter, ...)
"""

import math
import copy
from math import cos, sin, exp, pi, sqrt, radians
import random
import svg
import engine


def Gaussian(mu, sigma, x):
    # calculates the probability of x for 1-dim Gaussian with mean mu and var. sigma
    return exp(- ((mu - x) ** 2) / (sigma ** 2) / 2.0) / sqrt(2.0 * pi * (sigma ** 2 ))


class ParticleFilter(object):
    simple, markov = 0, 1
    DecentRelevance = 0.75

    """A particle filter that calculates localization probability
    based on a series of (noisy) measurements and displacements"""

    def __init__(self, car, map=None, initAngle=0, n=100, mode=simple, randomness=0.0):
        self.car = car
        self.N = n
        self.initAngle = initAngle
        self.particles = list()
        self.mode = mode
        self.randomness = randomness
        self.barycenter = None

        if map is not None:
            self.setMap(map)

    def setMap(self, map):
        """Sets a map for the particle filter (and executes random population)"""

        self.width = map.width
        self.height = map.height
        self.map = map
        self.populate(self.N, self.initAngle, probability=1./self.N)
        self.check_relevance()

    def reset(self):
        del self.particles
        self.relevance = 0
        self.barycenter = None
        self.particles = list()
        self.populate(self.N, self.initAngle, probability=1./self.N)
        self.check_relevance()


    def populate(self, N, objectAngle, probability):
        """Adds N random particles to the particle filter. (Useful at initialization)"""

        for i in xrange(N):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            while self.map.isObstacle(x, y):
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)

            self.particles.append(Particle(x, y, angle=objectAngle, probability=probability, car=self.car))

    def sense(self, measuredDist, angle):
        """Updates the probabilities to match a measurement.
        Uses a Gaussian on the difference between measured and calculated distance
        and takes into account the sensor's noise.
        measuredDist is in mm.
        """

        for particle in self.particles:
            particleDist = self.map.rayDistance(particle.x, particle.y, angle)

            # Those two tests are here just out of caution. distances shouldn't be None
            if particleDist is None:
                particleDist = self.width + self.height
            if measuredDist is None:
                measuredDist = self.width + self.height

            newProba = Gaussian(particleDist, self.car.sensor_noise, measuredDist)

            if self.mode == ParticleFilter.simple:
                particle.p = newProba
            elif self.mode == ParticleFilter.markov:
                particle.p *= newProba

    def setAngle(self, angle):
        """
        Turns all the particles to a particular angle
        """
        for particle in self.particles:
            angularNoise = random.gauss(0.0, math.radians(self.car.rotation_noise))
            particle.angle = angle + angularNoise

    def move(self, distance):
        """Updates the probabilities to match a displacement.
        Updates the particles' coordinates (taking into account 'noise')
        """

        for particle in self.particles:
            # ...  and it's position
            distanceNoise = random.gauss(0.0, (self.car.displacement_noise/100.)*distance)
            deltaDistance = distance + distanceNoise
            particle.move(deltaDistance)

            # If the particle goes out of the universe, we put it on the border
            particle.x = min(max(0, particle.x), self.width - 1)
            particle.y = min(max(0, particle.y), self.height - 1)

    def normalize(self):
        """Normalizes the particles's weights.
        (Makes the sum of all probabilities equal to 1)
        """
        sumProba = 0
        for particle in self.particles:
            sumProba += particle.p

        if sumProba != 0:
            for particle in self.particles:
                particle.p /= sumProba

    def resample(self):
        """Resampling the particles using a 'resampling wheel' algorithm."""

        newParticles = list()
        maxProba = max(particle.p for particle in self.particles)
        meanProba = sum(particle.p for particle in self.particles) / self.N

        index = random.randint(0, len(self.particles) - 1)
        B = 0.0

        n_resampled = int(self.N*(1.0 - self.randomness))
        for i in xrange(n_resampled):
            B += random.random() * 2 * maxProba

            while self.particles[index].p < B:
                B -= self.particles[index].p
                index = (index + 1) % len(self.particles)

            newParticles.append(copy.copy(self.particles[index]))

        self.particles = newParticles

	if len(self.particles) > 0:
            self.check_relevance()

        # Adding some random particles
        n_new_particles = self.N - n_resampled
        self.populate(n_new_particles, self.particles[-1].angle, probability=meanProba)

        self.normalize()

    def check_relevance(self):
        # Barycenter
        bX, bY = 0., 0.
        numParticles = len(self.particles)

        for particle in self.particles:
            bX += particle.x
            bY += particle.y
        bX /= numParticles
        bY /= numParticles

        self.barycenter = Particle(bX, bY)

        bMeanDist = sum(particle.distance(self.barycenter) for particle in self.particles) / len(self.particles)
        bMeanDist /= self.car.map.pixel_per_mm
        self.relevance = min(1., max(0., 1. - bMeanDist / self.car.length))

    def __repr__(self):
        result = ""
        for particle in self.particles:
            result += particle.__repr__() + '\n'
        result.normalize()
        return result


class Particle(object):

    def __init__(self, x, y, angle=0., probability=1., car=None):

        self.x, self.y = x, y
        self.angle = angle
        self.p = probability
        self.car = car

    def turnAngle(self, deltaAngle):

        self.angle = (self.angle + deltaAngle + pi) % (2*pi) - pi

    def move(self, displacement):
        dx = displacement * self.car.map.pixel_per_mm * -sin(self.angle  - radians(self.car.map.north_angle))
        dy = displacement * self.car.map.pixel_per_mm * -cos(self.angle  - radians(self.car.map.north_angle))

        self.x, self.y = int(self.x + dx), int(self.y + dy)

    def distance(self, particle):
        return sqrt( (self.x - particle.x)**2 + (self.y - particle.y)**2 )

    def __repr__(self):
        return '[x = {} y = {} angle = {} degree | proba = {}]'.format(self.x, self.y, int(math.degrees(self.angle)), self.p)


if __name__ == "__main__":

    myMap = svg.SvgTree("maps/mapexamplewithborder.svg")
    myCar = engine.Car(myMap)
    proba = ParticleFilter(map=myMap, car=myCar, n=20)



# x = 147.0  y = 483.0 ; angle = 0 => dist = 204
