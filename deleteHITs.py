import cPickle
import sys
import driver_rosch_pose_newtiming as D

hits = cPickle.load(open(sys.argv[2]))
D.exp.disableHIT(hits)

import os
os.remove(sys.argv[2])
