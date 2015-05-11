#!/usr/bin/env python
#
# This file is part of g_mmpbsa.
#
# Authors: Rashmi Kumari and Andrew Lynn
# Contribution: Rajendra Kumar
#
# Copyright (C) 2013, 2014, 2015 Rashmi Kumari and Andrew Lynn
#
# g_mmpbsa is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# g_mmpbsa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with g_mmpbsa.  If not, see <http://www.gnu.org/licenses/>.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#
#

import re
import numpy as np
import argparse
import sys
import os
import math

def main():
	args = ParseOptions()
	CheckInput(args)
	MMEnData,resnameA = ReadData(args.molmech)
	polEnData,resnameB = ReadData(args.polar)
	apolEnData,resnameC = ReadData(args.apolar)
	resname = CheckResname(resnameA,resnameB,resnameC)
	print 'Total number of Residue: {0}\n' .format(len(resname)+1)
	Residues = []
	for i in range(len(resname)):
		CheckEnData(MMEnData[i],polEnData[i],apolEnData[i])
		r = Residue()
		r.CalcEnergy(MMEnData[i],polEnData[i],apolEnData[i],args)
		Residues.append(r)
		print(' %8s %8.4f %8.4f' % (resname[i], r.TotalEn[0], r.TotalEn[1]))
	fout = open(args.output,'w')
	fmap = open(args.outmap,'w')
	fout.write('#Residues  MM Energy(+/-)dev/error  Polar Energy(+/-)dev/error APolar Energy(+/-)dev/error Total Energy(+/-)dev/error\n')
	for i in range(len(resname)):
		if (args.cutoff == 999):
			fout.write("%-8s  %4.4f  %4.4f    %4.4f  %4.4f    %4.4f  %4.4f    %4.4f  %4.4f \n" %(resname[i],Residues[i].FinalMM[0],Residues[i].FinalMM[1], 
                                      Residues[i].FinalPol[0], Residues[i].FinalPol[1], Residues[i].FinalAPol[0], Residues[i].FinalAPol[1], Residues[i].TotalEn[0],Residues[i].TotalEn[1] ))
		elif (args.cutoff <= Residues[i].TotalEn[0]) or ( (-1 *args.cutoff) >= Residues[i].TotalEn[0]):
			fout.write("%-8s  %4.4f  %4.4f    %4.4f  %4.4f    %4.4f  %4.4f    %4.4f  %4.4f \n" % (resname[i],Residues[i].FinalMM[0],Residues[i].FinalMM[1], 
                                  Residues[i].FinalPol[0], Residues[i].FinalPol[1], Residues[i].FinalAPol[0], Residues[i].FinalAPol[1], Residues[i].TotalEn[0],Residues[i].TotalEn[1] ))
			
		fmap.write("%-8d     %4.4f \n" %((i+1), Residues[i].TotalEn[0]))


class Residue():
	def __init__(self):
		self.FinalMM, self.FinalPol, self.FinalAPol, self.TotalEn = [], [], [], []
		
	def BootStrap(self,x,step):
		avg =[]
		x = np.array(x)
		n = len(x)
		idx = np.random.randint(0,n,(step,n))
		sample_x = x[idx]
		avg = np.sort(np.mean(sample_x,1))
		return np.mean(avg), np.std(avg)

	def CalcEnergy(self,MM,Pol,APol,args):
		TotalEn = np.sum([MM,Pol,APol],axis=0)
		if(args.bootstrap):
			self.FinalMM = self.BootStrap(MM,args.nbstep)
			self.FinalPol = self.BootStrap(Pol,args.nbstep)
			if (np.mean(APol) == 0):
				self.FinalAPol = [0.0,0.0]
			else:
				self.FinalAPol = self.BootStrap(APol,args.nbstep)
			self.TotalEn = self.BootStrap(TotalEn,args.nbstep)
		else:
			self.FinalMM = [np.mean(MM),np.std(MM)]
			self.FinalPol = [np.mean(Pol),np.std(Pol)]
			if (np.mean(APol) == 0):
				self.FinalAPol = [0.0,0.0]
			else:
				self.FinalAPol = [np.mean(APol),np.std(APol)]
			self.TotalEn = [np.mean(TotalEn),np.std(TotalEn)]
		self.FinalMM = np.round(self.FinalMM,4)
		self.FinalPol = np.round(self.FinalPol,4)
		self.FinalAPol = np.round(self.FinalAPol,4)
		self.TotalEn = np.round(self.TotalEn,4)

