import math
import numpy as np
import cPickle
import yamutils.fast as fast

from upload_images import publish_images
#import dldata.stimulus_sets.synthetic.synthetic_datasets as sd
#import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment

othersrc = ['three.min.js', 'posdict.js', 'Detector.js', 'TrackballControls.js', 'jstat.min.js', '../../lib/dltk.js']

NUM_TEST = 100
LEARNING_PERIOD = 5
REPEATS = 5

import sys
cat = sys.argv[1]
print cat

class RoschPoseExperiment(Experiment):

    def createTrials(self):

        dummy_upload = True
        image_bucket_name = 'rosch_pose'
        seed = 0

        meta_pth = '/home/hyo/.skdata/genthor/RoschDataset3_' + cat + '_6eef6648406c333a4035cd5e60d0bf2ecf2606d7/meta.pkl'
        meta = cPickle.load(open(meta_pth))
        perm = np.random.RandomState(0).permutation(len(meta))
        meta_p = meta[perm]
        pinv = fast.perminverse(perm)

        # decide learning_inds
        learning_inds = np.arange(LEARNING_PERIOD)
        # decide query_inds
        objs = list(set(meta['obj']))
        nObj = round(float(NUM_TEST) / len(objs)) + 1
        query_inds = np.array([], dtype=int)
        v = np.arange(len(meta))
        for obj in objs:
            query_inds = np.append(query_inds, perm[meta_p['obj']==obj][-nObj:])
        query_inds = np.sort(query_inds)[:NUM_TEST]
        query_inds = np.append(query_inds, query_inds[inds_repeat])
        query_inds = np.append(learning_inds, query_inds)
        assert len(query_inds) == NUM_TEST+REPEATS+LEARNING_PERIOD
        print query_inds

        # publish images if needed
        urls = publish_images(cat, query_inds, image_bucket_name, dummy_upload=dummy_upload)

        # construct experiment info
        bmeta = meta[query_inds]
        imgs = urls
        imgData = [{df: bm[df] for df in meta.dtype.names} for bm in bmeta]
        self._trials = {'imgFiles': imgs, 'imgData': imgData}

additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                    'new':  str(LEARNING_PERIOD)}]
exp = RoschPoseExperiment(htmlsrc = 'rosch_pose_newtiming.html',
                        htmldst = 'rosch_pose_newtiming_'+cat+'_1000_n%04d.html',
                        othersrc = othersrc,
                        sandbox = False,
                        title = 'Pose Judgement - ' + cat + ', 1s',
                        reward = 0.45,
                        duration = 2700,
                        description = 'Make object 3-d pose judgements for up to 50 cent bonus',
                        comment = "Pose judgement in Rosch dataset",
                        collection_name = 'rosch_pose_exp',
                        max_assignments=10,
                        bucket_name='rosch_pose_exp',
                        trials_per_hit=NUM_TEST+REPEATS+LEARNING_PERIOD,#BSIZE + REPEATS + LEARNING_PERIOD,
                        additionalrules=additionalrules)

if __name__ == '__main__':

    #cat = 'bear'
    #import sys
    #cat = sys.argv[1]
    inds_repeat = [int(i) for i in sys.argv[2:]]
    assert len(inds_repeat) == REPEATS

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    exp.createHIT(secure=True)

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
