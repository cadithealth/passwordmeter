# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# file: $Id$
# auth: Philip J Grabner <grabner@cadit.com>
# date: 2013/10/29
# copy: (C) Copyright 2013 Cadit Health Inc., All Rights Reserved.
#------------------------------------------------------------------------------

import unittest
import passwordmeter as pwm

class TestFactor(pwm.Factor):
  category = 'test'
  def test(self, value, extra):
    return (0.5, 'test value is: ' + value)

#------------------------------------------------------------------------------
class TestPasswordMeter(unittest.TestCase):

  #----------------------------------------------------------------------------
  def test_default(self):
    res = pwm.test('password')
    self.assertEqual(len(res), 2)
    self.assertIsInstance(res[0], float)
    self.assertIsInstance(res[1], dict)

  #----------------------------------------------------------------------------
  def test_notword(self):
    self.assertEqual(
      pwm.Meter(settings=dict(factors='notword')).test('password')[0], 0)
    self.assertEqual(
      pwm.Meter(settings=dict(factors='notword')).test('not0klsd@#$')[0], 1)

  #----------------------------------------------------------------------------
  def test_factorsAsString(self):
    self.assertEqual(
      pwm.Meter(settings=dict(
        factors='length,passwordmeter.test_passwordmeter.TestFactor')).test('short')[1],
      {'test': 'test value is: short',
       'length': 'Increase the length of the password'})

  #----------------------------------------------------------------------------
  def test_factorsAsList(self):
    self.assertEqual(
      pwm.Meter(settings=dict(
        factors=['length', TestFactor])).test('short')[1],
      {'test': 'test value is: short',
       'length': 'Increase the length of the password'})

  #----------------------------------------------------------------------------
  def test_strength(self):
    meter = pwm.Meter()
    p0 = meter.test('')[0]
    p1 = meter.test('password')[0]
    p2 = meter.test('pssa')[0]
    p3 = meter.test('pssawrd')[0]
    p4 = meter.test('pss4wr')[0]
    p5 = meter.test('pss4wr0d')[0]
    p6 = meter.test('p$$4wr0d!')[0]
    p7 = meter.test('p$$4WR0d!')[0]
    p8 = meter.test('p$4$WR0d!')[0]
    p9 = meter.test('my voice is my p$$4WR0d!')[0]
    pA = meter.test('mY voiCE is my p$$4WR0d!')[0]
    pB = meter.test('mY voiC3 !s m-y p$$4WR0d!')[0]
    self.assertLess(p0, p1)
    self.assertLess(p1, p2)
    self.assertLess(p2, p3)
    self.assertLess(p3, p4)
    self.assertLess(p4, p5)
    self.assertLess(p5, p6)
    self.assertLess(p6, p7)
    self.assertLess(p7, p8)
    self.assertLess(p8, p9)
    self.assertLess(p9, pA)
    self.assertLessEqual(pA, pB)

#------------------------------------------------------------------------------
# end of $Id$
#------------------------------------------------------------------------------