def CheckEnData(MM,Pol,APol):
	if(len(Pol) != len(MM)):
		print "Times or Frames Mismatch between files"
		exit(1)
	if(len(APol) != len(Pol)):
		print "Times or Frames Mismatch between files"
		exit(1)
	if(len(APol) != len(MM)):
		print "Times or Frames Mismatch between files"
		exit(1)


def ParseOptions():
        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--molmech", help='Molecular Mechanics energy file',action="store", default='contrib_MM.dat', metavar='contrib_MM.dat')
        parser.add_argument("-p", "--polar", help='Polar solvation energy file',action="store",default='contrib_pol.dat', metavar='contrib_pol.dat')
        parser.add_argument("-a", "--apolar", help='Non-Polar solvation energy file',action="store",default='contrib_apol.dat',metavar='contrib_apol.dat')
        parser.add_argument("-bs", "--bootstrap", help='Switch for Error by Boot Strap analysis',action="store_true")
        parser.add_argument("-nbs", "--nbstep", help='Number of boot strap steps',action="store", type=int,default=500, metavar=500)
	parser.add_argument("-ct", "--cutoff", help='Absolute Cutoff: energy output above and below this value',action="store",type=float,default=999, metavar=999)
        parser.add_argument("-o", "--output", help='Final Decomposed Energy File',action="store",default='final_contrib_energy.dat', metavar='final_contrib_energy.dat')
	parser.add_argument("-om", "--outmap", help='energy2bfac input file: to map energy on structure for visualization',action="store",default='energyMapIn.dat', metavar='energyMapIn.dat')
        
		args = parser.parse_args()

		if not os.path.exists(args.molmech):
			print '\n{0} not found....\n' .format(args.molmech)
			parser.print_help()
			exit(1)
		if not os.path.exists(args.polar):
			print '\n{0} not found....\n' .format(args.polar)
			parser.print_help()
			exit(1)
		if not os.path.exists(args.apolar):
			print '\n{0} not found....\n' .format(args.apolar)
			parser.print_help()
			exit(1)

		return parser.parse_args()

def CheckResname(resA,resB,resC):
	if(len(resA) != len(resB)):
		print "ERROR: Total number of residues mismatch between files"
		exit(1)
	if(len(resB) != len(resC)):
		print "ERROR: Total number of residues mismatch between files"
		exit(1)
	if(len(resC) != len(resA)):
		print "ERROR: Total number of residues mismatch between files"
		exit(1)
	for i in range(len(resA)):
		if (resA[i] != resB[i]):
			print "ERROR: Residue mismatch between files"
			exit(1)
	for i in range(len(resB)):
		if (resB[i] != resC[i]):
			print "ERROR: Residue mismatch between files"
			exit(1)
	for i in range(len(resA)):
		if (resA[i] != resC[i]):
			print "ERROR: Residue mismatch between files"
			exit(1)
	return resA

def CheckInput(args):
	if not os.path.exists(args.molmech):
		print '\n{0} not found....\n' .format(args.molmech)
		exit(1)
	if not os.path.exists(args.polar):
		print '\n{0} not found....\n' .format(args.polar)
		exit(1)
	if not os.path.exists(args.apolar):
		print '\n{0} not found....\n' .format(args.apolar)
		exit(1)


def ReadData(FileName):
        infile = open(FileName,'r')
        x, data,resname = [],[],[]
	for line in infile:
                line = line.rstrip('\n')
                if not line.strip():
                        continue
                if(re.match('#|@',line)==None):
                        temp = line.split()
                        data.append(np.array(temp))
		if(re.match('#',line)):
			resname = line.split()
	n = len(resname[1:])
        for j in range(1,n):
                x_temp =[]
                for i in range(len(data)):
                        x_temp.append(float(data[i][j]))
                x.append(x_temp)
        return x, resname[2:]

if __name__=="__main__":
        main()
