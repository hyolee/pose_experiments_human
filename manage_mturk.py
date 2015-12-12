import boto
import pymongo as pm
import numpy as np
from boto.mturk.connection import MTurkConnection
from mturkutils.base import parse_credentials_file
from mturkutils.base import parse_human_data_from_HITdata
from mturkutils.base import update_mongodb_once

sandbox = False
max_assignments = 10
comment = "Pose judgement in Rosch dataset"
description = 'Make object 3-d pose judgements for up to 50 cent bonus'


# Mturk
access_key_id, secretkey =  parse_credentials_file(section_name='MTurkCredentials')
if not sandbox:
    conn = MTurkConnection(aws_access_key_id=access_key_id,
                           aws_secret_access_key=secretkey)
else:
    conn = MTurkConnection(aws_access_key_id=access_key_id,
                           aws_secret_access_key=secretkey,
                           host='mechanicalturk.sandbox.amazonaws.com')



# --- hits --- retrieve Pose Judgement experiments only
allhits = [hit for hit in conn.get_all_hits()]
hits = []
for hit in allhits:
    if 'Pose' in hit.Title and 'changed' in hit.Title:
        hits.append(hit)
for hit in hits:
    print hit.HITId, ':', hit.Title
    assignments = conn.get_assignments(hit.HITId)
    print len(assignments), ' assignments for this HIT'
    for a in assignments:
        print a.AssignmentId, ':', a.AssignmentStatus

# mongoDB
mongo_conn = pm.Connection(host='localhost', port=22334)
db = mongo_conn['mturk']
coll = db['rosch_pose_exp']

for doc in coll.find():
    print doc['HITid'], ':', doc['Title']
    print "AssignmentID", doc['AssignmentID']
    print "BonusAwarded?", 'BonusAwarded' in doc.keys()

# getHITdata
def getHITdataraw(hitid, retry=5):
    """Get the human data as raw boto objects for the given `hitid`"""
    # NOTE: be extra careful when modify this function.
    # especially download_results() and cli.make_backup()
    # depends on this.  In short: avoid modification of this func
    # as much as possible, especially the returned data.

    try:
        assignments = conn.get_assignments(hit_id=hitid,
                page_size=min(max_assignments, 100))
        HITdata = conn.get_hit(hit_id=hitid)
    except Exception as e:
        if retry == 0:
            raise e
        from time import sleep
        sleep(5)
        assignments, HITdata = getHITdataraw(hitid, retry=retry - 1)

    return assignments, HITdata

def getHITdata(hitid, verbose=True, full=False):
    assignments, HITdata = getHITdataraw(hitid)
    return parse_human_data_from_HITdata(assignments, HITdata,
                comment=comment, description=description,
                full=full, verbose=verbose)

# updateDBwithHITS
def updateDBwithHITs(hitids, **kwargs):
    """See the documentation of updateDBwithHITs() and
    updateDBwithHITslocal()"""
    meta = None

    if coll is None:
        print('**NO DB CONNECTION**')
        return

    if sandbox:
        print('**WORKING IN SANDBOX MODE**')

    all_data = []
    for src in hitids:
        sdata = getHITdata(src, full=False)

        update_mongodb_once(coll, sdata, meta,
                **kwargs)
        all_data.extend(sdata)

    return all_data

# payBonus
def payBonuses(hitids, performance_threshold=0.375, bonus_threshold=None,
        performance_key='Error', performance_error=False,
        auto_approve=True):
    """
    This function approves and grants bonuses on all hits above a certain
    performance, with a bonus (stored in database) under a certain
    threshold (checked for safety).
    """
    if auto_approve:
        for hitid in hitids:
            assignments = conn.get_assignments(hitid)
            for a in assignments:
                try:
                    assignment_id = a.AssignmentId
                    assignment_status = a.AssignmentStatus
                    doc = coll.find_one({ "AssignmentID": a.AssignmentId })
                    if doc == None:
                        continue
                    performance = doc.get(performance_key)
                    if (performance_threshold is not None) and \
                            (performance is not None):
                        if (performance_error and
                                performance < performance_threshold) or \
                                        (performance > performance_threshold):
                            if assignment_status in ['Submitted']:
                                conn.reject_assignment(assignment_id,
                                    feedback='Your performance was '
                                    'significantly lower than other subjects')
                        else:
                            if assignment_status in ['Submitted']:
                                conn.approve_assignment(assignment_id)
                    else:
                        if assignment_status in ['Submitted']:
                            conn.approve_assignment(assignment_id)
                except boto.mturk.connection.MTurkRequestError, e:
                    print('Error for assignment_id %s' % assignment_id, e)
    for hitid in hitids:
        assignments = conn.get_assignments(hitid)
        for a in assignments:
            try:
                assignment_status = a.AssignmentStatus
                doc = coll.find_one({ "AssignmentID": a.AssignmentId })
                if doc == None:
                    continue
                assignment_id = doc['AssignmentID']
                worker_id = doc['WorkerID']
            except boto.mturk.connection.MTurkRequestError, e:
                print('Error for assignment_id %s' % assignment_id, e)
                continue
            bonus = doc.get('Bonus')
            if (bonus is not None) and (assignment_status == 'Approved'):
                if (bonus_threshold is None) or (float(bonus) <
                        float(bonus_threshold)):
                    if not doc.get('BonusAwarded', False):
                        bonus = np.round(float(bonus) * 100) / 100
                        if bonus >= 0.01:
                            p = boto.mturk.price.Price(bonus)
                            print 'award granted'
                            print bonus
                            conn.grant_bonus(worker_id,
                                    assignment_id,
                                    p,
                                    "Performance Bonus")
                            coll.update({'_id': doc['_id']},
                                    {'$set': {'BonusAwarded': True}},
                                    multi=True)

# approve mistakenly rejected HITs
def approveRejectedHITs(hitids):
    for hitid in hitids:
        assignments = conn.get_assignments(hitid)
        for a in assignments:
            params = {'AssignmentId': a.AssignmentId}
            try: 
              conn._process_request('ApproveRejectedAssignment', params)
            except:
              "Couldn't be approved. check if it is already approved"
