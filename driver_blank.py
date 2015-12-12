import math
import numpy as np
import cPickle
import yamutils.fast as fast

from upload_images import publish_images
#import dldata.stimulus_sets.synthetic.synthetic_datasets as sd
#import dldata.stimulus_sets.hvm as hvm
from mturkutils.base import Experiment
from boto.mturk.qualification import Requirement
from boto.mturk.qualification import Qualifications

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

        # publish images if needed
        urls = publish_images(cat, query_inds, image_bucket_name, dummy_upload=dummy_upload)

        # construct experiment info
        bmeta = meta[query_inds]
        imgs = urls
        imgData = [{df: bm[df] for df in meta.dtype.names} for bm in bmeta]
        self._trials = {'imgFiles': imgs, 'imgData': imgData}

def create_requirement(conn, workers, qualid, performance_thresh):
    """Returns an MTurk Qualification object for a list of workers which 
    can then be passed to a HIT object. 
    """
    # qualification type must already exist, for now.
    # qual_id = '28EKH1Q6SVQD54NMWRXLEOBVCK22L4' 
    for worker in workers:
        try:
            conn.assign_qualification(qualid, worker, value=100, send_notification=False)
        except Exception, e:
            print 'Worker qualification already exists.'


    req = Requirement(qualification_type_id=qualid, comparator='GreaterThan',
            integer_value=performance_thresh)
    qual = Qualifications()
    qual.add(req)
    return qual

from boto.mturk.connection import MTurkConnection
from mturkutils.base import parse_credentials_file
access_key_id, secretkey =  parse_credentials_file(section_name='MTurkCredentials')
conn = MTurkConnection(aws_access_key_id=access_key_id,
                       aws_secret_access_key=secretkey)
workers = ['A3K3IZ0S0YOLO1',
 'A2FV7F41LYJT25',
 'A3AA5G6HENO6VJ',
 'A26T3M57NK46L5',
 'A3ND4KJK19EZ42',
 'A1B9AYZBWJ0Z7Y',
 'A3HIIRTGJUJZ1D',
 'A2X30CJGIOQTJV',
 'A1Y0ABOUJUMCWW',
 'A10ZKWRZ8WL775',
 'A2WTDVHVVORNDU',
 'A3FW9NWR6TJ4M9',
 'A3AA5G6HENO6VJ',
 'A26T3M57NK46L5',
 'A10ZKWRZ8WL775',
 'A7DN8E3C7IWLI',
 'A3HIIRTGJUJZ1D',
 'A24JJH2D9IH2FZ',
 'A2X30CJGIOQTJV',
 'A2MZ883TW4UTAY']
qual = create_requirement(conn, workers, 'A2WTDVHVVORNDU', 99)

additionalrules = [{'old': 'LEARNINGPERIODNUMBER',
                    'new':  str(LEARNING_PERIOD)}]
exp = RoschPoseExperiment(htmlsrc = 'blank.html',
                        htmldst = 'blank_n%04d.html',
                        othersrc = othersrc,
                        sandbox = True,
                        title = 'Compensation for pose exp',
                        reward = 0.95,
                        duration = 100,
                        description = 'This is compensation for all hits that were mistakenly rejected.',
                        comment = "Just Simple Task",
                        collection_name = 'rosch_pose_exp',
                        max_assignments=20,
                        bucket_name='rosch_pose_exp',
                        trials_per_hit=NUM_TEST+REPEATS+LEARNING_PERIOD,#BSIZE + REPEATS + LEARNING_PERIOD,
                        other_quals = qual.requirements,
                        additionalrules=additionalrules)

if __name__ == '__main__':

    #cat = 'bear'
    #import sys
    #cat = sys.argv[1]
    inds_repeat = [int(i) for i in sys.argv[2:]]

    exp.createTrials()
    exp.prepHTMLs()
    exp.testHTMLs()
    exp.uploadHTMLs()
    exp.createHIT(secure=True)

    #hitids = cPickle.load(open('3ARIN4O78FSZNXPJJAE45TI21DLIF1_2014-06-13_16:25:48.143902.pkl'))
    #exp.disableHIT(hitids=hitids)
